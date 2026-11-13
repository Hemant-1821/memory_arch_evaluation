"""Human review sheet for the agent's answers (decision 2.14): every run scored wrong plus a
random ~10% of the runs scored right, for checking both real failures and over-strict scoring.
`code_hint` is a code-made first guess at the cause, for the reviewer to confirm or overrule.
Never overwrites an existing sheet - it holds the reviewer's verdicts.

Run: python -m scripts.build_answer_review results/full_sonnet55 data/kg_full
"""
import csv
import json
import random
import sys
from pathlib import Path

from generation.dataset_io import load_json
from generation.facts import display_name

SEED, SHARE = 11, 0.10  # seed 11 as for the scorer spot-check


def older_values(task, triples, entities) -> set:
    """Names that were the answer in an earlier period: the other end of a replaced fact that
    shares subject+relation or relation+object with a fact on the task's reasoning path."""
    path = [t for t in triples if t["fact_id"] in set(task["reasoning_path"])]
    old = set()
    for t in triples:
        if t["superseded_in_episode"] is None:
            continue
        for p in path:
            if t["predicate"] == p["predicate"] and t["subject"] == p["subject"]:
                old.add(display_name(t["object"], entities))
            if t["predicate"] == p["predicate"] and t["object"] == p["object"]:
                old.add(display_name(t["subject"], entities))
    return old - set(task["ground_truth_answer"])


def hint(run, task, triples, entities) -> str:
    if run["correct"]:
        return ""
    if run.get("refused"):
        return "refused"
    if run.get("hit_step_limit"):
        return "ran out of steps"
    if set(run["answer"] or []) & older_values(task, triples, entities):
        return "gave an older value"
    if run.get("recall") == 0:
        return "never retrieved the needed facts"
    return ""


def build(run_dir, dataset_dir) -> Path:
    out = Path(run_dir) / "review" / "agent_answers.csv"
    if out.exists():
        sys.exit(f"{out} exists - it holds the reviewer's verdicts; not overwritten")
    data = Path(dataset_dir)
    entities, triples = load_json(data / "entities.json"), load_json(data / "triples.json")
    tasks = {t["task_id"]: t for t in load_json(data / "tasks.json")}
    runs = [json.loads(line) for line in open(Path(run_dir) / "runs.jsonl")]
    right = [r for r in runs if r["correct"]]
    picked = random.Random(SEED).sample(right, round(SHARE * len(right)))
    rows = [r for r in runs if not r["correct"]] + picked
    rows.sort(key=lambda r: (["low", "medium", "high"].index(r["tier"]), r["task_id"],
                             ["vector", "graph", "hybrid"].index(r["condition"]), r["seed"]))
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "tier", "condition", "seed", "why_in_sheet", "question", "correct_answer",
                    "agent_answer", "agent_explanation", "scored_correct", "steps", "recall", "code_hint",
                    "you_agree", "failure_reason", "note"])
        for r in rows:
            t = tasks[r["task_id"]]
            w.writerow([r["task_id"], r["tier"], r["condition"], r["seed"],
                        "random_correct" if r["correct"] else "scored_wrong", t["question"],
                        "; ".join(t["ground_truth_answer"]), "; ".join(r["answer"] or []), r["explanation"] or "",
                        r["correct"], r["steps"], r["recall"], hint(r, t, triples, entities), "", "", ""])
    print(f"{out}: {len(rows) - len(picked)} scored wrong + {len(picked)} of {len(right)} scored right")
    return out


def demo() -> None:
    entities = {e: {"display_name": n} for e, n in [("P", "Kivo Ranet"), ("A", "Lumen"), ("B", "Vault")]}
    triples = [{"fact_id": "f1", "subject": "P", "predicate": "leads", "object": "A", "superseded_in_episode": 2},
               {"fact_id": "f2", "subject": "P", "predicate": "leads", "object": "B", "superseded_in_episode": None}]
    task = {"reasoning_path": ["f2"], "ground_truth_answer": ["Vault"]}
    run = {"correct": False, "answer": ["Lumen"], "recall": 1.0}
    assert hint(run, task, triples, entities) == "gave an older value"
    assert hint({**run, "answer": ["Vault"], "correct": True}, task, triples, entities) == ""
    assert hint({**run, "answer": None, "hit_step_limit": True}, task, triples, entities) == "ran out of steps"
    print("build_answer_review: OK")


if __name__ == "__main__":
    build(*sys.argv[1:]) if len(sys.argv) > 1 else demo()
