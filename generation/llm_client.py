"""The only way this project calls a model (decision 2.16).

Each call is cached on disk, keyed by a hash of everything that shapes the
response plus a sample number, so reruns after a bug fix cost nothing and the
cache is the reproducibility record (Sonnet 5 accepts no temperature, so its
outputs can't be made deterministic). Every uncached call is logged with tokens
and cost, and refused once logged spend reaches the configured cap.

Set MEMARCH_LLM_DIR to redirect cache + log (self-checks use private/llm_selfcheck).
"""
import hashlib
import json
import os
from pathlib import Path

import anthropic
import yaml

from generation.dataset_io import CANARY


def _load_dotenv(path=".env") -> None:
    """Minimal .env reader (KEY=value lines). Real environment variables win."""
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and not key.strip().startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

with open("configs/llm_config.yaml") as f:
    CONFIG = yaml.safe_load(f)

LLM_DIR = Path(os.environ.get("MEMARCH_LLM_DIR", "data"))
CACHE_DIR = LLM_DIR / "llm_cache"
LOG_PATH = LLM_DIR / "llm_calls.jsonl"
PROMPT_DIR = Path("generation/prompts")

_client = None


class BudgetExceeded(RuntimeError):
    pass


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.txt").read_text()


def spent_usd() -> float:
    if not LOG_PATH.exists():
        return 0.0
    return sum(json.loads(line)["cost_usd"] for line in LOG_PATH.read_text().splitlines() if line.strip())


def call_llm(role, step, system, prompt, schema=None, sample=0, max_tokens=None) -> dict:
    global _client
    model = CONFIG["generation_model"] if role == "generation" else CONFIG["backbone_model"]
    params = {
        "model": model,
        "max_tokens": max_tokens or CONFIG["max_tokens"],
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    output_config = {}
    if role == "backbone":  # Haiku 4.5 rejects `effort`
        output_config["effort"] = CONFIG["effort"][step]
    if schema:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    if output_config:
        params["output_config"] = output_config

    key = hashlib.sha256(json.dumps({**params, "sample": sample}, sort_keys=True).encode()).hexdigest()
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return {**json.loads(path.read_text()), "cached": True}

    if spent_usd() >= CONFIG["budget"]["cap_usd"]:
        raise BudgetExceeded(f"logged spend ${spent_usd():.2f} >= cap ${CONFIG['budget']['cap_usd']}")

    _client = _client or anthropic.Anthropic()
    response = _client.messages.create(**params)
    usage = response.usage
    price = CONFIG["prices_usd_per_mtok"][model]
    cost = round((usage.input_tokens * price["input"] + usage.output_tokens * price["output"]) / 1e6, 6)
    # Log every billed call - including failed ones - so the budget cap sees all spend.
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps({"cache_key": key, "step": step, "model": model, "sample": sample,
                            "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
                            "cost_usd": cost, "stop_reason": response.stop_reason}) + "\n")
    if response.stop_reason in ("max_tokens", "refusal"):
        raise RuntimeError(f"{step}: stop_reason={response.stop_reason}, not parsing partial output")

    text = next(b.text for b in response.content if b.type == "text")
    result = {
        "canary": CANARY, "step": step, "model": model, "sample": sample,
        "system": system, "prompt": prompt, "text": text,
        "json": json.loads(text) if schema else None,
        "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
        "cost_usd": cost, "request_id": response._request_id,
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2))
    return {**result, "cached": False}


if __name__ == "__main__":
    assert os.environ.get("MEMARCH_LLM_DIR"), "run self-check with MEMARCH_LLM_DIR=private/llm_selfcheck"
    schema = {"type": "object", "properties": {"reply": {"type": "string"}},
              "required": ["reply"], "additionalProperties": False}

    # Real call on each model with a schema (catches a model rejecting structured output).
    a = call_llm("generation", "selfcheck", "Be brief.", "Reply with the word OK.", schema=schema)
    b = call_llm("backbone", "kg_extraction", "Be brief.", "Reply with the word OK.", schema=schema)
    assert isinstance(a["json"]["reply"], str) and isinstance(b["json"]["reply"], str)

    # Review Focus: an identical call is served from cache with no new log line.
    lines_before = len(LOG_PATH.read_text().splitlines())
    again = call_llm("generation", "selfcheck", "Be brief.", "Reply with the word OK.", schema=schema)
    assert again["cached"] and again["text"] == a["text"]
    assert len(LOG_PATH.read_text().splitlines()) == lines_before

    # Review Focus: truncated output raises instead of being parsed - and its
    # (billed) cost is still logged so the budget cap counts it.
    spend_before = spent_usd()
    try:
        call_llm("generation", "selfcheck", "Be verbose.", "Write 300 words about rivers.", max_tokens=5)
        raise AssertionError("expected RuntimeError on max_tokens stop")
    except RuntimeError as e:
        assert "max_tokens" in str(e)
    assert spent_usd() > spend_before, "a billed failed call must still be logged"

    # Review Focus: at the cap, uncached calls are refused but cached ones still work.
    cap = CONFIG["budget"]["cap_usd"]
    CONFIG["budget"]["cap_usd"] = 0
    try:
        assert call_llm("generation", "selfcheck", "Be brief.", "Reply with the word OK.", schema=schema)["cached"]
        call_llm("generation", "selfcheck", "Be brief.", "Reply with the word NO.", schema=schema)
        raise AssertionError("expected BudgetExceeded")
    except BudgetExceeded:
        pass
    finally:
        CONFIG["budget"]["cap_usd"] = cap

    print(f"generation/llm_client.py: OK (self-check spend so far ${spent_usd():.4f})")
