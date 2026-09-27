"""Verbalisation coverage + invented-claim check (decision 2.20).

Cheap code check first: every entity named in a fact must appear in the text.
Only then does Sonnet check meaning (stated / missing / contradicted) and list
claims the document invents. Threshold: 100% of assigned facts stated, nothing
contradicted, nothing invented.
"""
from generation.facts import contains_name, fact_to_statement
from generation.llm_client import call_llm, load_prompt

SYSTEM = "You check documents against fact lists precisely and literally."
SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {"type": "array", "items": {
            "type": "object",
            "properties": {"fact_id": {"type": "string"},
                           "verdict": {"type": "string", "enum": ["stated", "missing", "contradicted"]}},
            "required": ["fact_id", "verdict"], "additionalProperties": False}},
        "invented_claims": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["facts", "invented_claims"], "additionalProperties": False,
}


def name_check(doc_text, facts, entities) -> list[str]:
    return [t["fact_id"] for t in facts
            if any(x in entities and not contains_name(doc_text, entities[x]["display_name"])
                   for x in (t["subject"], t["object"]))]


def fidelity_check(doc_text, facts, entities, attempt=0) -> dict:
    missing_names = name_check(doc_text, facts, entities)
    if missing_names:
        return {"passed": False, "coverage": 1 - len(missing_names) / len(facts),
                "missing_names": missing_names, "verdicts": {}, "invented_claims": []}
    listing = "\n".join(f"{t['fact_id']}: {fact_to_statement(t, entities)}" for t in facts) or "(none)"
    result = call_llm("backbone", "fidelity_check", SYSTEM,
                      load_prompt("fidelity_checker").format(facts=listing, document=doc_text),
                      schema=SCHEMA, sample=attempt)["json"]
    verdicts = {v["fact_id"]: v["verdict"] for v in result["facts"]}
    stated = [t for t in facts if verdicts.get(t["fact_id"]) == "stated"]
    return {"passed": len(stated) == len(facts) and not result["invented_claims"],
            "coverage": len(stated) / len(facts) if facts else 1.0,
            "missing_names": [], "verdicts": verdicts, "invented_claims": result["invented_claims"]}


if __name__ == "__main__":
    ents = {"Person_0000": {"display_name": "Kivo Ranet"}, "Team_0000": {"display_name": "Photonic Sensing Group"},
            "Project_0000": {"display_name": "Lumen Vault"}}
    facts = [{"fact_id": "fact_a", "subject": "Person_0000", "predicate": "member_of", "object": "Team_0000"}]

    good = "Org update: Kivo Ranet has joined the Photonic Sensing Group team this period."
    assert fidelity_check(good, facts, ents)["passed"]

    no_name = "Org update: a new colleague has joined the Photonic Sensing Group."
    r = fidelity_check(no_name, facts, ents)
    assert not r["passed"] and r["missing_names"] == ["fact_a"], "code check must catch a missing name"

    garbled = "Kivo Ranet met the Photonic Sensing Group team, and Kivo Ranet now leads project Lumen Vault."
    r = fidelity_check(garbled, facts, ents)
    assert not r["passed"], "met-with is not member-of, and the leadership claim is invented"
    assert r["verdicts"].get("fact_a") != "stated" or r["invented_claims"]
    print("validation/fidelity_check.py: OK")
