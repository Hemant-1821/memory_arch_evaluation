"""Loads and cross-validates schema/ontology.yaml.

Every other generation script imports load_ontology() from here rather than
reading the YAML directly, so ontology validity is checked exactly once,
in one place.
"""
import yaml

VALID_ATTR_TYPES = {"string", "enum", "date", "ref", "list_of_refs"}


def load_ontology(path: str = "schema/ontology.yaml") -> dict:
    with open(path) as f:
        ontology = yaml.safe_load(f)
    _validate(ontology)
    return ontology


def _validate(ontology: dict) -> None:
    entity_types = ontology["entity_types"]
    relation_types = ontology["relation_types"]

    for entity_name, entity_def in entity_types.items():
        for attr_name, attr_def in entity_def["attributes"].items():
            attr_type = attr_def["type"]
            if attr_type not in VALID_ATTR_TYPES:
                raise ValueError(
                    f"{entity_name}.{attr_name}: unknown attribute type '{attr_type}'"
                )
            if attr_type == "enum" and not attr_def.get("values"):
                raise ValueError(f"{entity_name}.{attr_name}: enum with no values")
            if attr_type in ("ref", "list_of_refs"):
                relation = attr_def.get("via_relation")
                if relation not in relation_types:
                    raise ValueError(
                        f"{entity_name}.{attr_name}: via_relation '{relation}' "
                        f"is not a declared relation type"
                    )

    for rel_name, rel_def in relation_types.items():
        for source_type in rel_def["source_types"]:
            if source_type not in entity_types:
                raise ValueError(
                    f"relation '{rel_name}': source type '{source_type}' "
                    f"is not a declared entity type"
                )
        target_type = rel_def["target_type"]
        if target_type not in entity_types:
            raise ValueError(
                f"relation '{rel_name}': target type '{target_type}' "
                f"is not a declared entity type"
            )


if __name__ == "__main__":
    # Self-check: the real ontology loads cleanly...
    ontology = load_ontology()
    assert len(ontology["entity_types"]) == 9, "expected 9 entity types"
    # 14 from the reference doc's list + sponsors (backs Project.sponsor_org)
    # + concerns (backs Meeting.project) - both gaps flagged and agreed with user.
    assert len(ontology["relation_types"]) == 16, "expected 16 relation types"

    # ...and the validator actually catches a broken cross-reference, not just
    # always saying "OK" (proves the checks fire, not just parse successfully).
    broken = dict(ontology)
    broken["relation_types"] = dict(ontology["relation_types"])
    broken["relation_types"]["fake_relation"] = {
        "source_types": ["NoSuchEntity"],
        "target_type": "Person",
        "cardinality": "N:1",
        "replaceable": False,
    }
    try:
        _validate(broken)
        raise AssertionError("validator failed to catch a bad source type")
    except ValueError:
        pass

    print("schema/ontology.yaml: OK (9 entity types, 16 relation types, all refs resolve)")
