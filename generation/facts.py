"""Shared helpers: turn a ground-truth fact into a plain sentence, and compare
names the same way everywhere (fidelity check, entity resolution, grading)."""
import re

PREDICATE_TEMPLATES = {
    "member_of": "{s} is a member of the {o} team.",
    "works_at": "{s} works on project {o}.",
    "leads": "{s} leads project {o}.",
    "has_skill": "{s} has the skill {o}.",
    "requires_skill": "Project {s} requires the skill {o}.",
    "based_in": "{s} is based in {o}.",
    "partners_with": "Project {s} partners with {o}.",
    "authored": '{s} authored the publication "{o}".',
    "cites": 'The publication "{s}" cites "{o}".',
    "depends_on": "{s} depends on project {o}.",
    "attends": "{s} attended {o}.",
    "reports_to": "{s} reports to {o}.",
    "uses_resource": "Project {s} uses the equipment {o}.",
    "located_at": "{s} is located in {o}.",
    "sponsors": "{s} sponsors project {o}.",
    "concerns": "{s} concerns project {o}.",
    "status": "The status of project {s} is {o}.",
    "availability": "The availability of equipment {s} is {o}.",
}
TITLES = {"dr", "prof", "mr", "mrs", "ms"}


def display_name(value, entities) -> str:
    if isinstance(value, str) and value in entities:
        return entities[value]["display_name"]
    return str(value)


def period_label(episode: int) -> str:
    return f"Period {episode + 1}"


def fact_to_statement(triple, entities, with_period=False) -> str:
    text = PREDICATE_TEMPLATES[triple["predicate"]].format(
        s=display_name(triple["subject"], entities), o=display_name(triple["object"], entities))
    return f"As of {period_label(triple['episode_id'])}: {text}" if with_period else text


def normalise_name(name: str) -> str:
    words = re.sub(r"[^\w\s-]", " ", name.lower()).split()
    words = [w for w in words if w not in TITLES]
    if words and words[0] == "the":
        words = words[1:]
    return " ".join(words)


def contains_name(text: str, name: str) -> bool:
    target = normalise_name(name)
    return bool(target) and re.search(rf"(?<!\w){re.escape(target)}(?!\w)", normalise_name(text)) is not None


if __name__ == "__main__":
    from schema.validate_ontology import load_ontology
    ontology = load_ontology()
    replaceable_attrs = {a for e in ontology["entity_types"].values()
                         for a, d in e["attributes"].items() if d.get("replaceable")}
    missing = (set(ontology["relation_types"]) | replaceable_attrs) - set(PREDICATE_TEMPLATES)
    assert not missing, f"no sentence template for {missing}"

    assert normalise_name("Dr. Kivo  Ranet") == normalise_name("kivo ranet") == "kivo ranet"
    assert normalise_name("The Photonic Sensing Group") == "photonic sensing group"
    assert contains_name("Yesterday Dr. Kivo Ranet joined.", "Kivo Ranet")
    assert not contains_name("Kivvo Ranet joined.", "Kivo Ranet")

    ents = {"Person_0000": {"display_name": "Kivo Ranet"}, "Team_0000": {"display_name": "Photonic Sensing Group"}}
    t = {"subject": "Person_0000", "predicate": "member_of", "object": "Team_0000", "episode_id": 2}
    assert fact_to_statement(t, ents) == "Kivo Ranet is a member of the Photonic Sensing Group team."
    assert fact_to_statement(t, ents, with_period=True).startswith("As of Period 3:")
    print("generation/facts.py: OK")
