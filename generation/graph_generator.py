"""Procedural knowledge graph generation (reference doc: "the graph is
generated before any text and is the only source of truth"). Reads
schema/ontology.yaml and configs/sizing.yaml - nothing here hardcodes
entity/relation names or counts.

Run as a module: python -m generation.graph_generator
"""
import pickle
import random
from datetime import date, timedelta
from pathlib import Path

import networkx as nx
import yaml

from schema.validate_ontology import load_ontology
from generation.entity_namer import generate_names_raw
from generation.seeding import derive_seed
from generation.dataset_io import save_json

_START_DATE = date(2021, 1, 1)
_END_DATE = date(2026, 1, 1)


def _random_date(rng: random.Random) -> str:
    span = (_END_DATE - _START_DATE).days
    return (_START_DATE + timedelta(days=rng.randint(0, span))).isoformat()


def _load_sizing(pilot: bool) -> dict:
    with open("configs/sizing.yaml") as f:
        sizing = yaml.safe_load(f)
    key = "pilot" if pilot else "full"
    return sizing[key]


def _count_for(entity_type: str, sizing: dict, rng: random.Random, pilot: bool) -> int:
    spec = sizing[entity_type]
    if pilot:
        return spec  # pilot sizing is a flat int, not a min/max range
    return rng.randint(spec["min"], spec["max"])


def _invented_string(rng: random.Random) -> str:
    # rng is already a deterministic stream, so its own next int is a fine
    # deterministic sub-seed - no need to route through derive_seed here.
    return generate_names_raw("Location", 1, seed=rng.randint(0, 10_000_000))[0]


def _generate_entities(ontology: dict, sizing: dict, seed: int, pilot: bool) -> dict:
    entities = {}
    for entity_type, entity_def in ontology["entity_types"].items():
        rng = random.Random(derive_seed(seed, "entities", entity_type))
        count = _count_for(entity_type, sizing, rng, pilot)
        names = generate_names_raw(entity_type, count, seed)
        for i, name in enumerate(names):
            entity_id = f"{entity_type}_{i:04d}"
            # "entity_type", not "type" - Equipment has its own domain
            # attribute literally named "type" (compute_cluster, etc.),
            # which would otherwise collide with this bookkeeping key.
            # display_name = the generated name, used whenever a fact is written
            # as text. Meeting has no name attribute, so this is its only label.
            attrs = {"entity_type": entity_type, "display_name": name}
            for attr_name, attr_def in entity_def["attributes"].items():
                if attr_def["type"] == "string":
                    attrs[attr_name] = name if attr_name in ("name", "title", "city") else _invented_string(rng)
                elif attr_def["type"] == "enum":
                    attrs[attr_name] = rng.choice(attr_def["values"])
                elif attr_def["type"] == "date":
                    attrs[attr_name] = _random_date(rng)
                # ref / list_of_refs are populated by relation wiring below, not here
            entities[entity_id] = attrs
    return entities


def _ids_of_type(entities: dict, entity_type: str) -> list[str]:
    return [eid for eid, attrs in entities.items() if attrs["entity_type"] == entity_type]


def _wire_relation(
    triples: list[dict], entities: dict, rel_name: str, rel_def: dict, rng: random.Random
) -> None:
    target_ids = _ids_of_type(entities, rel_def["target_type"])
    if not target_ids:
        return
    for source_type in rel_def["source_types"]:
        source_ids = _ids_of_type(entities, source_type)
        for source_id in source_ids:
            if rel_def["cardinality"] in ("N:1", "1:1"):
                if rng.random() < 0.9:  # not every entity necessarily has every N:1 link
                    triples.append({
                        "subject": source_id, "predicate": rel_name,
                        "object": rng.choice(target_ids),
                    })
            else:  # N:M or 1:N - each source can link to several targets
                k = rng.randint(1, min(3, len(target_ids)))
                for target_id in rng.sample(target_ids, k):
                    if rng.random() < 0.5:
                        triples.append({
                            "subject": source_id, "predicate": rel_name,
                            "object": target_id,
                        })


def _add_replaceable_attribute_triples(triples: list[dict], entities: dict, ontology: dict) -> None:
    """Literal attributes flagged replaceable: true become attribute-triples
    too (e.g. Project.status), per the agreed unified triple model."""
    for entity_id, attrs in entities.items():
        entity_def = ontology["entity_types"][attrs["entity_type"]]
        for attr_name, attr_def in entity_def["attributes"].items():
            if attr_def.get("replaceable") and attr_name in attrs:
                triples.append({
                    "subject": entity_id, "predicate": attr_name,
                    "object": attrs[attr_name],
                })


