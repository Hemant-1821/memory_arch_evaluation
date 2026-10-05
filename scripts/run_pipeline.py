"""Dataset pipeline, end to end (decision 2.21 scope): graph -> episodes -> documents
-> fidelity -> KG extraction -> tasks -> phrasing/ambiguity -> closed-book /
gold-context -> human review sheets. Rerunning is free for anything cached.

Run: python -m scripts.run_pipeline [--full]   (needs ANTHROPIC_API_KEY in .env)
Pilot (~34 entities) writes data/kg_pilot; --full (~550 entities, 6 episodes,
30 tasks per level) writes data/kg_full - raise budget.cap_usd first.
"""
import csv
import sys
from pathlib import Path

import yaml

from generation.dataset_io import save_json
from generation.document_generator import build_fact_doc_map, write_documents
from generation.document_planner import plan_documents
from generation.episode_splitter import split_into_episodes
from generation.facts import fact_to_statement, period_label
from generation.graph_generator import generate_graph, save_graph
from generation.kg_extractor import extract_kg
from generation.llm_client import spent_usd
from generation.task_generator import generate_tasks, phrase_task_as_question
from schema.validate_ontology import load_ontology
from validation.ambiguity_check import ambiguity_check
from validation.closed_book_check import closed_book_check
from validation.document_accuracy_check import document_accuracy_check
from validation.extraction_quality import evaluate_extraction
from validation.gold_context_check import gold_context_check
from validation.level_accuracy_check import level_accuracy_check

PILOT = "--full" not in sys.argv
OUT = Path("data/kg_pilot" if PILOT else "data/kg_full")
SEED = 7


def run_task_checks(task, entities, triples) -> None:
    checks = task["checks"]
    checks["level_accuracy"] = level_accuracy_check(task, triples)
    for attempt in range(2):  # one rephrase if the ambiguity check objects
        question = phrase_task_as_question(task, attempt)
        checks["ambiguity"] = ambiguity_check(task, question, attempt)
        if checks["ambiguity"]["passed"]:
            break
    task["question"] = question
    for name, passed in (("level_accuracy", checks["level_accuracy"]),
                         ("ambiguity", checks["ambiguity"]["passed"])):
        if not passed:
            task["status"], task["drop_reason"] = "dropped", name
            return
    checks["closed_book"] = closed_book_check(task, entities, triples)
    if not checks["closed_book"]["passed"]:
        task["status"], task["drop_reason"] = "dropped", "closed_book"
        return
    checks["gold_context"] = gold_context_check(task, entities, triples)
    task["status"] = "kept" if checks["gold_context"]["passed"] else "dropped"
    task["drop_reason"] = None if checks["gold_context"]["passed"] else "gold_context"
    checks["human_review"] = None  # filled in from review/questions.csv


def write_review_sheets(docs, fidelity, tasks, triples, entities) -> None:
    if (OUT / "review").exists():  # never overwrite human review work
        print(f"{OUT}/review exists - left untouched (delete it to regenerate the sheets)")
        return
    by_id = {t["fact_id"]: t for t in triples}
    checks = {r["doc_id"]: r for r in fidelity}
    (OUT / "review").mkdir(parents=True)
    with open(OUT / "review/questions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "tier", "status", "question", "really_asking", "correct_answer",
                    "ambiguity_issue", "approve_reject_rewrite", "note"])
        for t in tasks:
            w.writerow([t["task_id"], t["tier"], t["status"], t["question"], t["meaning"],
                        "; ".join(t["ground_truth_answer"]), t["checks"]["ambiguity"]["issue"], "", ""])
    with open(OUT / "review/documents.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["doc_id", "kind", "period", "doc_type", "status", "facts_it_must_contain",
                    "auto_verdicts", "invented_claims", "text", "your_verdict", "note"])
        for d in docs:
            r = checks[d["doc_id"]]
            facts = " | ".join(f"{f}: {fact_to_statement(by_id[f], entities)}"
                               for f in d["home_fact_ids"] + d["mention_fact_ids"])
            w.writerow([d["doc_id"], d["kind"], period_label(d["episode"]), d["doc_type"], d["status"], facts,
                        r.get("verdicts"), "; ".join(r.get("invented_claims", [])), d["text"], "", ""])
    with open(OUT / "review/answers.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "check", "sample", "answer", "scored_correct", "explanation", "you_agree", "note"])
        for t in tasks:
            for check in ("closed_book", "gold_context"):
                result = t["checks"].get(check)
                for i, (a, ok) in enumerate(zip(result["answers"], result["correct"]) if result else []):
                    w.writerow([t["task_id"], check, i, "; ".join(a["answer"]), ok, a["explanation"], "", ""])


def main() -> None:
    ontology = load_ontology()
    triples, entities = generate_graph(SEED, pilot=PILOT)
    episoded = split_into_episodes(triples, SEED, pilot=PILOT)
    save_graph(episoded, entities, out_dir=str(OUT))

    docs, fidelity = write_documents(plan_documents(episoded, entities, SEED), episoded, entities)
    save_json(OUT / "documents.json", docs)
    save_json(OUT / "fact_doc_map.json", build_fact_doc_map(docs))
    save_json(OUT / "fidelity_results.json", fidelity)

    extracted = extract_kg(docs, ontology)
    quality = evaluate_extraction(extracted, episoded, entities)
    save_json(OUT / "extracted_kg.json", extracted)
    save_json(OUT / "extraction_quality.json", quality)

    with open("configs/sizing.yaml") as f:
        per_level = yaml.safe_load(f)["tasks"]["per_level_pilot" if PILOT else "per_level_full"]
    tasks = generate_tasks(episoded, entities, SEED, per_level)
    for task in tasks:
        run_task_checks(task, entities, episoded)
    save_json(OUT / "tasks.json", tasks)
    write_review_sheets(docs, fidelity, tasks, episoded, entities)

    summary = {
        "documents": len(docs), "distractors": sum(d["kind"] != "fact" for d in docs),
        "documents_flagged": sum(d["status"] == "flagged" for d in docs),
        "document_accuracy": document_accuracy_check(fidelity),
        "extraction_precision": quality["precision"], "extraction_recall": quality["recall"],
        "tasks_by_tier": {tier: {"generated": sum(t["tier"] == tier for t in tasks),
                                 "kept": sum(t["tier"] == tier and t["status"] == "kept" for t in tasks)}
                          for tier in ("low", "medium", "high")},
        "drop_reasons": {t["task_id"]: t["drop_reason"] for t in tasks if t["status"] == "dropped"},
        "total_spend_usd": round(spent_usd(), 4),
    }
    save_json(OUT / "summary.json", summary)
    print(yaml.safe_dump(summary, sort_keys=False))


if __name__ == "__main__":
    main()
