"""How much of the true graph survives automatic extraction - the thesis's
extraction-loss measurement. Evaluation only: this is the one place extracted
names are compared with ground truth (decision 2.9)."""
from generation.facts import display_name, normalise_name


def evaluate_extraction(extracted, gt_triples, entities) -> dict:
    names = {n["node_id"]: n["name"] for n in extracted["nodes"]}
    gold = {(normalise_name(display_name(t["subject"], entities)), t["predicate"],
             normalise_name(display_name(t["object"], entities))) for t in gt_triples}
    got = {(normalise_name(names[t["subject"]]), t["predicate"],
            normalise_name(names.get(t["object"], t["object"]))) for t in extracted["triples"]}
    correct = len(gold & got)
    return {"gold_facts": len(gold), "extracted_facts": len(got), "correct": correct,
            "precision": correct / len(got) if got else 0.0,
            "recall": correct / len(gold) if gold else 0.0,
            "missed": [list(x) for x in sorted(gold - got)],
            "spurious": [list(x) for x in sorted(got - gold)]}


if __name__ == "__main__":
    ents = {"P": {"display_name": "Kivo Ranet"}, "T": {"display_name": "Photonic Sensing Group"},
            "X": {"display_name": "Lumen Vault"}}
    gt = [{"subject": "P", "predicate": "member_of", "object": "T"},
          {"subject": "X", "predicate": "status", "object": "active"}]
    ext = {"nodes": [{"node_id": "e0", "name": "Dr. Kivo Ranet"}, {"node_id": "e1", "name": "Photonic Sensing Group"},
                     {"node_id": "e2", "name": "Lumen Vault"}],
           "triples": [{"subject": "e0", "predicate": "member_of", "object": "e1"},
                       {"subject": "e2", "predicate": "status", "object": "on_hold"}]}
    r = evaluate_extraction(ext, gt, ents)
    assert r["correct"] == 1 and r["precision"] == 0.5 and r["recall"] == 0.5
    print("validation/extraction_quality.py: OK")
