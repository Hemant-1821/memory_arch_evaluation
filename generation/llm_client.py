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
import time
from pathlib import Path

import anthropic
import yaml
from openai import OpenAI

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
_azure = None


class BudgetExceeded(RuntimeError):
    pass


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.txt").read_text()


def spent_usd(models=None) -> float:
    if not LOG_PATH.exists():
        return 0.0
    rows = [json.loads(line) for line in LOG_PATH.read_text().splitlines() if line.strip()]
    return sum(r["cost_usd"] for r in rows if models is None or r["model"] in models)


def _cache_key(params, sample) -> str:
    return hashlib.sha256(json.dumps({**params, "sample": sample}, sort_keys=True).encode()).hexdigest()


def _cached(key):
    path = CACHE_DIR / f"{key}.json"
    return {**json.loads(path.read_text()), "cached": True} if path.exists() else None


def _check_budget() -> None:
    if spent_usd() >= CONFIG["budget"]["cap_usd"]:
        raise BudgetExceeded(f"logged spend ${spent_usd():.2f} >= cap ${CONFIG['budget']['cap_usd']}")


def _log(entry) -> None:
    """Every billed call is logged - including failed ones - so the budget cap sees all spend."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _save(key, result) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{key}.json").write_text(json.dumps(result, indent=2))
    return {**result, "cached": False}


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

    key = _cache_key(params, sample)
    if hit := _cached(key):
        return hit
    _check_budget()

    _client = _client or anthropic.Anthropic()
    response = _client.messages.create(**params)
    usage = response.usage
    price = CONFIG["prices_usd_per_mtok"][model]
    cost = round((usage.input_tokens * price["input"] + usage.output_tokens * price["output"]) / 1e6, 6)
    _log({"cache_key": key, "step": step, "model": model, "sample": sample,
          "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
          "cost_usd": cost, "stop_reason": response.stop_reason})
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
    return _save(key, result)


def call_azure(step, input_items, tools=None, schema=None, sample=0, model=None) -> dict:
    """Backbone calls on Azure (decision 4.1): the Responses API, the only Azure API
    that combines tool calling with reasoning on GPT-6.x. Stateless (store=False) with
    encrypted reasoning passed back, so a conversation replays exactly from the cache.
    Only the new output items are cached; earlier turns live in their own entries."""
    global _azure
    model = model or CONFIG["azure"]["backbone"]
    params = {"provider": "azure", "model": model, "input": input_items, "store": False,
              "include": ["reasoning.encrypted_content"], "reasoning": {"effort": CONFIG["effort"][step]},
              "max_output_tokens": CONFIG["azure"]["max_output_tokens"]}
    if tools:
        params["tools"] = tools
    if schema:
        params["text"] = {"format": {"type": "json_schema", "name": "output", "schema": schema, "strict": True}}
    key = _cache_key(params, sample)
    if hit := _cached(key):
        return hit
    _check_budget()
    azure_spent = spent_usd({CONFIG["azure"]["backbone"], CONFIG["azure"]["dev"]})
    if azure_spent >= CONFIG["budget"]["azure_cap_usd"]:
        raise BudgetExceeded(f"Azure spend ${azure_spent:.3f} >= cap ${CONFIG['budget']['azure_cap_usd']}")

    host = os.environ["AZURE_OPENAI_ENDPOINT"].split("/")[2]
    _azure = _azure or OpenAI(base_url=f"https://{host}/openai/v1/", api_key=os.environ["AZURE_OPENAI_API_KEY"])
    start = time.perf_counter()
    response = _azure.responses.create(**{k: v for k, v in params.items() if k != "provider"})
    latency = round(time.perf_counter() - start, 3)
    usage = response.usage
    cached_in = usage.input_tokens_details.cached_tokens or 0
    price = CONFIG["prices_usd_per_mtok"][model]
    cost = round(((usage.input_tokens - cached_in) * price["input"] + cached_in * price["cached_input"]
                  + usage.output_tokens * price["output"]) / 1e6, 6)
    _log({"cache_key": key, "step": step, "model": model, "sample": sample,
          "input_tokens": usage.input_tokens, "cached_tokens": cached_in, "output_tokens": usage.output_tokens,
          "cost_usd": cost, "latency_s": latency, "stop_reason": response.status})
    if cost > CONFIG["budget"]["max_call_usd"]:
        raise BudgetExceeded(f"{step}: one call cost ${cost} > ${CONFIG['budget']['max_call_usd']} - stopping")
    if response.status != "completed":
        raise RuntimeError(f"{step}: status={response.status} ({response.incomplete_details}), not parsing")

    result = {
        "canary": CANARY, "step": step, "model": model, "sample": sample,
        "output": [item.model_dump(exclude_none=True) for item in response.output],
        "text": response.output_text, "json": json.loads(response.output_text) if schema else None,
        "input_tokens": usage.input_tokens, "cached_tokens": cached_in, "output_tokens": usage.output_tokens,
        "cost_usd": cost, "latency_s": latency, "request_id": response.id,
    }
    return _save(key, result)


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

    # Azure route: replay is free, logs nothing, and keeps the original latency.
    pong = [{"role": "user", "content": "Reply with exactly: pong"}]
    az = call_azure("experiment_agent", pong)
    lines_before = len(LOG_PATH.read_text().splitlines())
    replay = call_azure("experiment_agent", pong)
    assert replay["cached"] and replay["latency_s"] == az["latency_s"] and "pong" in replay["text"].lower()
    assert len(LOG_PATH.read_text().splitlines()) == lines_before

    print(f"generation/llm_client.py: OK (self-check spend so far ${spent_usd():.4f})")
