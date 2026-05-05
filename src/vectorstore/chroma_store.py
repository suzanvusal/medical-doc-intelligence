"""ChromaDB vector store for medical document embeddings."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    chunk_id:    str
    document_id: str
    content:     str
    score:       float
    metadata:    dict[str, Any]


class MedicalChromaStore:
    """Manages ChromaDB collections for medical document chunks."""

    def __init__(self, host: str = "localhost", port: int = 8001,
                 collection_prefix: str = "medical") -> None:
        self.client = chromadb.HttpClient(
            host=host, port=port,
            settings=Settings(anonymized_telemetry=False),
        )
        self.prefix = collection_prefix
        self._collections: dict[str, Any] = {}

    def _get_collection(self, doc_type: str = "default"):
        name = f"{self.prefix}_{doc_type}"
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    def upsert(self, chunk_id: str, document_id: str, content: str,
               embedding: list[float], metadata: dict | None = None,
               doc_type: str = "default") -> None:
        col = self._get_collection(doc_type)
        col.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{"document_id": document_id, **(metadata or {})}],
        )

    def search(self, query_embedding: list[float], top_k: int = 5,
               doc_type: str = "default",
               filters: dict | None = None) -> list[SearchResult]:
        col = self._get_collection(doc_type)
        where = filters if filters else None
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )
        hits = []
        for i, chunk_id in enumerate(results["ids"][0]):
            hits.append(SearchResult(
                chunk_id=chunk_id,
                document_id=results["metadatas"][0][i].get("document_id", ""),
                content=results["documents"][0][i],
                score=1 - results["distances"][0][i],
                metadata=results["metadatas"][0][i],
            ))
        return hits

    def delete_document(self, document_id: str,
                        doc_type: str = "default") -> None:
        col = self._get_collection(doc_type)
        col.delete(where={"document_id": document_id})
        logger.info("Deleted document %s from collection %s", document_id, doc_type)

    def collection_stats(self, doc_type: str = "default") -> dict:
        col = self._get_collection(doc_type)
        return {"count": col.count(), "name": col.name}

# 11:22:02 — feat: add vector store backup utility to S3

# 11:22:02 — test: add ChromaDB integration tests with real embeddings

# 11:22:02 — fix: ChromaDB collection name validation rejecting valid nam

# 11:22:02 — refactor: abstract vector store behind VectorStoreInterface
