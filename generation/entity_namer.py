"""Code-only invented-name generation for every entity type (reference doc
principle #2: all names are invented, code-generated, and checkable without
model judgement - an LLM would just return common invented names already in
its own training data, defeating the point).
"""
import random

from generation.seeding import derive_seed

_CONSONANTS = list("brtnkvmslpdfgzh")
_VOWELS = list("aeiou")

_PROJECT_PREFIXES = ["Aeon", "Vantor", "Lumen", "Kestrel", "Nomos", "Halcyon",
                      "Ferrix", "Solace", "Tundra", "Virel", "Corvid", "Ashen"]
_PROJECT_SUFFIXES = ["Initiative", "Array", "Protocol", "Bridge", "Forge",
                      "Nexus", "Cascade", "Loop", "Vault", "Signal"]
_TEAM_FOCUS_WORDS = ["Cryogenics", "Swarm Robotics", "Photonic Sensing",
                      "Bio-Fabrication", "Grid Resilience", "Adaptive Materials"]
_ORG_SUFFIXES = ["Dynamics", "Collective", "Foundry", "Systems", "Works", "Labs"]
_PUB_TOPIC_WORDS = ["resilient", "adaptive", "distributed", "low-power",
                     "scalable", "self-calibrating", "cross-domain"]
_PUB_SUBJECT_WORDS = ["sensor fusion", "materials synthesis", "swarm control",
                       "thermal regulation", "signal compression"]


def _syllable(rng: random.Random) -> str:
    s = rng.choice(_CONSONANTS) + rng.choice(_VOWELS)
    if rng.random() < 0.4:
        s += rng.choice(_CONSONANTS)
    return s


def _invented_word(rng: random.Random, syllables: int) -> str:
    word = "".join(_syllable(rng) for _ in range(syllables))
    return word.capitalize()


def _generate_person_names(rng: random.Random, count: int) -> list[str]:
    names = set()
    while len(names) < count:
        given = _invented_word(rng, rng.choice([2, 3]))
        family = _invented_word(rng, rng.choice([2, 3]))
        names.add(f"{given} {family}")
    return list(names)[:count]


def _generate_team_names(rng: random.Random, count: int) -> list[str]:
    # _TEAM_FOCUS_WORDS alone gives only len(_TEAM_FOCUS_WORDS) combinations -
    # too few once count exceeds it. Pairing with an invented word keeps the
    # Solstice flavor while making the pool effectively unbounded.
    names = set()
    while len(names) < count:
        names.add(f"{rng.choice(_TEAM_FOCUS_WORDS)} {_invented_word(rng, 2)} Group")
    return list(names)[:count]


def _generate_project_names(rng: random.Random, count: int) -> list[str]:
    names = set()
    while len(names) < count:
        names.add(f"{rng.choice(_PROJECT_PREFIXES)} {rng.choice(_PROJECT_SUFFIXES)}")
    return list(names)[:count]


def _generate_org_names(rng: random.Random, count: int) -> list[str]:
    names = set()
    while len(names) < count:
        names.add(f"{_invented_word(rng, 2)} {rng.choice(_ORG_SUFFIXES)}")
    return list(names)[:count]


def _generate_publication_titles(rng: random.Random, count: int) -> list[str]:
    # _PUB_TOPIC_WORDS x _PUB_SUBJECT_WORDS alone gives only 35 combinations -
    # too few for full-scale sizing (up to 120 publications). An invented
    # qualifier keeps the pool effectively unbounded.
    titles = set()
    while len(titles) < count:
        titles.add(
            f"Towards {rng.choice(_PUB_TOPIC_WORDS).capitalize()} "
            f"{rng.choice(_PUB_SUBJECT_WORDS)}: A {_invented_word(rng, 2)} Approach"
        )
    return list(titles)[:count]


def _generate_location_names(rng: random.Random, count: int) -> list[str]:
    # Invented city names (reference doc principle #2 applies to every entity
    # type, including Location - a real city could leak real timezone/region
    # facts the backbone model already knows).
    names = set()
    while len(names) < count:
        names.add(_invented_word(rng, rng.choice([2, 3])))
    return list(names)[:count]


