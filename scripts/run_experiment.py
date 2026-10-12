"""Runs the experiment: kept tasks x memory conditions x seeds, seed-major (all of
seed 1, then seed 2, then seed 3 - decision 2026-10-12), one JSON line per run in
results/<name>/runs.jsonl. Reruns replay from the LLM cache for free. Stops early
if the projected cost of the whole run passes --max-usd (checked from run 3 on).
Needs `docker compose up -d`; loads the dataset into both stores first.

Run: python -m scripts.run_experiment --name e2e --per-tier 1 --seeds 1 --max-usd 0.5
"""
import argparse
import json
from pathlib import Path

from agent.react import run_task
from generation.dataset_io import load_json
from generation.llm_client import CONFIG
from memory.graph_store import GraphMemory
from memory.vector_store import VectorMemory


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/kg_pilot")
    ap.add_argument("--name", required=True)
    ap.add_argument("--conditions", nargs="+", default=["vector", "graph", "hybrid"])
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--per-tier", type=int, default=30)
    ap.add_argument("--model", choices=["backbone", "dev"], default="backbone")
    ap.add_argument("--max-usd", type=float, required=True)
    args = ap.parse_args()

    data, name = Path(args.dataset), Path(args.dataset).name
    entities, triples = load_json(data / "entities.json"), load_json(data / "triples.json")
    kept = [t for t in load_json(data / "tasks.json") if t["status"] == "kept"]
    tasks = [t for tier in ("low", "medium", "high") for t in [t for t in kept if t["tier"] == tier][:args.per_tier]]
    vector, graph = VectorMemory(name), GraphMemory(name)
    vector.load(load_json(data / "documents.json"))  # ponytail: reload every run; skip when full-size loads get slow
    graph.load(load_json(data / "extracted_kg.json"))

    out = Path("results") / args.name
    out.mkdir(parents=True, exist_ok=True)
    plan = [(seed, t, c) for seed in range(args.seeds) for t in tasks for c in args.conditions]
    runs = []
    with open(out / "runs.jsonl", "w") as f:
        for seed, task, condition in plan:
            try:
                run = run_task(task, condition, vector, graph, entities, triples, seed, CONFIG["azure"][args.model])
            except RuntimeError as e:  # an incomplete model response is a failed run, not a crash
                run = {"task_id": task["task_id"], "tier": task["tier"], "condition": condition, "seed": seed,
                       "correct": False, "error": str(e)}
            runs.append(run)
            f.write(json.dumps(run) + "\n")
            spent = sum(r.get("cost_usd", 0) for r in runs)
            print(f"{task['task_id']:10} {condition:7} seed {seed}  correct={run['correct']!s:5} "
                  f"steps={run.get('steps')} recall={run.get('recall')} ${run.get('cost_usd', 0):.4f}")
            if len(runs) >= 3 and spent / len(runs) * len(plan) > args.max_usd:
                print(f"STOP: projected ${spent / len(runs) * len(plan):.3f} > --max-usd {args.max_usd}")
                break
    graph.driver.close()

    summary = {"runs": len(runs), "planned": len(plan), "model": CONFIG["azure"][args.model],
               "cost_usd": round(sum(r.get("cost_usd", 0) for r in runs), 6),
               "accuracy_by_condition": {c: round(sum(r["correct"] for r in runs if r["condition"] == c) /
                                                  max(1, sum(r["condition"] == c for r in runs)), 3)
                                         for c in args.conditions}}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