def _enrich_for_staffing_queries(triples: list[dict], entities: dict, rng: random.Random) -> None:
    """Deliberately engineers the constraint-satisfaction opportunities the
    high-complexity tier needs (reference doc §1, §3.1): overlapping skills
    across active projects, people on 2+ active projects, and a real,
    derivable conflict of interest. A purely random wire-up would make
    staffing-style queries answerable by luck rather than by design, or not
    answerable at all.

    Conflict of interest is NEVER stored as a flag - it's always computed at
    query time (task_generator.has_conflict_of_interest) from a structural
    condition: a person already leads a different active project that shares
    a sponsor with the project being staffed. This function creates that
    precondition (two active projects sponsored by the same org, one led by
    a person) so at least one real, explainable COI exists in the graph -
    not an arbitrary label with no underlying reason.
    """
    active_projects = [
        eid for eid in _ids_of_type(entities, "Project")
        if entities[eid].get("status") == "active"
    ]
    people = _ids_of_type(entities, "Person")
    skills = _ids_of_type(entities, "Skill")
    orgs = _ids_of_type(entities, "PartnerOrganization")
    if len(active_projects) < 2 or len(people) < 4 or len(skills) < 2 or not orgs:
        return  # pilot graph too small for this enrichment - fine, not required

    # Force skill overlap: two active projects share 2 required skills - chosen
    # from skills 2+ people actually hold, else nobody could ever staff them.
    holders = {s: {t["subject"] for t in triples if t["predicate"] == "has_skill" and t["object"] == s}
               for s in skills}
    held = [s for s in skills if len(holders[s]) >= 2]
    shared_skills = rng.sample(held, 2) if len(held) >= 2 else rng.sample(skills, 2)
    for skill_id in shared_skills:
        for person_id in rng.sample(people, max(0, 2 - len(holders[skill_id]))):
            triples.append({"subject": person_id, "predicate": "has_skill", "object": skill_id})
    for project_id in rng.sample(active_projects, 2):
        for skill_id in shared_skills:
            triples.append({
                "subject": project_id, "predicate": "requires_skill",
                "object": skill_id,
            })

    # Force multi-project staffing: some people work_at 2+ active projects.
    multi_project_people = rng.sample(people, max(1, len(people) // 5))
    for person_id in multi_project_people:
        for project_id in rng.sample(active_projects, min(2, len(active_projects))):
            triples.append({
                "subject": person_id, "predicate": "works_at",
                "object": project_id,
            })

    # Derived conflict of interest: one sponsor funds two active projects,
    # and a person already leads one of them - so that person has a
    # competing stake if staffed on the other (see docstring above).
    sponsor = rng.choice(orgs)
    coi_project_a, coi_project_b = rng.sample(active_projects, 2)
    triples.append({"subject": sponsor, "predicate": "sponsors", "object": coi_project_a})
    triples.append({"subject": sponsor, "predicate": "sponsors", "object": coi_project_b})
    conflicted_person = rng.choice(people)
    # `leads` is N:1 - move any existing leadership rather than add a second one.
    triples[:] = [t for t in triples if not (t["subject"] == conflicted_person and t["predicate"] == "leads")]
    triples.append({"subject": conflicted_person, "predicate": "leads", "object": coi_project_a})


MIN_ACTIVE_PROJECTS = 3  # enrichment needs 2 (the COI pair); +1 spare in case one changes status later


def _ensure_active_projects(entities: dict, rng: random.Random) -> None:
    """Guarantees the precondition of _enrich_for_staffing_queries. Random
    statuses alone can leave no project active (it happened on the seed-7
    pilot), which silently removes every high-complexity staffing task."""
    projects = _ids_of_type(entities, "Project")
    inactive = [p for p in projects if entities[p]["status"] != "active"]
    shortfall = MIN_ACTIVE_PROJECTS - (len(projects) - len(inactive))
    for p in rng.sample(inactive, max(0, min(shortfall, len(inactive)))):
        entities[p]["status"] = "active"


def generate_graph(seed: int, pilot: bool = False) -> tuple[list[dict], dict]:
    ontology = load_ontology()
    sizing = _load_sizing(pilot)
    entities = _generate_entities(ontology, sizing, seed, pilot)
    _ensure_active_projects(entities, random.Random(derive_seed(seed, "active_projects")))

    triples: list[dict] = []
    rel_rng = random.Random(derive_seed(seed, "relations"))
    for rel_name, rel_def in ontology["relation_types"].items():
        _wire_relation(triples, entities, rel_name, rel_def, rel_rng)

    _add_replaceable_attribute_triples(triples, entities, ontology)
    _enrich_for_staffing_queries(triples, entities, random.Random(derive_seed(seed, "enrichment")))

    # Enrichment can re-add a fact the random wiring already made; a duplicate
    # would double-count workload in the staffing checker. Keep first occurrence.
    unique = {(t["subject"], t["predicate"], t["object"]): t for t in reversed(triples)}
    triples = [t for t in triples if unique.get((t["subject"], t["predicate"], t["object"])) is t]
    return triples, entities


def _build_networkx_graph(triples: list[dict], entities: dict) -> nx.MultiDiGraph:
    """NetworkX-native serialization of the entity-to-entity edges (spec §3:
    "both a NetworkX-native serialization ... and a portable triples.json").
    Literal attribute-triples (object is a value, not an entity id) have no
    second node to connect to, so they stay in triples.json only - the graph
    captures structure, triples.json remains the complete fact record."""
    g = nx.MultiDiGraph()
    for entity_id, attrs in entities.items():
        g.add_node(entity_id, **attrs)
    for t in triples:
        obj = t["object"]
        if isinstance(obj, str) and obj in entities:
            g.add_edge(t["subject"], obj, predicate=t["predicate"])
    return g


def save_graph(triples: list[dict], entities: dict, out_dir: str = "data/kg") -> None:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    save_json(f"{out_dir}/triples.json", triples)
    save_json(f"{out_dir}/entities.json", entities)
    graph = _build_networkx_graph(triples, entities)
    with open(f"{out_dir}/graph.gpickle", "wb") as f:
        pickle.dump(graph, f)


if __name__ == "__main__":
    # Determinism: same seed, same pilot flag -> identical output.
    t1, e1 = generate_graph(seed=7, pilot=True)
    t2, e2 = generate_graph(seed=7, pilot=True)
    assert t1 == t2 and e1 == e2, "graph generation is not deterministic"

    # Cardinality: every N:1/1:1 relation has at most one live edge per subject.
    ontology = load_ontology()
    for rel_name, rel_def in ontology["relation_types"].items():
        if rel_def["cardinality"] in ("N:1", "1:1"):
            by_subject: dict[str, int] = {}
            for triple in t1:
                if triple["predicate"] == rel_name:
                    by_subject[triple["subject"]] = by_subject.get(triple["subject"], 0) + 1
            assert all(n <= 1 for n in by_subject.values()), (
                f"{rel_name} (N:1) has a subject with >1 live edge"
            )

    # No dangling references: every triple object that looks like an entity id
    # (matches "<EntityType>_####") resolves to a real generated entity.
    for triple in t1:
        obj = triple["object"]
        if isinstance(obj, str) and "_" in obj and obj.split("_")[-1].isdigit():
            assert obj in e1, f"dangling reference: {triple} -> missing {obj}"

    assert len({(t["subject"], t["predicate"], t["object"]) for t in t1}) == len(t1), "duplicate facts"

    # The staffing enrichment actually ran (it silently skips itself when fewer
    # than 2 projects are active - no escape clause here): enough active
    # projects, one with >=2 required skills, and a real derived COI.
    from generation.task_generator import has_conflict_of_interest
    active_projects = [eid for eid, a in e1.items() if a["entity_type"] == "Project" and a["status"] == "active"]
    assert len(active_projects) >= MIN_ACTIVE_PROJECTS, "not enough active projects"
    assert any(sum(t["predicate"] == "requires_skill" and t["subject"] == p for t in t1) >= 2
               for p in active_projects), "no active project needs 2+ skills"
    people = [eid for eid, a in e1.items() if a["entity_type"] == "Person"]
    assert any(has_conflict_of_interest(x, p, e1, t1) for x in people for p in active_projects), \
        "enrichment did not create a derivable conflict of interest"

    # Temp dir: scripts/run_pipeline.py is the only writer of data/kg_pilot/.
    import tempfile
    tmp = tempfile.mkdtemp()
    save_graph(t1, e1, out_dir=tmp)
    with open(f"{tmp}/graph.gpickle", "rb") as f:
        reloaded = pickle.load(f)
    assert reloaded.number_of_nodes() == len(e1), "gpickle node count mismatch"
    assert all("display_name" in a for a in e1.values()), "every entity needs a display_name"

    print(f"generation/graph_generator.py: OK ({len(e1)} entities, {len(t1)} triples)")
