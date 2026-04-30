"""Async Ollama client for LLM inference and embedding generation."""
from __future__ import annotations
import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import AsyncGenerator
import httpx

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    base_url:      str   = "http://localhost:11434"
    llm_model:     str   = "llama3.2"
    embed_model:   str   = "nomic-embed-text"
    timeout:       float = 120.0
    keep_alive:    str   = "10m"
    max_retries:   int   = 3


class OllamaClient:
    """Async HTTP client for Ollama API with retry and streaming support."""

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig()
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )

    async def generate(self, prompt: str, system: str = "",
                       temperature: float = 0.1) -> str:
        """Generate a completion from the LLM."""
        payload = {
            "model":      self.config.llm_model,
            "prompt":     prompt,
            "system":     system,
            "stream":     False,
            "keep_alive": self.config.keep_alive,
            "options":    {"temperature": temperature},
        }
        for attempt in range(self.config.max_retries):
            try:
                resp = await self._client.post("/api/generate", json=payload)
                resp.raise_for_status()
                return resp.json()["response"].strip()
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                wait = 2 ** attempt
                logger.warning("Ollama attempt %d failed: %s — retrying in %ds",
                               attempt + 1, exc, wait)
                await asyncio.sleep(wait)
        raise RuntimeError(f"Ollama failed after {self.config.max_retries} retries")

    async def stream(self, prompt: str, system: str = "") -> AsyncGenerator[str, None]:
        """Stream tokens from the LLM."""
        payload = {"model": self.config.llm_model, "prompt": prompt,
                   "system": system, "stream": True}
        async with self._client.stream("POST", "/api/generate", json=payload) as resp:
            async for line in resp.aiter_lines():
                if line:
                    data = json.loads(line)
                    if token := data.get("response"):
                        yield token
                    if data.get("done"):
                        break

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for text."""
        resp = await self._client.post("/api/embeddings", json={
            "model": self.config.embed_model,
            "prompt": text,
        })
        resp.raise_for_status()
        return resp.json()["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return await asyncio.gather(*[self.embed(t) for t in texts])

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        resp = await self._client.get("/api/tags")
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]

    async def close(self) -> None:
        await self._client.aclose()

# 11:45:54 — feat: add medical summarization prompt template

# 11:45:42 — refactor: rename variable for clarity in ollama_client
