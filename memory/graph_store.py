"""Knowledge-graph-only condition (reference doc 3.2): the LLM-extracted graph in
Neo4j, queried only through four fixed traversal tools (no raw Cypher), so neither
condition gets unlimited query power. Unlike the vector store, a newer fact
replaces the old one: the old edge is kept but marked invalid from that episode,
so the graph always shows one current state for whatever episode the agent is in."""
import os
from collections import defaultdict

import yaml
from neo4j import GraphDatabase

from generation.facts import normalise_name
from schema.validate_ontology import load_ontology

with open("configs/memory.yaml") as f:
    CONFIG = yaml.safe_load(f)

VALID = "r.valid_from <= $as_of AND (r.invalid_from IS NULL OR r.invalid_from > $as_of)"


def _single_valued(ontology) -> set[str]:
    """Predicates where a later, different object replaces the earlier one."""
    relations = {p for p, d in ontology["relation_types"].items() if d["replaceable"] and d["cardinality"] == "N:1"}
    attributes = {a for e in ontology["entity_types"].values() for a, d in e["attributes"].items() if d.get("replaceable")}
    return relations | attributes


def build_edges(triples, single_valued) -> list[dict]:
    """Merges repeated mentions into one edge (earliest episode wins) and sets
    invalid_from where a later episode gives the same subject a different object.
    ponytail: N:M replaceable predicates (works_at) are never invalidated - the
    text rarely says which project someone left; revisit if recall shows stale edges."""
    edges: dict[tuple, dict] = {}
    for t in sorted(triples, key=lambda t: t["episode"]):
        key = (t["subject"], t["predicate"], t["object"])
        edge = edges.setdefault(key, {"subject": t["subject"], "predicate": t["predicate"], "object": t["object"],
                                      "valid_from": t["episode"], "invalid_from": None, "doc_ids": []})
        edge["doc_ids"].append(t["doc_id"])
    by_slot = defaultdict(list)
    for e in edges.values():
        if e["predicate"] in single_valued:
            by_slot[(e["subject"], e["predicate"])].append(e)
    for slot in by_slot.values():
        for e in slot:
            later = [o["valid_from"] for o in slot if o["valid_from"] > e["valid_from"]]
            e["invalid_from"] = min(later, default=None)
    return list(edges.values())


class GraphMemory:
    def __init__(self, dataset: str):
        self.dataset = dataset
        self.driver = GraphDatabase.driver(CONFIG["neo4j_uri"],
                                           auth=("neo4j", os.environ.get("NEO4J_PASSWORD") or "memarch-local"))

    def _run(self, query, **params):
        return [r.data() for r in self.driver.execute_query(query, params, dataset=self.dataset).records]

    def load(self, kg) -> int:
        """Replaces this dataset's graph. Attribute values (e.g. status 'active') become Value nodes."""
        edges = build_edges(kg["triples"], _single_valued(load_ontology()))
        nodes = [{"id": n["node_id"], "name": n["name"], "type": n["entity_type"]} for n in kg["nodes"]]
        known = {n["id"] for n in nodes}
        nodes += [{"id": f"val_{o}", "name": o, "type": "Value"} for o in {e["object"] for e in edges} - known]
        for e in edges:
            e["object"] = e["object"] if e["object"] in known else f"val_{e['object']}"
        self._run("MATCH (n:Node {dataset: $dataset}) DETACH DELETE n")
        self._run("UNWIND $nodes AS n CREATE (:Node {dataset: $dataset, id: n.id, name: n.name, "
                  "norm: n.norm, type: n.type})", nodes=[dict(n, norm=normalise_name(n["name"])) for n in nodes])
        for t in {n["type"] for n in nodes}:  # display-only label, so Neo4j Browser colours each type
            assert t.isidentifier(), t  # labels can't be query parameters
            self._run(f"MATCH (n:Node {{dataset: $dataset, type: $t}}) SET n:{t}", t=t)
        self._run("UNWIND $edges AS e MATCH (s:Node {dataset: $dataset, id: e.subject}), "
                  "(o:Node {dataset: $dataset, id: e.object}) CREATE (s)-[:REL {predicate: e.predicate, "
                  "valid_from: e.valid_from, invalid_from: e.invalid_from, doc_ids: e.doc_ids}]->(o)", edges=edges)
        return len(edges)

    # --- the four agent tools; as_of_episode is set by the harness, not the agent ---

    def find_entity(self, name: str) -> list[dict]:
        """Entities whose name contains the given text."""
        return self._run("MATCH (n:Node {dataset: $dataset}) WHERE n.type <> 'Value' AND n.norm CONTAINS $q "
                         "RETURN n.name AS name, n.type AS type ORDER BY size(n.norm) LIMIT 10",
                         q=normalise_name(name))

    def get_neighbours(self, name: str, as_of_episode: int) -> list[dict]:
        return self._run(f"MATCH (s:Node {{dataset: $dataset}})-[r:REL]->(o:Node) WHERE (s.norm = $q OR o.norm = $q) "
                         f"AND {VALID} RETURN s.name AS subject, r.predicate AS predicate, o.name AS object "
                         f"ORDER BY predicate, object", q=normalise_name(name), as_of=as_of_episode)

    def follow_relation(self, name: str, predicate: str, as_of_episode: int, direction: str = "out") -> list[str]:
        start, end = ("s", "o") if direction == "out" else ("o", "s")
        rows = self._run(f"MATCH (s:Node {{dataset: $dataset}})-[r:REL {{predicate: $p}}]->(o:Node) "
                         f"WHERE {start}.norm = $q AND {VALID} RETURN DISTINCT {end}.name AS name ORDER BY name",
                         q=normalise_name(name), p=predicate, as_of=as_of_episode)
        return [r["name"] for r in rows]

    def filter_by_attribute(self, entity_type: str, predicate: str, value: str, as_of_episode: int) -> list[str]:
        """Entities of a type linked by `predicate` to `value`, e.g. ('Project', 'status', 'active')."""
        rows = self._run(f"MATCH (s:Node {{dataset: $dataset, type: $t}})-[r:REL {{predicate: $p}}]->(o:Node) "
                         f"WHERE o.norm = $v AND {VALID} RETURN DISTINCT s.name AS name ORDER BY name",
                         t=entity_type, p=predicate, v=normalise_name(value), as_of=as_of_episode)
        return [r["name"] for r in rows]


