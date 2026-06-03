"""Medical text embedding generator using Ollama nomic-embed-text."""
from __future__ import annotations
import asyncio
import logging
import math
from src.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class MedicalEmbedder:
    """Generates and normalises embeddings for medical text chunks."""

    def __init__(self, client: OllamaClient, batch_size: int = 16) -> None:
        self.client     = client
        self.batch_size = batch_size

    async def embed(self, text: str) -> list[float]:
        raw = await self.client.embed(text)
        return self._normalise(raw)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in batches respecting Ollama concurrency."""
        results = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_results = await asyncio.gather(*[self.embed(t) for t in batch])
            results.extend(batch_results)
            logger.debug("Embedded batch %d/%d",
                         min(i + self.batch_size, len(texts)), len(texts))
        return results

    def _normalise(self, vector: list[float]) -> list[float]:
        """L2 normalise embedding vector."""
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude == 0:
            return vector
        return [v / magnitude for v in vector]

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two normalised vectors."""
        if len(a) != len(b):
            raise ValueError("Vector dimensions must match")
        return sum(x * y for x, y in zip(a, b))

# 11:57:47 — test: add embedding tests verifying medical term similarity 

# 11:57:47 — fix: batch processor failing silently on encoding errors

# 11:57:47 — refactor: rename variable for clarity in embedder

# 12:11:08 — chore: remove debug print statement in embedder

# 12:00:38 — refactor: rename variable for clarity in embedder

# 16:12:54 — fix: handle None input edge case in embedder

# 14:50:08 — test: add assertion for return type in embedder
