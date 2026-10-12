"""Groups the episoded ground-truth facts into document specs - no LLM.

Decision 2.4: mixed document types, each belonging to exactly one episode, so a
changed fact shows up in a later document while the old one stays in the corpus.
Decision 2.6: each fact has one home document plus up to N passing mentions in
other documents where it is still true. Decision 2.5: ~22% distractors - mostly
same-entities-no-new-facts and look-alike names, a little off-topic noise.
"""
import random

import yaml

from generation.facts import normalise_name
from generation.seeding import derive_seed

DOC_TYPES = ["facilities_notice", "meeting_minutes", "partnership_announcement",
             "project_report", "publication_abstract", "team_memo"]


def _doc_config() -> dict:
    with open("configs/sizing.yaml") as f:
        return yaml.safe_load(f)["documents"]


def classify_fact(t, entities) -> tuple[str, str | None]:
    """Which kind of document naturally states this fact, and what it is about."""
    p, s, o = t["predicate"], t["subject"], t["object"]
    s_type = entities[s]["entity_type"]
    if p == "attends" or s_type == "Meeting":
        return "meeting_minutes", (o if p == "attends" else s)
    if p == "authored" or s_type == "Publication":
        return "publication_abstract", (o if p == "authored" else s)
    if p == "partners_with" or s_type == "PartnerOrganization":
        return "partnership_announcement", (o if p == "partners_with" else s)
    if s_type == "Equipment":
        return "facilities_notice", s
    if s_type == "Project":
        return "project_report", s
    if p in ("works_at", "leads"):
        return "project_report", o
    # member_of, reports_to, based_in, has_skill: one org-update memo per episode,
    # chunked, covering several people - like a real HR/org update.
    return "team_memo", None


def _lookalike(name: str, rng: random.Random, taken: set[str]) -> str:
    """Double one letter ('Kivo Ranet' -> 'Kivvo Ranet'); never a real name."""
    while True:
        i = rng.randrange(len(name))
        if name[i].isalpha():
            candidate = name[:i + 1] + name[i] + name[i + 1:]
            if normalise_name(candidate) not in taken:
                return candidate


def plan_documents(triples, entities, seed) -> list[dict]:
    cfg = _doc_config()
    rng = random.Random(derive_seed(seed, "documents"))
    by_id = {t["fact_id"]: t for t in triples}

    groups: dict[tuple, list] = {}
    for t in sorted(triples, key=lambda t: (t["episode_id"], t["subject"], t["fact_id"])):
        doc_type, anchor = classify_fact(t, entities)
        groups.setdefault((t["episode_id"], doc_type, anchor or ""), []).append(t["fact_id"])

    # Pack anchor groups of the same episode + type into documents of min..max
    # facts (e.g. one portfolio update covering two small projects). Single-fact
    # documents would make retrieval artificially easy for vector search.
    size, minimum = cfg["max_facts_per_doc"], cfg["min_facts_per_doc"]
    packed: dict[tuple, list[list]] = {}
    for (episode, doc_type, _anchor), fact_ids in sorted(groups.items()):
        docs = packed.setdefault((episode, doc_type), [])
        for i in range(0, len(fact_ids), size):
            chunk = fact_ids[i:i + size]
            if docs and len(docs[-1]) < minimum and len(docs[-1]) + len(chunk) <= size:
                docs[-1].extend(chunk)
            else:
                docs.append(chunk)
    specs = []
    for (episode, doc_type), docs in sorted(packed.items()):
        for fact_ids in docs:
            specs.append({"doc_id": f"doc_{len(specs):03d}", "episode": episode, "doc_type": doc_type,
                          "kind": "fact", "home_fact_ids": fact_ids,
                          "mention_fact_ids": [], "entity_names": []})

    home_of = {f: s["doc_id"] for s in specs for f in s["home_fact_ids"]}
    touches = {s["doc_id"]: {x for f in s["home_fact_ids"] for x in (by_id[f]["subject"], by_id[f]["object"])}
               for s in specs}
    for fact_id in sorted(by_id):
        fact = by_id[fact_id]
        until = fact["superseded_in_episode"]
        candidates = [s for s in specs
                      if s["doc_id"] != home_of[fact_id]
                      and fact["episode_id"] <= s["episode"]
                      and (until is None or s["episode"] < until)
                      and touches[s["doc_id"]] & {fact["subject"], fact["object"]}]
        k = min(len(candidates), rng.randint(0, cfg["max_extra_mentions"]))
        for s in rng.sample(candidates, k):
            s["mention_fact_ids"].append(fact_id)

    frac = cfg["distractor_fraction"]
    n_distractors = round(len(specs) * frac / (1 - frac))
    real_names = {normalise_name(e["display_name"]) for e in entities.values()}
    named = sorted(eid for eid, e in entities.items() if e["entity_type"] in ("Person", "Project", "Team"))
    episodes = sorted({t["episode_id"] for t in triples})
    n_each = int(n_distractors * 0.45)  # proportional, not random draws: a small pilot skews badly
    kinds = ["same_entity_no_facts"] * n_each + ["lookalike"] * n_each
    kinds += ["noise"] * (n_distractors - len(kinds))
    rng.shuffle(kinds)
    for kind in kinds:
        spec = {"doc_id": f"doc_{len(specs):03d}", "episode": rng.choice(episodes),
                "doc_type": rng.choice(DOC_TYPES), "kind": kind,
                "home_fact_ids": [], "mention_fact_ids": [], "entity_names": []}
        if kind == "same_entity_no_facts":
            spec["entity_names"] = [entities[e]["display_name"] for e in rng.sample(named, 2)]
        elif kind == "lookalike":
            spec["entity_names"] = [_lookalike(entities[rng.choice(named)]["display_name"], rng, real_names)]
        specs.append(spec)
    return specs


