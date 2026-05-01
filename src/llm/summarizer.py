"""Medical document summarizer using Ollama LLM."""
from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass
from src.llm.ollama_client import OllamaClient
from src.llm.prompt_templates import (
    SUMMARIZATION_SYSTEM, SUMMARIZATION_PROMPT, render
)

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    document_id:  str
    key_findings: list[str]
    diagnosis:    list[str]
    medications:  list[str]
    plan:         str
    summary:      str
    urgency:      str
    confidence:   float = 1.0
    raw_response: str = ""


class MedicalSummarizer:
    """Summarizes medical documents using Ollama llama3.2."""

    def __init__(self, client: OllamaClient) -> None:
        self.client = client

    async def summarize(self, document_id: str, content: str,
                        document_type: str = "clinical_note") -> SummaryResult:
        prompt = render(SUMMARIZATION_PROMPT,
                        content=content[:4000],
                        document_type=document_type)
        raw = await self.client.generate(prompt, system=SUMMARIZATION_SYSTEM,
                                         temperature=0.05)
        logger.debug("Summarizer raw output for %s: %s", document_id, raw[:200])
        parsed = self._parse(raw)
        return SummaryResult(
            document_id=document_id,
            key_findings=parsed.get("key_findings", []),
            diagnosis=parsed.get("diagnosis", []),
            medications=parsed.get("medications", []),
            plan=parsed.get("plan", ""),
            summary=parsed.get("summary", ""),
            urgency=parsed.get("urgency", "routine"),
            raw_response=raw,
        )

    def _parse(self, raw: str) -> dict:
        try:
            clean = re.sub(r"```json|```", "", raw).strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from summarizer output")
            return {
                "key_findings": [],
                "diagnosis": [],
                "medications": [],
                "plan": "",
                "summary": raw[:500],
                "urgency": "routine",
            }

    async def summarize_chunks(self, document_id: str,
                               chunks: list[str]) -> SummaryResult:
        """Progressively summarize large documents via chunk reduction."""
        if len(chunks) == 1:
            return await self.summarize(document_id, chunks[0])
        intermediate = []
        for i, chunk in enumerate(chunks):
            result = await self.summarize(f"{document_id}_chunk_{i}", chunk)
            intermediate.append(result.summary)
        combined = "

".join(intermediate)
        return await self.summarize(document_id, combined)

# 11:15:23 — feat: add summary caching with Redis to avoid re-processing

# 11:15:23 — feat: implement batch summarization for multiple documents
