"""Writes the corpus with Haiku from the planner's specs, checks each document,
and rewrites failures up to max_retries times before flagging it for human
review (decisions 2.4-2.6, 2.20). Retry attempts are separate cache entries. A refusal
counts as a failed attempt; a document refused on every attempt stops the run (decision 6.7)."""
from generation.facts import contains_name, fact_to_statement, period_label
from generation.llm_client import Refusal, call_llm, load_prompt
from validation.fidelity_check import fidelity_check

SYSTEM = "You write realistic internal documents for a fictional organisation."
SCHEMA = {"type": "object",
          "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
          "required": ["title", "body"], "additionalProperties": False}

NO_CLAIMS = ("Do not state any relationship, role, leadership, membership, location, skill, status, "
             "availability or date for any named person, team, project, organisation, publication, "
             "equipment or place.")


def _distractor_instruction(spec) -> str:
    names = " and ".join(spec["entity_names"])
    if spec["kind"] == "same_entity_no_facts":
        return (f"Mention {names} by name, but record no decisions or facts about them - for example an "
                f"agenda, a thank-you note or a scheduling notice. {NO_CLAIMS}")
    if spec["kind"] == "lookalike":
        return (f"The document is about {names}. You may describe its work, role or plans, but do not "
                f"mention any other named person, team, project, organisation, publication, equipment or place.")
    return ("Write a general notice unrelated to research work, such as facilities, canteen, IT maintenance "
            f"or a social event. Do not mention any person, team, project or organisation by name. {NO_CLAIMS}")


def _write(spec, by_id, entities, attempt) -> str:
    period, doc_type = period_label(spec["episode"]), spec["doc_type"].replace("_", " ")
    if spec["kind"] == "fact":
        listed = lambda ids: "\n".join(f"- {fact_to_statement(by_id[f], entities)}" for f in ids) or "- (none)"
        prompt = load_prompt("document_writer").format(
            period=period, doc_type=doc_type,
            home_facts=listed(spec["home_fact_ids"]), mention_facts=listed(spec["mention_fact_ids"]))
    else:
        prompt = load_prompt("distractor_writer").format(
            period=period, doc_type=doc_type, instruction=_distractor_instruction(spec))
    doc = call_llm("generation", "document_writing", SYSTEM, prompt, schema=SCHEMA, sample=attempt)["json"]
    return f"{doc['title']}\n\n{doc['body']}"


def _check(spec, text, by_id, entities, attempt) -> dict:
    if spec["kind"] == "lookalike":  # may state facts about the fake entity; must not name real ones
        leaked = sorted(e["display_name"] for e in entities.values() if contains_name(text, e["display_name"]))
        return {"passed": not leaked, "coverage": 1.0, "missing_names": [], "verdicts": None,
                "invented_claims": [], "leaked_real_names": leaked}
    facts = [by_id[f] for f in spec["home_fact_ids"] + spec["mention_fact_ids"]]
    return fidelity_check(text, facts, entities, attempt)


def write_documents(specs, triples, entities, max_retries=2):
    by_id = {t["fact_id"]: t for t in triples}
    docs, results = [], []
    for spec in specs:
        written = None
        for attempt in range(max_retries + 1):
            try:
                text = _write(spec, by_id, entities, attempt)
                written = text, _check(spec, text, by_id, entities, attempt)
            except Refusal:  # billed and logged by llm_client; try again
                continue
            if written[1]["passed"]:
                break
        if written is None:
            raise RuntimeError(f"{spec['doc_id']}: refused on all {max_retries + 1} attempts - stopping (decision 6.7)")
        text, check = written
        docs.append({**spec, "text": text, "attempts": attempt + 1, "status": "ok" if check["passed"] else "flagged"})
        results.append({"doc_id": spec["doc_id"], **check})
    return docs, results


def build_fact_doc_map(docs) -> dict:
    mapping = {}
    for d in docs:
        for f in d["home_fact_ids"]:
            mapping.setdefault(f, {"home": None, "mentions": []})["home"] = d["doc_id"]
        for f in d["mention_fact_ids"]:
            mapping.setdefault(f, {"home": None, "mentions": []})["mentions"].append(d["doc_id"])
    return mapping


if __name__ == "__main__":
    # Refusal handling, no API calls: a lookalike is checked by code only.
    spec = {"doc_id": "doc_x", "kind": "lookalike", "home_fact_ids": [], "mention_fact_ids": []}
    real_write, tries = _write, []

    def flaky(spec, by_id, entities, attempt):
        tries.append(attempt)
        if attempt == 0 or spec["doc_id"] == "doc_never":
            raise Refusal({"step": "document_writing", "refusal_category": "bio"})
        return "Facilities notice: the east entrance closes early on Friday."
    _write = flaky
    docs, _ = write_documents([spec], [], {})
    assert docs[0]["status"] == "ok" and docs[0]["attempts"] == 2 and tries == [0, 1], "refusal = failed attempt"
    try:
        write_documents([dict(spec, doc_id="doc_never")], [], {})
        raise AssertionError("expected a stop")
    except RuntimeError as e:
        assert "doc_never" in str(e) and not isinstance(e, Refusal)
    _write = real_write

    from generation.document_planner import plan_documents
    from generation.episode_splitter import split_into_episodes
    from generation.graph_generator import generate_graph

    triples, entities = generate_graph(seed=7, pilot=True)
    episoded = split_into_episodes(triples, seed=7, pilot=True)
    specs = plan_documents(episoded, entities, seed=7)
    sample = [next(s for s in specs if s["kind"] == "fact" and s["mention_fact_ids"]),
              next(s for s in specs if s["kind"] == "lookalike")]

    docs, results = write_documents(sample, episoded, entities)
    for d, r in zip(docs, results):
        assert d["text"].strip() and d["doc_id"] == r["doc_id"]
        print(f"  {d['doc_id']} ({d['kind']}): {d['status']} after {d['attempts']} attempt(s)")
    m = build_fact_doc_map(docs)
    assert all(m[f]["home"] == docs[0]["doc_id"] for f in docs[0]["home_fact_ids"])
    print("generation/document_generator.py: OK")