if __name__ == "__main__":
    from collections import Counter
    from generation.graph_generator import generate_graph
    from generation.episode_splitter import split_into_episodes

    triples, entities = generate_graph(seed=7, pilot=True)
    episoded = split_into_episodes(triples, seed=7, pilot=True)
    by_id = {t["fact_id"]: t for t in episoded}
    cfg = _doc_config()

    specs = plan_documents(episoded, entities, seed=7)
    assert specs == plan_documents(episoded, entities, seed=7), "planner not deterministic"

    fact_docs = [s for s in specs if s["kind"] == "fact"]
    homes = Counter(f for s in fact_docs for f in s["home_fact_ids"])
    assert set(homes) == set(by_id) and set(homes.values()) == {1}, "every fact needs exactly one home"

    for s in fact_docs:
        assert 1 <= len(s["home_fact_ids"]) <= cfg["max_facts_per_doc"]
        assert all(by_id[f]["episode_id"] == s["episode"] for f in s["home_fact_ids"]), "home facts span episodes"
        for f in s["mention_fact_ids"]:
            fact = by_id[f]
            assert fact["episode_id"] <= s["episode"], "mention before the fact existed"
            assert fact["superseded_in_episode"] is None or s["episode"] < fact["superseded_in_episode"], \
                "mention after the fact stopped being true"
    mentions = Counter(f for s in fact_docs for f in s["mention_fact_ids"])
    assert all(n <= cfg["max_extra_mentions"] for n in mentions.values())

    # A replacement fact lives in a later document than the fact it replaced.
    home_ep = {f: s["episode"] for s in fact_docs for f in s["home_fact_ids"]}
    for old in (t for t in episoded if t["superseded_in_episode"] is not None):
        new = next(t for t in episoded if t["subject"] == old["subject"] and t["predicate"] == old["predicate"]
                   and t["episode_id"] == old["superseded_in_episode"] and t["superseded_in_episode"] is None)
        assert home_ep[old["fact_id"]] < home_ep[new["fact_id"]]

    distractors = [s for s in specs if s["kind"] != "fact"]
    assert 0.15 <= len(distractors) / len(specs) <= 0.30, "distractor share out of range"
    real = {normalise_name(e["display_name"]) for e in entities.values()}
    for s in distractors:
        if s["kind"] == "lookalike":
            assert normalise_name(s["entity_names"][0]) not in real, "look-alike collides with a real name"

    print(f"generation/document_planner.py: OK ({len(fact_docs)} fact docs, {len(distractors)} distractors)")
