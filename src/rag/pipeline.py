"""RAG pipeline: retrieval + context assembly + LLM generation."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from src.llm.ollama_client import OllamaClient
from src.llm.prompt_templates import RAG_SYSTEM, RAG_PROMPT, render
from src.vectorstore.chroma_store import MedicalChromaStore, SearchResult
from src.vectorstore.embedder import MedicalEmbedder

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    question:    str
    answer:      str
    sources:     list[SearchResult]
    confidence:  float
    latency_ms:  float
    citations:   list[str] = field(default_factory=list)


class MedicalRAGPipeline:
    """End-to-end RAG pipeline for medical document Q&A."""

    def __init__(self, client: OllamaClient, store: MedicalChromaStore,
                 embedder: MedicalEmbedder, top_k: int = 5) -> None:
        self.client   = client
        self.store    = store
        self.embedder = embedder
        self.top_k    = top_k

    async def query(self, question: str,
                    doc_type: str = "default",
                    patient_id: str | None = None) -> RAGResponse:
        import time
        t0 = time.perf_counter()

        # 1 — embed the question
        q_embedding = await self.embedder.embed(question)

        # 2 — retrieve relevant chunks
        filters = {"patient_id": patient_id} if patient_id else None
        results = self.store.search(q_embedding, top_k=self.top_k,
                                    doc_type=doc_type, filters=filters)

        if not results:
            return RAGResponse(
                question=question,
                answer="No relevant documents found for this query.",
                sources=[], confidence=0.0,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )

        # 3 — build context
        context = self._build_context(results)

        # 4 — generate answer
        prompt = render(RAG_PROMPT, context=context, question=question)
        answer = await self.client.generate(prompt, system=RAG_SYSTEM,
                                            temperature=0.05)

        # 5 — compute confidence from retrieval scores
        confidence = sum(r.score for r in results) / len(results)
        citations  = [f"[Doc {r.document_id}, p.{r.metadata.get('page_number','?')}]"
                      for r in results[:3]]

        return RAGResponse(
            question=question, answer=answer, sources=results,
            confidence=round(confidence, 3),
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            citations=citations,
        )

    def _build_context(self, results: list[SearchResult]) -> str:
        parts = []
        for i, r in enumerate(results, 1):
            parts.append(f"[Source {i} | Doc: {r.document_id} | Score: {r.score:.3f}]
{r.content}")
        return "

---

".join(parts)

# 11:56:36 — feat: add RAG response confidence scoring
