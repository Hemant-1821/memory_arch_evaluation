"""Vector-only condition (reference doc 3.2): documents split into fixed-size
overlapping word chunks, embedded locally (decision 3.1) and stored in Qdrant with
episode/source metadata. Loading only ever adds - when a fact is replaced, the old
chunk stays in the store, which is the write behaviour under study."""
import os
import uuid

import yaml
from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

with open("configs/memory.yaml") as f:
    CONFIG = yaml.safe_load(f)


def chunk_document(doc, size=CONFIG["chunk_words"], overlap=CONFIG["chunk_overlap_words"]) -> list[dict]:
    words = doc["text"].split()
    starts = range(0, max(len(words) - overlap, 1), size - overlap)  # last chunk always reaches the end
    return [{"chunk_id": f"{doc['doc_id']}_c{i}", "doc_id": doc["doc_id"], "episode": doc["episode"],
             "text": " ".join(words[s:s + size])} for i, s in enumerate(starts)]


class VectorMemory:
    def __init__(self, collection: str):
        self.collection = collection
        self.client = QdrantClient(url=CONFIG["qdrant_url"])
        self.model = TextEmbedding(CONFIG["embedding_model"], cache_dir=os.path.expanduser("~/.cache/fastembed"))

    def load(self, docs) -> int:
        """Rebuilds the collection from scratch, so reloading a dataset is idempotent."""
        chunks = [c for d in docs for c in chunk_document(d)]
        vectors = list(self.model.passage_embed([c["text"] for c in chunks]))
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(self.collection, vectors_config=models.VectorParams(
            size=len(vectors[0]), distance=models.Distance.COSINE))
        self.client.upsert(self.collection, points=[
            models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])), vector=v.tolist(), payload=c)
            for c, v in zip(chunks, vectors)])
        return len(chunks)

    def search_memory(self, query: str, as_of_episode: int, k: int = CONFIG["top_k"]) -> list[dict]:
        """Top-k chunks by cosine similarity, from episodes the agent has lived through so far."""
        vector = next(iter(self.model.query_embed([query]))).tolist()
        hits = self.client.query_points(self.collection, query=vector, limit=k, query_filter=models.Filter(
            must=[models.FieldCondition(key="episode", range=models.Range(lte=as_of_episode))])).points
        return [dict(h.payload, score=round(h.score, 4)) for h in hits]


if __name__ == "__main__":
    long_doc = {"doc_id": "d0", "episode": 0, "text": " ".join(f"w{i}" for i in range(250))}
    chunks = chunk_document(long_doc)
    assert len(chunks) == 3 and chunks[-1]["text"].endswith("w249"), "last chunk must reach the end"
    assert chunks[1]["text"].split()[0] == "w90", "chunks must overlap by 30 words"
    assert len(chunk_document({"doc_id": "d1", "episode": 0, "text": "one short note"})) == 1

    memory = VectorMemory("selfcheck")
    memory.load([{"doc_id": "a", "episode": 0, "text": "Kivo Ranet leads project Lumen Vault."},
                 {"doc_id": "b", "episode": 1, "text": "Mira Olsen now leads project Lumen Vault."},
                 {"doc_id": "c", "episode": 0, "text": "The canteen is closed on Friday for cleaning."}])
    assert memory.search_memory("Who leads Lumen Vault?", as_of_episode=0, k=1)[0]["doc_id"] == "a"
    assert {h["doc_id"] for h in memory.search_memory("Who leads Lumen Vault?", 1, k=2)} == {"a", "b"}, \
        "the old chunk must stay searchable after the fact changes"
    memory.client.delete_collection("selfcheck")
    print("vector_store self-check passed")
