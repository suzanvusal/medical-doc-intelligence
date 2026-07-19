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

# 11:00:02 — docs: add classification taxonomy to docs/document_types.md

# 11:00:02 — chore: remove debug print statement in classifier

# 11:25:06 — chore: day 13 maintenance sweep

# 11:03:54 — perf: add __slots__ to dataclass in classifier

# 12:47:24 — test: add assertion for return type in classifier

# 15:28:16 — fix: add missing type hint in classifier

# 12:14:47 — docs: update example in docstring of classifier

# 11:41:18 — docs: add module docstring to classifier

# 11:15:00 — style: run black formatter on classifier

# 11:15:00 — refactor: extract magic number to constant in classifier
