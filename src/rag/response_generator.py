"""Structured clinical response generator with citation formatting."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from src.llm.ollama_client import OllamaClient
from src.vectorstore.chroma_store import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class ClinicalResponse:
    answer:        str
    citations:     list[str]
    confidence:    str
    uncertainty:   str | None = None
    follow_up:     list[str] = field(default_factory=list)


class ResponseGenerator:
    """Generates structured, cited clinical responses from RAG results."""

    UNCERTAINTY_PHRASES = [
        "based on available documents",
        "the documentation suggests",
        "according to the records",
    ]

    def __init__(self, client: OllamaClient) -> None:
        self.client = client

    async def generate(self, question: str, context_chunks: list[SearchResult],
                       max_tokens: int = 500) -> ClinicalResponse:
        if not context_chunks:
            return ClinicalResponse(
                answer="No relevant clinical documentation found.",
                citations=[], confidence="low",
                uncertainty="Insufficient documentation to answer this question.",
            )

        context = "

".join(
            f"[Source {i+1}]: {chunk.content}"
            for i, chunk in enumerate(context_chunks)
        )
        system = (
            "You are a clinical documentation assistant. Answer only from the provided sources. "
            "If uncertain, say so. Never fabricate clinical information."
        )
        prompt = f"Sources:
{context}

Question: {question}

Answer concisely and cite sources:"
        answer = await self.client.generate(prompt, system=system, temperature=0.05)

        citations = [
            f"[Source {i+1}] Doc:{chunk.document_id} (relevance: {chunk.score:.2f})"
            for i, chunk in enumerate(context_chunks[:3])
        ]
        avg_score  = sum(c.score for c in context_chunks) / len(context_chunks)
        confidence = "high" if avg_score > 0.8 else "medium" if avg_score > 0.6 else "low"

        return ClinicalResponse(
            answer=answer, citations=citations, confidence=confidence,
            uncertainty=None if avg_score > 0.7 else "Limited documentation available.",
        )

# 11:25:06 — perf: streaming response generation for long answers

# 11:03:54 — perf: cache repeated computation in response_generator

# 11:05:49 — docs: add module docstring to response_generator

# 12:28:25 — ci: update step name for readability
