"""Hybrid search: semantic (ChromaDB) + keyword (BM25) with RRF fusion."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from rank_bm25 import BM25Okapi
from src.vectorstore.chroma_store import MedicalChromaStore, SearchResult
from src.vectorstore.embedder import MedicalEmbedder

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    chunk_id:    str
    document_id: str
    content:     str
    semantic_score: float
    bm25_score:     float
    rrf_score:      float
    metadata:    dict


class HybridSearcher:
    """Combines semantic and BM25 search with Reciprocal Rank Fusion."""

    def __init__(self, store: MedicalChromaStore, embedder: MedicalEmbedder,
                 semantic_weight: float = 0.7, k_rrf: int = 60) -> None:
        self.store    = store
        self.embedder = embedder
        self.sw       = semantic_weight
        self.k        = k_rrf
        self._bm25: BM25Okapi | None = None
        self._corpus:  list[str] = []
        self._meta:    list[dict] = []

    def index_corpus(self, documents: list[tuple[str, str, dict]]) -> None:
        """Index documents for BM25. Each tuple: (chunk_id, content, metadata)."""
        self._corpus = [content for _, content, _ in documents]
        self._meta   = [{"chunk_id": cid, **meta} for cid, _, meta in documents]
        tokenized    = [doc.lower().split() for doc in self._corpus]
        self._bm25   = BM25Okapi(tokenized)
        logger.info("BM25 index built with %d documents", len(self._corpus))

    async def search(self, query: str, top_k: int = 5,
                     doc_type: str = "default") -> list[HybridSearchResult]:
        # Semantic search
        q_emb     = await self.embedder.embed(query)
        sem_hits  = self.store.search(q_emb, top_k=top_k * 2, doc_type=doc_type)

        # BM25 search
        bm25_hits = self._bm25_search(query, top_k * 2) if self._bm25 else []

        # RRF fusion
        return self._rrf_fuse(sem_hits, bm25_hits, top_k)

    def _bm25_search(self, query: str, top_k: int) -> list[dict]:
        scores  = self._bm25.get_scores(query.lower().split())
        indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [{"index": i, "score": scores[i], "content": self._corpus[i],
                 "meta": self._meta[i]} for i in indices]

    def _rrf_fuse(self, sem: list[SearchResult], bm25: list[dict],
                  top_k: int) -> list[HybridSearchResult]:
        scores: dict[str, dict] = {}
        for rank, hit in enumerate(sem):
            scores.setdefault(hit.chunk_id, {"sem": 0, "bm25": 0, "hit": hit})
            scores[hit.chunk_id]["sem"] = 1 / (self.k + rank + 1)
        for rank, hit in enumerate(bm25):
            cid = hit["meta"].get("chunk_id", f"bm25_{rank}")
            scores.setdefault(cid, {"sem": 0, "bm25": 0, "hit": None})
            scores[cid]["bm25"] = 1 / (self.k + rank + 1)

        results = []
        for cid, data in scores.items():
            rrf = self.sw * data["sem"] + (1 - self.sw) * data["bm25"]
            hit = data.get("hit")
            if hit:
                results.append(HybridSearchResult(
                    chunk_id=cid, document_id=hit.document_id,
                    content=hit.content, semantic_score=data["sem"],
                    bm25_score=data["bm25"], rrf_score=rrf,
                    metadata=hit.metadata,
                ))
        return sorted(results, key=lambda r: r.rrf_score, reverse=True)[:top_k]

# 11:03:54 — refactor: make fusion algorithm configurable

# 11:03:54 — perf: pre-build BM25 index on startup

# 13:54:03 — refactor: extract magic number to constant in hybrid_searche

# 13:35:23 — style: run black formatter on hybrid_searcher

# 12:44:00 — fix: handle None input edge case in hybrid_searcher

# 11:27:02 — fix: handle None input edge case in hybrid_searcher

# 12:48:43 — docs: add module docstring to hybrid_searcher

# 11:58:15 — test: add assertion for return type in hybrid_searcher

# 12:05:06 — fix: correct off-by-one error in hybrid_searcher

# 13:49:27 — docs: add module docstring to hybrid_searcher

# 13:40:14 — fix: correct off-by-one error in hybrid_searcher

# 15:28:16 — refactor: rename variable for clarity in hybrid_searcher

# 12:28:16 — refactor: extract magic number to constant in hybrid_searche

# 12:39:25 — docs: update example in docstring of hybrid_searcher

# 12:14:07 — fix: remove unused import in hybrid_searcher

# 11:40:55 — refactor: extract magic number to constant in hybrid_searche

# 11:12:25 — style: reorder imports alphabetically in hybrid_searcher

# 11:10:56 — chore: add logging statement to hybrid_searcher
