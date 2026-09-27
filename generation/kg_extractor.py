"""Builds the graph the graph/hybrid conditions will use - extracted by Sonnet
from the documents, given the ontology vocabulary but never the true facts
(decisions 2.7, 2.8). Names are merged after light normalisation only; the
ground-truth entity table is never consulted (decision 2.9)."""
from collections import Counter

from generation.facts import normalise_name, period_label
from generation.llm_client import call_llm, load_prompt

SYSTEM = "You extract knowledge graphs precisely, using only the vocabulary you are given."


def _vocabulary(ontology):
    relations = "\n".join(f"- {r}: {' or '.join(d['source_types'])} -> {d['target_type']}"
                          for r, d in ontology["relation_types"].items())
    attributes = sorted({a for e in ontology["entity_types"].values()
                         for a, d in e["attributes"].items() if d.get("replaceable")})
    return relations, attributes


def _schema(ontology, attributes):
    types = sorted(ontology["entity_types"])
    triple = {"type": "object",
              "properties": {"subject": {"type": "string"},
                             "subject_type": {"type": "string", "enum": types},
                             "predicate": {"type": "string", "enum": sorted(ontology["relation_types"]) + attributes},
                             "object": {"type": "string"},
                             "object_type": {"type": "string", "enum": types + ["Value"]}},
              "required": ["subject", "subject_type", "predicate", "object", "object_type"],
              "additionalProperties": False}
    return {"type": "object", "properties": {"triples": {"type": "array", "items": triple}},
            "required": ["triples"], "additionalProperties": False}


def extract_document(doc, ontology) -> list[dict]:
    relations, attributes = _vocabulary(ontology)
    prompt = load_prompt("kg_extractor").format(
        entity_types=", ".join(sorted(ontology["entity_types"])), relations=relations,
        attributes=", ".join(attributes), period=period_label(doc["episode"]), document=doc["text"])
    raw = call_llm("backbone", "kg_extraction", SYSTEM, prompt, schema=_schema(ontology, attributes))["json"]
    return [dict(t, doc_id=doc["doc_id"], episode=doc["episode"]) for t in raw["triples"]]


def build_graph(raw_triples) -> dict:
    nodes: dict[str, dict] = {}

    def node(name, etype):
        key = normalise_name(name)
        if key not in nodes:
            nodes[key] = {"node_id": f"ext_{len(nodes):04d}", "name": name.strip(), "types": Counter()}
        nodes[key]["types"][etype] += 1
        return nodes[key]["node_id"]

    triples = []
    for t in raw_triples:
        subject = node(t["subject"], t["subject_type"])
        obj = t["object"].strip().lower() if t["object_type"] == "Value" else node(t["object"], t["object_type"])
        triples.append({"subject": subject, "predicate": t["predicate"], "object": obj,
                        "doc_id": t["doc_id"], "episode": t["episode"]})
    return {"nodes": [{"node_id": n["node_id"], "name": n["name"], "entity_type": n["types"].most_common(1)[0][0]}
                      for n in nodes.values()],
            "triples": triples}


def extract_kg(docs, ontology) -> dict:
    return build_graph([t for d in docs for t in extract_document(d, ontology)])


if __name__ == "__main__":
    from schema.validate_ontology import load_ontology
    raw = [{"subject": "Dr. Kivo Ranet", "subject_type": "Person", "predicate": "member_of",
            "object": "Photonic Sensing Group", "object_type": "Team", "doc_id": "d1", "episode": 0},
           {"subject": "kivo ranet", "subject_type": "Person", "predicate": "works_at",
            "object": "Lumen Vault", "object_type": "Project", "doc_id": "d2", "episode": 1},
           {"subject": "Lumen Vault", "subject_type": "Project", "predicate": "status",
            "object": "Active", "object_type": "Value", "doc_id": "d2", "episode": 1}]
    g = build_graph(raw)
    assert len(g["nodes"]) == 3, "'Dr. Kivo Ranet' and 'kivo ranet' must merge"
    assert g["triples"][2]["object"] == "active"

    doc = {"doc_id": "d_test", "episode": 1,
           "text": "Project Lumen Vault update: Kivo Ranet now works on project Lumen Vault. Status: active."}
    got = extract_document(doc, load_ontology())
    assert got and all(t["doc_id"] == "d_test" for t in got)
    print(f"generation/kg_extractor.py: OK ({len(got)} triples from the test document)")
