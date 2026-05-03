"""Zero-shot medical document classifier using Ollama."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from src.llm.ollama_client import OllamaClient
from src.ingestion.schemas import DocumentType

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """Classify the following medical document into exactly one of these categories:
discharge_summary, lab_report, radiology, prescription, clinical_note, pathology, unknown

Also rate the clinical urgency: routine, urgent, or critical.

Document excerpt:
{content}

Respond with JSON only:
{{"document_type": "...", "urgency": "...", "confidence": 0.0-1.0, "reason": "..."}}"""


@dataclass
class ClassificationResult:
    document_id:   str
    document_type: DocumentType
    urgency:       str
    confidence:    float
    reason:        str


class MedicalDocumentClassifier:
    """Classifies medical documents by type and urgency using Ollama."""

    def __init__(self, client: OllamaClient,
                 confidence_threshold: float = 0.6) -> None:
        self.client    = client
        self.threshold = confidence_threshold

    async def classify(self, document_id: str,
                       content: str) -> ClassificationResult:
        import json, re
        prompt = CLASSIFICATION_PROMPT.format(content=content[:1500])
        raw    = await self.client.generate(prompt, temperature=0.0)

        try:
            clean  = re.sub(r"```json|```", "", raw).strip()
            parsed = json.loads(clean)
            dtype  = DocumentType(parsed.get("document_type", "unknown"))
        except Exception:
            dtype  = DocumentType.UNKNOWN
            parsed = {"urgency": "routine", "confidence": 0.0, "reason": "parse error"}

        if parsed.get("confidence", 0) < self.threshold:
            dtype = DocumentType.UNKNOWN

        return ClassificationResult(
            document_id=document_id,
            document_type=dtype,
            urgency=parsed.get("urgency", "routine"),
            confidence=parsed.get("confidence", 0.0),
            reason=parsed.get("reason", ""),
        )

# 11:00:02 — fix: urgency scorer not detecting sepsis-related keywords
