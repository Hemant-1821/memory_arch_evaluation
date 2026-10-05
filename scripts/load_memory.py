"""Loads a generated dataset into both memory stores: documents into Qdrant
(vector condition), the extracted KG into Neo4j (graph condition). The hybrid
condition reads both. No LLM calls. Needs `docker compose up -d`.

Run: python -m scripts.load_memory [data/kg_pilot]
"""
import sys
from pathlib import Path

from generation.dataset_io import load_json
from memory.graph_store import GraphMemory
from memory.vector_store import VectorMemory


def main(dataset_dir="data/kg_pilot") -> None:
    data, name = Path(dataset_dir), Path(dataset_dir).name
    vector = VectorMemory(name)
    chunks = vector.load(load_json(data / "documents.json"))
    graph = GraphMemory(name)
    edges = graph.load(load_json(data / "extracted_kg.json"))
    print(f"{name}: {chunks} chunks in Qdrant, {edges} edges in Neo4j")

    # smoke test: one real task's entities must be findable in both stores
    task = next(t for t in load_json(data / "tasks.json") if t["status"] == "kept")
    print("task:", task["question"])
    for hit in vector.search_memory(task["question"], task["as_of_episode"], k=2):
        print(f"  vector  {hit['score']}  {hit['text'][:90]}")
    entity = load_json(data / "entities.json")[task["source_entities"][0]]["display_name"]
    print(f"  graph   {entity}: {graph.get_neighbours(entity, task['as_of_episode'])[:4]}")
    graph.driver.close()


if __name__ == "__main__":
    main(*sys.argv[1:])
