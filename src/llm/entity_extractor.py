"""Clinical entity extractor: diagnoses, medications, procedures, labs."""
from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass, field
from src.llm.ollama_client import OllamaClient
from src.llm.prompt_templates import ENTITY_EXTRACTION_PROMPT, render

logger = logging.getLogger(__name__)


@dataclass
class ClinicalEntity:
    entity_type: str
    value:       str
    confidence:  float = 1.0
    metadata:    dict  = field(default_factory=dict)


@dataclass
class EntityExtractionResult:
    document_id: str
    diagnoses:   list[ClinicalEntity]
    medications: list[ClinicalEntity]
    procedures:  list[ClinicalEntity]
    lab_values:  list[ClinicalEntity]
    vital_signs: list[ClinicalEntity]

    @property
    def all_entities(self) -> list[ClinicalEntity]:
        return (self.diagnoses + self.medications + self.procedures +
                self.lab_values + self.vital_signs)

    @property
    def entity_count(self) -> int:
        return len(self.all_entities)


class ClinicalEntityExtractor:
    """Extracts structured clinical entities from medical text using Ollama."""

    def __init__(self, client: OllamaClient) -> None:
        self.client = client

    async def extract(self, document_id: str, content: str) -> EntityExtractionResult:
        prompt = render(ENTITY_EXTRACTION_PROMPT, content=content[:3000])
        raw    = await self.client.generate(prompt, temperature=0.0)
        parsed = self._parse(raw)

        return EntityExtractionResult(
            document_id=document_id,
            diagnoses=[ClinicalEntity("DIAGNOSIS", d["term"],
                       metadata={"icd10_hint": d.get("icd10_hint","")})
                       for d in parsed.get("diagnoses", [])],
            medications=[ClinicalEntity("MEDICATION", m["name"],
                         metadata={"dose": m.get("dose",""), "route": m.get("route","")})
                         for m in parsed.get("medications", [])],
            procedures=[ClinicalEntity("PROCEDURE", p["name"],
                        metadata={"date": p.get("date","")})
                        for p in parsed.get("procedures", [])],
            lab_values=[ClinicalEntity("LAB_VALUE", l["test"],
                        metadata={"value": l.get("value",""), "unit": l.get("unit",""),
                                  "flag": l.get("flag","normal")})
                        for l in parsed.get("lab_values", [])],
            vital_signs=[ClinicalEntity("VITAL_SIGN", v["type"],
                         metadata={"value": v.get("value",""), "unit": v.get("unit","")})
                         for v in parsed.get("vital_signs", [])],
        )

    def _parse(self, raw: str) -> dict:
        try:
            clean = re.sub(r"```json|```", "", raw).strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            logger.warning("Entity extraction JSON parse failed")
            return {}