if __name__ == "__main__":
    kg = {"nodes": [{"node_id": "e1", "name": "Dr. Kivo Ranet", "entity_type": "Person"},
                    {"node_id": "e2", "name": "Mira Olsen", "entity_type": "Person"},
                    {"node_id": "e3", "name": "Lumen Vault", "entity_type": "Project"},
                    {"node_id": "e4", "name": "Photonic Sensing Group", "entity_type": "Team"}],
          "triples": [{"subject": "e1", "predicate": "leads", "object": "e3", "doc_id": "a", "episode": 0},
                      {"subject": "e1", "predicate": "leads", "object": "e3", "doc_id": "b", "episode": 1},
                      {"subject": "e2", "predicate": "member_of", "object": "e4", "doc_id": "a", "episode": 0},
                      {"subject": "e3", "predicate": "status", "object": "proposed", "doc_id": "a", "episode": 0},
                      {"subject": "e3", "predicate": "status", "object": "active", "doc_id": "c", "episode": 2},
                      {"subject": "e1", "predicate": "works_at", "object": "e3", "doc_id": "a", "episode": 0}]}
    edges = build_edges(kg["triples"], _single_valued(load_ontology()))
    assert len(edges) == 5, "repeated mentions of the same fact must merge into one edge"
    assert next(e for e in edges if e["object"] == "proposed")["invalid_from"] == 2
    assert next(e for e in edges if e["predicate"] == "leads")["invalid_from"] is None, "re-mention is not a change"

    g = GraphMemory("selfcheck")
    try:
        assert g.load(kg) == 5
        assert g.find_entity("kivo") == [{"name": "Dr. Kivo Ranet", "type": "Person"}]
        assert g.filter_by_attribute("Project", "status", "Proposed", as_of_episode=1) == ["Lumen Vault"]
        assert g.filter_by_attribute("Project", "status", "proposed", as_of_episode=2) == [], "old status must expire"
        assert g.follow_relation("Lumen Vault", "status", as_of_episode=2) == ["active"]
        assert g.follow_relation("Lumen Vault", "leads", 0, direction="in") == ["Dr. Kivo Ranet"]
        assert g.follow_relation("Lumen Vault", "status", as_of_episode=0) == ["proposed"], "future facts must be hidden"
        assert len(g.get_neighbours("kivo ranet", 0)) == 2
    finally:
        g._run("MATCH (n:Node {dataset: $dataset}) DETACH DELETE n")
        g.driver.close()
    print("graph_store self-check passed")