def _generate_skill_names(rng: random.Random, count: int) -> list[str]:
    words = ["Cryogenic Control", "Swarm Coordination", "Photonic Design",
             "Bio-Fabrication", "Grid Modeling", "Adaptive Materials",
             "Signal Processing", "Thermal Systems", "Sensor Fusion",
             "Distributed Control"]
    rng.shuffle(words)
    names = set(words)
    while len(names) < count:
        names.add(f"{_invented_word(rng, 2)} Engineering")
    return list(names)[:count]


def _generate_equipment_names(rng: random.Random, count: int) -> list[str]:
    names = set()
    while len(names) < count:
        names.add(f"{_invented_word(rng, 2)}-{rng.randint(100, 999)}")
    return list(names)[:count]


def _generate_meeting_labels(rng: random.Random, count: int) -> list[str]:
    kinds = ["Sync", "Review", "Planning Session", "Retrospective", "Kickoff"]
    labels = set()
    while len(labels) < count:
        labels.add(f"{rng.choice(kinds)} {rng.randint(1, 9999)}")
    return list(labels)[:count]


_GENERATORS = {
    "Person": _generate_person_names,
    "Team": _generate_team_names,
    "Project": _generate_project_names,
    "PartnerOrganization": _generate_org_names,
    "Publication": _generate_publication_titles,
    "Location": _generate_location_names,
    "Skill": _generate_skill_names,
    "Equipment": _generate_equipment_names,
    "Meeting": _generate_meeting_labels,
}


def generate_names_raw(entity_type: str, count: int, seed: int) -> list[str]:
    """Deterministic, code-only name generation. Used directly by
    graph_generator.py - NOT verification-gated (see generate_verified_name_pool)."""
    if entity_type not in _GENERATORS:
        raise ValueError(f"no name generator for entity type '{entity_type}'")
    rng = random.Random(derive_seed(seed, entity_type))
    return _GENERATORS[entity_type](rng, count)


def verify_name_not_in_training_data(name: str) -> bool:
    """Stub: needs the backbone LLM to confirm it can't describe/recognize `name`.
    Real implementation: prompt the backbone with the name alone and check for
    a non-answer/refusal-to-recognize response."""
    raise NotImplementedError(
        "requires backbone LLM access - see reference doc §3.1 step 2"
    )


def verify_name_not_real_person(name: str) -> bool:
    """Stub: needs a real-people-name list/lookup to check `name` against."""
    raise NotImplementedError(
        "requires a real-person-name reference list - see reference doc §3.1 step 2"
    )


def generate_verified_name_pool(
    entity_type: str, count: int, seed: int, overgeneration_factor: float = 1.3
) -> list[str]:
    """Structured so plugging in real verification later doesn't require
    touching generation logic above. Not callable yet - verification is stubbed."""
    import math
    raw_count = math.ceil(count * overgeneration_factor)
    candidates = generate_names_raw(entity_type, raw_count, seed)
    verified = [
        name for name in candidates
        if verify_name_not_in_training_data(name) and verify_name_not_real_person(name)
    ]
    return verified[:count]


if __name__ == "__main__":
    # Determinism: same seed -> identical output, for every entity type.
    for entity_type in _GENERATORS:
        a = generate_names_raw(entity_type, 10, seed=42)
        b = generate_names_raw(entity_type, 10, seed=42)
        assert a == b, f"{entity_type}: not deterministic"
        assert len(set(a)) == 10, f"{entity_type}: collision within pool"

    # Different seeds -> different pools (sanity, not a hard determinism check).
    assert generate_names_raw("Person", 10, seed=1) != generate_names_raw("Person", 10, seed=2)

    # The verification gate is wired up (raises), not silently bypassed.
    try:
        generate_verified_name_pool("Person", 5, seed=1)
        raise AssertionError("expected NotImplementedError from the verification gate")
    except NotImplementedError:
        pass

    print("generation/entity_namer.py: OK (deterministic, collision-free, verification gate wired)")
