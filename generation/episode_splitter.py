"""Splits a flat triple list into ordered ingestion episodes and simulates
replaceable facts changing in a later episode. This is the mechanism the
whole vector-vs-graph comparison depends on (reference doc §3.2, §6): a
graph store can update an edge in place, a vector store can only add more
text - so the old triple is tagged superseded_in_episode, never deleted.

Run as a module: python -m generation.episode_splitter
"""
import random

import yaml

from schema.validate_ontology import load_ontology
from generation.seeding import derive_seed


def _attr_def_for(predicate: str, ontology: dict) -> dict | None:
    for entity_def in ontology["entity_types"].values():
        attr_def = entity_def["attributes"].get(predicate)
        if attr_def is not None:
            return attr_def
    return None


def _load_episode_config(pilot: bool) -> tuple[int, float]:
    with open("configs/sizing.yaml") as f:
        sizing = yaml.safe_load(f)
    episodes = sizing["episodes"]
    count = episodes["pilot"] if pilot else episodes["full"]
    return count, episodes["replacement_fraction"]


def _is_replaceable(predicate: str, ontology: dict) -> bool:
    if predicate in ontology["relation_types"]:
        return ontology["relation_types"][predicate]["replaceable"]
    attr_def = _attr_def_for(predicate, ontology)
    return bool(attr_def and attr_def.get("replaceable"))


def _replacement_object(predicate: str, current_object, rng: random.Random, ontology: dict, all_ids_by_predicate: dict):
    if predicate not in ontology["relation_types"]:
        # Literal attribute (e.g. Project.status) - reuse the enum's own
        # values from the ontology rather than a second, unsynced copy here.
        attr_def = _attr_def_for(predicate, ontology)
        choices = [v for v in attr_def["values"] if v != current_object]
        return rng.choice(choices) if choices else current_object
    candidates = [o for o in all_ids_by_predicate.get(predicate, []) if o != current_object]
    return rng.choice(candidates) if candidates else current_object


def split_into_episodes(triples: list[dict], seed: int, pilot: bool = False) -> list[dict]:
    ontology = load_ontology()
    episode_count, replacement_fraction = _load_episode_config(pilot)
    rng = random.Random(derive_seed(seed, "episodes"))

    result = [dict(t, episode_id=rng.randint(0, episode_count - 1), superseded_in_episode=None)
              for t in triples]

    all_ids_by_predicate: dict[str, list] = {}
    for t in result:
        all_ids_by_predicate.setdefault(t["predicate"], []).append(t["object"])

    replaceable = [t for t in result if _is_replaceable(t["predicate"], ontology)]
    to_replace = rng.sample(replaceable, k=max(1, int(len(replaceable) * replacement_fraction))) if replaceable else []

    new_triples = []
    for original in to_replace:
        if original["episode_id"] >= episode_count - 1:
            continue
        later_episode = rng.randint(original["episode_id"] + 1, episode_count - 1)
        original["superseded_in_episode"] = later_episode
        new_object = _replacement_object(original["predicate"], original["object"], rng, ontology, all_ids_by_predicate)
        new_triples.append({
            "subject": original["subject"], "predicate": original["predicate"],
            "object": new_object,
            "episode_id": later_episode, "superseded_in_episode": None,
        })

    return result + new_triples


def current_state(triples: list[dict], as_of_episode: int) -> list[dict]:
    return [
        t for t in triples
        if t["episode_id"] <= as_of_episode
        and (t["superseded_in_episode"] is None or t["superseded_in_episode"] > as_of_episode)
    ]


if __name__ == "__main__":
    from generation.graph_generator import generate_graph

    triples, entities = generate_graph(seed=7, pilot=True)

    # Determinism.
    e1 = split_into_episodes(triples, seed=7, pilot=True)
    e2 = split_into_episodes(triples, seed=7, pilot=True)
    assert e1 == e2, "episode splitting is not deterministic"

    # At least one real superseded-triple example exists (not just scaffolded).
    superseded = [t for t in e1 if t["superseded_in_episode"] is not None]
    assert len(superseded) >= 1, "no triple was actually marked superseded"

    # Stale data must not leak: querying the same (subject, predicate) at an
    # early vs. a late as_of_episode gives different answers for a superseded fact.
    example = superseded[0]
    early = current_state(e1, as_of_episode=example["episode_id"])
    late = current_state(e1, as_of_episode=example["superseded_in_episode"])
    early_objects = {t["object"] for t in early if t["subject"] == example["subject"] and t["predicate"] == example["predicate"]}
    late_objects = {t["object"] for t in late if t["subject"] == example["subject"] and t["predicate"] == example["predicate"]}
    assert early_objects != late_objects, "superseded fact still visible unchanged in the later episode"
    assert example["object"] in early_objects and example["object"] not in late_objects, (
        "old value should be visible early and gone (replaced) late"
    )

    print(f"generation/episode_splitter.py: OK ({len(superseded)} superseded triples, supersession verified)")
