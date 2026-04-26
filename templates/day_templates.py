"""
templates/day_templates.py
===========================
30 days of real, production-quality code for the
Medical Document Intelligence Pipeline.
"""

DAY_FILES: dict[int, dict[str, str]] = {

# ═══════════════════════════════════════════════════════
# DAY 1 — Bootstrap
# ═══════════════════════════════════════════════════════
1: {
"src/__init__.py": '"""Medical Document Intelligence Pipeline v0.1.0."""\n__version__ = "0.1.0"\n',
"src/ingestion/__init__.py": '"""PDF ingestion, OCR, chunking, document schemas."""\n',
"src/llm/__init__.py": '"""Ollama LLM client, summarizer, entity extractor."""\n',
"src/vectorstore/__init__.py": '"""ChromaDB vector store, embeddings, search."""\n',
"src/rag/__init__.py": '"""RAG pipeline: retrieval, context, generation."""\n',
"src/monitoring/__init__.py": '"""Quality monitor, hallucination detector, drift."""\n',
"src/api/__init__.py": '"""FastAPI REST interface for document intelligence."""\n',
},

# ═══════════════════════════════════════════════════════
# DAY 2 — Document schemas & PDF processor
# ═══════════════════════════════════════════════════════
2: {
"src/ingestion/schemas.py": '''\
"""Pydantic schemas for medical document ingestion pipeline."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    DISCHARGE_SUMMARY = "discharge_summary"
    LAB_REPORT        = "lab_report"
    RADIOLOGY         = "radiology"
    PRESCRIPTION      = "prescription"
    CLINICAL_NOTE     = "clinical_note"
    PATHOLOGY         = "pathology"
    UNKNOWN           = "unknown"


class DocumentStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"


class MedicalDocument(BaseModel):
    """Core medical document schema."""
    document_id:   str
    patient_id:    Optional[str] = None
    document_type: DocumentType = DocumentType.UNKNOWN
    title:         Optional[str] = None
    date:          Optional[datetime] = None
    source_path:   str
    page_count:    int = Field(ge=1)
    status:        DocumentStatus = DocumentStatus.PENDING
    created_at:    datetime = Field(default_factory=datetime.utcnow)
    metadata:      dict = Field(default_factory=dict)

    @field_validator("patient_id")
    @classmethod
    def anonymise_patient_id(cls, v: Optional[str]) -> Optional[str]:
        """Ensure patient_id is in expected format."""
        if v and not v.startswith("PAT-"):
            return f"PAT-{v}"
        return v


class DocumentChunk(BaseModel):
    """A text chunk extracted from a medical document."""
    chunk_id:     str
    document_id:  str
    content:      str = Field(min_length=1)
    page_number:  int = Field(ge=1)
    chunk_index:  int = Field(ge=0)
    section:      Optional[str] = None
    token_count:  int = 0
    embedding_id: Optional[str] = None

    @property
    def is_embedded(self) -> bool:
        return self.embedding_id is not None


class ExtractionResult(BaseModel):
    """Result of document text extraction."""
    document_id: str
    raw_text:    str
    chunks:      list[DocumentChunk]
    page_count:  int
    ocr_used:    bool = False
    language:    str = "en"
    extraction_time_ms: float = 0.0
''',

"src/ingestion/pdf_processor.py": '''\
"""PDF text extraction with OCR fallback for scanned medical documents."""
from __future__ import annotations
import io
import logging
import time
import uuid
from pathlib import Path
from typing import Optional
from src.ingestion.schemas import DocumentChunk, ExtractionResult

logger = logging.getLogger(__name__)

# Minimum characters per page before triggering OCR
OCR_THRESHOLD = 50


class PDFProcessor:
    """Extracts text from medical PDFs using PyMuPDF with Tesseract OCR fallback."""

    def __init__(self, ocr_enabled: bool = True, language: str = "eng") -> None:
        self.ocr_enabled = ocr_enabled
        self.language    = language

    def extract(self, pdf_path: str, document_id: str) -> ExtractionResult:
        """Extract text from PDF, falling back to OCR for scanned pages."""
        import fitz  # PyMuPDF
        t0   = time.perf_counter()
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc       = fitz.open(str(path))
        pages     = []
        ocr_used  = False

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if len(text) < OCR_THRESHOLD and self.ocr_enabled:
                text     = self._ocr_page(page)
                ocr_used = True

            pages.append((page_num + 1, text))

        doc.close()
        raw_text = "\n\n".join(f"[Page {p}]\n{t}" for p, t in pages if t)
        chunks   = self._make_chunks(pages, document_id)
        elapsed  = (time.perf_counter() - t0) * 1000

        logger.info("Extracted %d pages from %s (ocr=%s) in %.0fms",
                    len(pages), path.name, ocr_used, elapsed)
        return ExtractionResult(
            document_id=document_id,
            raw_text=raw_text,
            chunks=chunks,
            page_count=len(pages),
            ocr_used=ocr_used,
            extraction_time_ms=round(elapsed, 2),
        )

    def _ocr_page(self, page) -> str:
        """Rasterize page and run Tesseract OCR."""
        try:
            import pytesseract
            from PIL import Image
            pix   = page.get_pixmap(dpi=300)
            img   = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return pytesseract.image_to_string(img, lang=self.language)
        except Exception as exc:
            logger.warning("OCR failed on page: %s", exc)
            return ""

    def _make_chunks(self, pages: list[tuple[int, str]],
                     document_id: str) -> list[DocumentChunk]:
        chunks = []
        idx = 0
        for page_num, text in pages:
            if not text.strip():
                continue
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            for para in paragraphs:
                chunks.append(DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=para,
                    page_number=page_num,
                    chunk_index=idx,
                    token_count=len(para.split()),
                ))
                idx += 1
        return chunks
''',

"tests/unit/test_schemas.py": '''\
"""Unit tests for medical document schemas."""
import uuid
from datetime import datetime
import pytest
from pydantic import ValidationError
from src.ingestion.schemas import (
    MedicalDocument, DocumentChunk, DocumentType, DocumentStatus
)


def make_doc(**kwargs) -> dict:
    base = dict(
        document_id=str(uuid.uuid4()),
        source_path="/data/report.pdf",
        page_count=5,
    )
    base.update(kwargs)
    return base


def test_valid_medical_document():
    doc = MedicalDocument(**make_doc())
    assert doc.status == DocumentStatus.PENDING
    assert doc.document_type == DocumentType.UNKNOWN


def test_patient_id_prefixed():
    doc = MedicalDocument(**make_doc(patient_id="12345"))
    assert doc.patient_id == "PAT-12345"


def test_patient_id_already_prefixed():
    doc = MedicalDocument(**make_doc(patient_id="PAT-12345"))
    assert doc.patient_id == "PAT-12345"


def test_page_count_must_be_positive():
    with pytest.raises(ValidationError):
        MedicalDocument(**make_doc(page_count=0))


def test_document_chunk_is_embedded_false():
    chunk = DocumentChunk(
        chunk_id=str(uuid.uuid4()),
        document_id="doc-1",
        content="Patient presents with chest pain.",
        page_number=1,
        chunk_index=0,
    )
    assert not chunk.is_embedded


def test_document_chunk_is_embedded_true():
    chunk = DocumentChunk(
        chunk_id=str(uuid.uuid4()),
        document_id="doc-1",
        content="Patient presents with chest pain.",
        page_number=1,
        chunk_index=0,
        embedding_id="emb-abc123",
    )
    assert chunk.is_embedded


def test_chunk_content_cannot_be_empty():
    with pytest.raises(ValidationError):
        DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            document_id="doc-1",
            content="",
            page_number=1,
            chunk_index=0,
        )
''',
},

# ═══════════════════════════════════════════════════════
# DAY 3 — Chunker & preprocessor
# ═══════════════════════════════════════════════════════
3: {
"src/ingestion/chunker.py": '''\
"""Smart text chunker for medical documents preserving clinical context."""
from __future__ import annotations
import re
import uuid
from dataclasses import dataclass
from src.ingestion.schemas import DocumentChunk

MEDICAL_SECTIONS = [
    "chief complaint", "history of present illness", "past medical history",
    "medications", "allergies", "physical examination", "assessment",
    "plan", "diagnosis", "discharge instructions", "lab results",
    "radiology findings", "impression", "recommendation",
]


@dataclass
class ChunkConfig:
    chunk_size:    int = 512
    chunk_overlap: int = 64
    min_chunk_size:int = 50


class MedicalTextChunker:
    """Sentence-aware chunker that preserves medical section boundaries."""

    def __init__(self, config: ChunkConfig | None = None) -> None:
        self.config = config or ChunkConfig()

    def chunk(self, text: str, document_id: str) -> list[DocumentChunk]:
        sections  = self._split_sections(text)
        chunks: list[DocumentChunk] = []
        idx = 0

        for section_name, section_text in sections:
            for chunk_text in self._split_text(section_text):
                if len(chunk_text) < self.config.min_chunk_size:
                    continue
                chunks.append(DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=chunk_text,
                    page_number=1,
                    chunk_index=idx,
                    section=section_name,
                    token_count=len(chunk_text.split()),
                ))
                idx += 1
        return chunks

    def _split_sections(self, text: str) -> list[tuple[str | None, str]]:
        """Split text by clinical section headers."""
        pattern = "|".join(re.escape(s) for s in MEDICAL_SECTIONS)
        regex   = re.compile(f"(?i)({pattern})\\s*[:\\n]")
        parts   = regex.split(text)
        if len(parts) == 1:
            return [(None, text)]
        sections = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and regex.match(parts[i] + ":"):
                sections.append((parts[i].lower(), parts[i+1]))
                i += 2
            else:
                sections.append((None, parts[i]))
                i += 1
        return sections

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks respecting sentence boundaries."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks, current, current_len = [], [], 0

        for sent in sentences:
            sent_len = len(sent.split())
            if current_len + sent_len > self.config.chunk_size and current:
                chunks.append(" ".join(current))
                overlap = current[-2:] if len(current) >= 2 else current
                current, current_len = overlap[:], sum(len(s.split()) for s in overlap)
            current.append(sent)
            current_len += sent_len

        if current:
            chunks.append(" ".join(current))
        return chunks
''',

"src/ingestion/preprocessor.py": '''\
"""Medical text preprocessor: PII anonymization, abbreviation expansion."""
from __future__ import annotations
import re

# Common medical abbreviations
ABBREVIATIONS = {
    "BP": "blood pressure", "HR": "heart rate", "RR": "respiratory rate",
    "T": "temperature", "SpO2": "oxygen saturation", "ECG": "electrocardiogram",
    "CBC": "complete blood count", "BMP": "basic metabolic panel",
    "CT": "computed tomography", "MRI": "magnetic resonance imaging",
    "PRN": "as needed", "QID": "four times daily", "TID": "three times daily",
    "BID": "twice daily", "QD": "once daily", "NPO": "nothing by mouth",
    "SOB": "shortness of breath", "CP": "chest pain", "HA": "headache",
    "HTN": "hypertension", "DM": "diabetes mellitus", "CAD": "coronary artery disease",
    "CHF": "congestive heart failure", "COPD": "chronic obstructive pulmonary disease",
    "UTI": "urinary tract infection", "URI": "upper respiratory infection",
}

PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b",   "[SSN]"),
    (r"\b\d{10}\b",               "[PHONE]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
    (r"\b\d{1,5}\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr)\b", "[ADDRESS]"),
    (r"\bDOB:\s*\d{1,2}/\d{1,2}/\d{2,4}\b", "DOB: [DATE]"),
]


class MedicalPreprocessor:
    """Cleans and normalises medical text before LLM processing."""

    def __init__(self, expand_abbreviations: bool = True,
                 anonymize_pii: bool = True) -> None:
        self.expand_abbr = expand_abbreviations
        self.anonymize   = anonymize_pii

    def process(self, text: str) -> str:
        text = self._normalise_whitespace(text)
        if self.anonymize:
            text = self._anonymize_pii(text)
        if self.expand_abbr:
            text = self._expand_abbreviations(text)
        return text.strip()

    def _normalise_whitespace(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text

    def _anonymize_pii(self, text: str) -> str:
        for pattern, replacement in PII_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def _expand_abbreviations(self, text: str) -> str:
        for abbr, expansion in ABBREVIATIONS.items():
            pattern = r"\b" + re.escape(abbr) + r"\b"
            text = re.sub(pattern, f"{abbr} ({expansion})", text, count=1)
        return text
''',
},

# ═══════════════════════════════════════════════════════
# DAY 4 — Ollama client
# ═══════════════════════════════════════════════════════
4: {
"src/llm/ollama_client.py": '''\
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
''',

"src/llm/prompt_templates.py": '''\
"""Jinja2 prompt templates for medical document processing."""
from __future__ import annotations
from jinja2 import Environment, BaseLoader

_env = Environment(loader=BaseLoader())

# ── Summarization ──────────────────────────────────────────
SUMMARIZATION_SYSTEM = """\
You are a clinical documentation specialist. Your task is to produce accurate,
concise summaries of medical documents. Always base your summary strictly on
the provided text. Never add information not present in the source document.
Output valid JSON only."""

SUMMARIZATION_PROMPT = """\
Summarize the following medical document.

Document Type: {{ document_type }}
Content:
{{ content }}

Respond with a JSON object containing:
{
  "key_findings": ["list of main clinical findings"],
  "diagnosis": ["list of diagnoses mentioned"],
  "medications": ["list of medications"],
  "plan": "brief treatment plan",
  "summary": "2-3 sentence overall summary",
  "urgency": "routine|urgent|critical"
}"""

# ── Entity Extraction ──────────────────────────────────────
ENTITY_EXTRACTION_PROMPT = """\
Extract all clinical entities from the following medical text.

Text:
{{ content }}

Respond with a JSON object:
{
  "diagnoses": [{"term": "...", "icd10_hint": "..."}],
  "medications": [{"name": "...", "dose": "...", "route": "..."}],
  "procedures": [{"name": "...", "date": "..."}],
  "lab_values": [{"test": "...", "value": "...", "unit": "...", "flag": "normal|high|low"}],
  "vital_signs": [{"type": "...", "value": "...", "unit": "..."}]
}"""

# ── RAG Answer Generation ──────────────────────────────────
RAG_SYSTEM = """\
You are a clinical information assistant. Answer questions about medical documents
using ONLY the provided context. If the answer is not in the context, say so clearly.
Never fabricate clinical information."""

RAG_PROMPT = """\
Context from medical documents:
{{ context }}

Question: {{ question }}

Provide a precise, evidence-based answer citing the relevant context.
If uncertain, express that uncertainty explicitly."""


def render(template_str: str, **kwargs) -> str:
    return _env.from_string(template_str).render(**kwargs)
''',
},

# ═══════════════════════════════════════════════════════
# DAY 5 — CI/CD
# ═══════════════════════════════════════════════════════
5: {
".github/workflows/ci.yml": '''\
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install dependencies
        run: pip install -e ".[dev]" --quiet

      - name: Lint
        run: ruff check src/ tests/

      - name: Type check
        run: mypy src/ --ignore-missing-imports

      - name: Test
        run: pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Security scan
        run: |
          pip install bandit pip-audit --quiet
          bandit -r src/ -ll -q || true
          pip-audit || true

  docker-build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == '"'"'refs/heads/main'"'"'
    steps:
      - uses: actions/checkout@v4
      - name: Build API image
        run: docker build -f infra/docker/Dockerfile.api -t medical-doc-api:latest . || true
''',
},

# ═══════════════════════════════════════════════════════
# DAY 6 — Summarizer
# ═══════════════════════════════════════════════════════
6: {
"src/llm/summarizer.py": '''\
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
        combined = "\n\n".join(intermediate)
        return await self.summarize(document_id, combined)
''',
},

# ═══════════════════════════════════════════════════════
# DAY 7 — Entity extractor
# ═══════════════════════════════════════════════════════
7: {
"src/llm/entity_extractor.py": '''\
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
''',
},

# ═══════════════════════════════════════════════════════
# DAY 8 — Classifier
# ═══════════════════════════════════════════════════════
8: {
"src/llm/classifier.py": '''\
"""Zero-shot medical document classifier using Ollama."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from src.llm.ollama_client import OllamaClient
from src.ingestion.schemas import DocumentType

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """\
Classify the following medical document into exactly one of these categories:
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
''',
},

# ═══════════════════════════════════════════════════════
# DAY 9 — Embedder
# ═══════════════════════════════════════════════════════
9: {
"src/vectorstore/embedder.py": '''\
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
''',
},

# ═══════════════════════════════════════════════════════
# DAY 10 — ChromaDB store
# ═══════════════════════════════════════════════════════
10: {
"src/vectorstore/chroma_store.py": '''\
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
''',
},

# ═══════════════════════════════════════════════════════
# DAY 11 — RAG Pipeline
# ═══════════════════════════════════════════════════════
11: {
"src/rag/pipeline.py": '''\
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
            parts.append(f"[Source {i} | Doc: {r.document_id} | Score: {r.score:.3f}]\n{r.content}")
        return "\n\n---\n\n".join(parts)
''',
},

# ═══════════════════════════════════════════════════════
# DAY 12-16 — abbreviated key files
# ═══════════════════════════════════════════════════════
12: {
"src/rag/query_understanding.py": '''\
"""Medical query parser and intent detector."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re


class QueryIntent(str, Enum):
    DIAGNOSIS_LOOKUP   = "diagnosis_lookup"
    MEDICATION_CHECK   = "medication_check"
    LAB_RESULT_LOOKUP  = "lab_result_lookup"
    SUMMARY_REQUEST    = "summary_request"
    PROCEDURE_LOOKUP   = "procedure_lookup"
    GENERAL_QUESTION   = "general_question"


INTENT_PATTERNS = {
    QueryIntent.DIAGNOSIS_LOOKUP:  [r"diagnos", r"condition", r"disorder", r"disease"],
    QueryIntent.MEDICATION_CHECK:  [r"medication", r"drug", r"prescri", r"dose", r"mg"],
    QueryIntent.LAB_RESULT_LOOKUP: [r"lab", r"blood test", r"result", r"level", r"value"],
    QueryIntent.SUMMARY_REQUEST:   [r"summar", r"overview", r"brief", r"main points"],
    QueryIntent.PROCEDURE_LOOKUP:  [r"procedure", r"surgery", r"operation", r"treatment"],
}

MEDICAL_ABBREVIATION_MAP = {
    "MI": "myocardial infarction", "CVA": "cerebrovascular accident",
    "DM": "diabetes mellitus", "HTN": "hypertension",
    "CHF": "congestive heart failure", "COPD": "chronic obstructive pulmonary disease",
}


@dataclass
class ParsedQuery:
    original:    str
    rewritten:   str
    intent:      QueryIntent
    keywords:    list[str]
    temporal:    str | None = None


class MedicalQueryParser:
    def parse(self, query: str) -> ParsedQuery:
        rewritten = self._expand_abbreviations(query)
        intent    = self._detect_intent(rewritten)
        keywords  = self._extract_keywords(rewritten)
        temporal  = self._extract_temporal(rewritten)
        return ParsedQuery(original=query, rewritten=rewritten,
                          intent=intent, keywords=keywords, temporal=temporal)

    def _expand_abbreviations(self, text: str) -> str:
        for abbr, expansion in MEDICAL_ABBREVIATION_MAP.items():
            text = re.sub(r"\b" + abbr + r"\b", expansion, text, flags=re.IGNORECASE)
        return text

    def _detect_intent(self, text: str) -> QueryIntent:
        text_lower = text.lower()
        for intent, patterns in INTENT_PATTERNS.items():
            if any(re.search(p, text_lower) for p in patterns):
                return intent
        return QueryIntent.GENERAL_QUESTION

    def _extract_keywords(self, text: str) -> list[str]:
        stop = {"what","is","the","a","an","of","for","in","on","at","to","and","or"}
        return [w for w in re.findall(r"\b\w{3,}\b", text.lower()) if w not in stop][:10]

    def _extract_temporal(self, text: str) -> str | None:
        patterns = [r"last \d+ (days?|weeks?|months?)", r"past \d+ (days?|weeks?|months?)",
                    r"since \w+", r"between .+ and .+"]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group()
        return None
''',
},

13: {
"src/rag/response_generator.py": '''\
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

        context = "\n\n".join(
            f"[Source {i+1}]: {chunk.content}"
            for i, chunk in enumerate(context_chunks)
        )
        system = (
            "You are a clinical documentation assistant. Answer only from the provided sources. "
            "If uncertain, say so. Never fabricate clinical information."
        )
        prompt = f"Sources:\n{context}\n\nQuestion: {question}\n\nAnswer concisely and cite sources:"
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
''',
},

14: {
"src/rag/hybrid_searcher.py": '''\
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
''',
},

15: {
"src/rag/session_manager.py": '''\
"""Multi-turn Q&A session manager with Redis persistence."""
from __future__ import annotations
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
import redis

logger = logging.getLogger(__name__)
_KEY = "session:{session_id}"


@dataclass
class ConversationTurn:
    question: str
    answer:   str
    sources:  list[str]
    timestamp:str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Session:
    session_id:  str
    patient_id:  str | None
    doc_type:    str
    history:     list[ConversationTurn] = field(default_factory=list)
    created_at:  str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_turn(self, question: str, answer: str, sources: list[str]) -> None:
        self.history.append(ConversationTurn(question, answer, sources))
        if len(self.history) > 10:      # Keep last 10 turns
            self.history = self.history[-10:]

    def context_summary(self) -> str:
        """Return recent conversation as context string."""
        if not self.history:
            return ""
        recent = self.history[-3:]
        return "\n".join(f"Q: {t.question}\nA: {t.answer}" for t in recent)


class SessionManager:
    def __init__(self, redis_url: str = "redis://localhost:6379",
                 ttl_seconds: int = 3600) -> None:
        self._r   = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds

    def create(self, patient_id: str | None = None,
               doc_type: str = "default") -> Session:
        session = Session(session_id=str(uuid.uuid4()),
                          patient_id=patient_id, doc_type=doc_type)
        self._save(session)
        return session

    def get(self, session_id: str) -> Session | None:
        raw = self._r.get(_KEY.format(session_id=session_id))
        if raw is None:
            return None
        data = json.loads(raw)
        data["history"] = [ConversationTurn(**t) for t in data.get("history", [])]
        return Session(**data)

    def update(self, session: Session) -> None:
        self._save(session)

    def _save(self, session: Session) -> None:
        data = {
            "session_id": session.session_id,
            "patient_id": session.patient_id,
            "doc_type":   session.doc_type,
            "created_at": session.created_at,
            "history": [
                {"question": t.question, "answer": t.answer,
                 "sources": t.sources, "timestamp": t.timestamp}
                for t in session.history
            ],
        }
        self._r.setex(_KEY.format(session_id=session.session_id),
                      self._ttl, json.dumps(data))
''',
},

# ═══════════════════════════════════════════════════════
# DAY 16 — FastAPI
# ═══════════════════════════════════════════════════════
16: {
"src/api/main.py": '''\
"""FastAPI application for Medical Document Intelligence Pipeline."""
from __future__ import annotations
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel
from src.llm.ollama_client import OllamaClient, OllamaConfig
from src.vectorstore.chroma_store import MedicalChromaStore
from src.vectorstore.embedder import MedicalEmbedder
from src.rag.pipeline import MedicalRAGPipeline

logger = logging.getLogger(__name__)

# Global state
_ollama: OllamaClient | None = None
_store:  MedicalChromaStore | None = None
_rag:    MedicalRAGPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ollama, _store, _rag
    config  = OllamaConfig(base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    _ollama = OllamaClient(config)
    _store  = MedicalChromaStore(
        host=os.getenv("CHROMADB_HOST", "localhost"),
        port=int(os.getenv("CHROMADB_PORT", "8001")),
    )
    embedder = MedicalEmbedder(_ollama)
    _rag     = MedicalRAGPipeline(_ollama, _store, embedder)
    logger.info("Medical Doc Intelligence API started")
    yield
    if _ollama:
        await _ollama.close()


app = FastAPI(
    title="Medical Document Intelligence API",
    description="LLM-powered medical document Q&A with RAG and hallucination detection",
    version="1.0.0",
    lifespan=lifespan,
)


class QueryRequest(BaseModel):
    question:   str
    patient_id: str | None = None
    doc_type:   str = "default"
    session_id: str | None = None


class QueryResponse(BaseModel):
    question:   str
    answer:     str
    citations:  list[str]
    confidence: float
    latency_ms: float


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    if _rag is None:
        raise HTTPException(503, "RAG pipeline not initialised")
    result = await _rag.query(req.question, req.doc_type, req.patient_id)
    return QueryResponse(
        question=req.question, answer=result.answer,
        citations=result.citations, confidence=result.confidence,
        latency_ms=result.latency_ms,
    )


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    content = await file.read()
    # In production: save to storage and queue processing task
    return {"message": "Document queued for processing", "filename": file.filename,
            "size_bytes": len(content)}


@app.get("/health")
async def health():
    ollama_ok = await _ollama.health_check() if _ollama else False
    return {"status": "ok" if ollama_ok else "degraded",
            "ollama": ollama_ok, "rag": _rag is not None}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
''',
},

# ═══════════════════════════════════════════════════════
# DAY 17-20 — Monitoring & hallucination detection
# ═══════════════════════════════════════════════════════
17: {
"src/monitoring/metrics.py": '''\
"""Prometheus metrics for Medical Document Intelligence Pipeline."""
from prometheus_client import Counter, Histogram, Gauge

DOCS_PROCESSED = Counter(
    "medai_documents_processed_total",
    "Total documents processed", ["doc_type", "status"]
)
LLM_LATENCY = Histogram(
    "medai_llm_inference_seconds",
    "LLM inference latency",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    labelnames=["operation"]
)
RAG_QUERIES = Counter(
    "medai_rag_queries_total",
    "Total RAG queries", ["intent", "status"]
)
EMBEDDING_LATENCY = Histogram(
    "medai_embedding_seconds",
    "Embedding generation latency",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0]
)
CHROMA_COLLECTION_SIZE = Gauge(
    "medai_chroma_collection_size",
    "ChromaDB collection document count", ["collection"]
)
HALLUCINATION_RATE = Gauge(
    "medai_hallucination_rate",
    "Rolling hallucination detection rate (last 100 responses)"
)
QUALITY_SCORE = Gauge(
    "medai_response_quality_score",
    "Rolling average response quality score", ["metric"]
)
ACTIVE_SESSIONS = Gauge(
    "medai_active_sessions",
    "Number of active Q&A sessions"
)
''',
},

18: {
"src/monitoring/quality_monitor.py": '''\
"""LLM response quality monitor: faithfulness, ROUGE, BERTScore."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from rouge_score import rouge_scorer

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    faithfulness:   float   # 0-1: is answer grounded in sources?
    rouge_l:        float   # 0-1: lexical overlap with reference
    overall:        float   # weighted average
    passed:         bool
    details:        dict


class ResponseQualityMonitor:
    """Monitors LLM response quality using multiple metrics."""

    def __init__(self, faithfulness_threshold: float = 0.75,
                 rouge_threshold: float = 0.3) -> None:
        self.faith_threshold = faithfulness_threshold
        self.rouge_threshold = rouge_threshold
        self._scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)

    def score(self, answer: str, context_chunks: list[str],
              reference: str | None = None) -> QualityScore:
        faithfulness = self._faithfulness(answer, context_chunks)
        rouge_l      = self._rouge_l(answer, reference) if reference else 0.5
        overall      = 0.7 * faithfulness + 0.3 * rouge_l
        passed       = (faithfulness >= self.faith_threshold and
                        rouge_l >= self.rouge_threshold)

        score = QualityScore(
            faithfulness=round(faithfulness, 4),
            rouge_l=round(rouge_l, 4),
            overall=round(overall, 4),
            passed=passed,
            details={"faith_threshold": self.faith_threshold,
                     "rouge_threshold": self.rouge_threshold},
        )
        if not passed:
            logger.warning("Quality check failed: faith=%.3f rouge=%.3f",
                           faithfulness, rouge_l)
        return score

    def _faithfulness(self, answer: str, contexts: list[str]) -> float:
        """Simple token overlap faithfulness check."""
        if not contexts:
            return 0.0
        answer_tokens = set(answer.lower().split())
        context_text  = " ".join(contexts)
        context_tokens= set(context_text.lower().split())
        overlap = answer_tokens & context_tokens
        return len(overlap) / max(len(answer_tokens), 1)

    def _rouge_l(self, hypothesis: str, reference: str) -> float:
        scores = self._scorer.score(reference, hypothesis)
        return scores["rougeL"].fmeasure
''',
},

19: {
"src/monitoring/hallucination_detector.py": '''\
"""Hallucination detector using claim extraction and grounding verification."""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from src.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class HallucinationResult:
    is_hallucinated:  bool
    severity:         str   # none / minor / moderate / critical
    ungrounded_claims:list[str]
    grounding_score:  float
    details:          str


class HallucinationDetector:
    """Detects ungrounded claims in LLM responses using source verification."""

    SEVERITY_THRESHOLDS = {
        "none":     (0.85, 1.00),
        "minor":    (0.65, 0.85),
        "moderate": (0.40, 0.65),
        "critical": (0.00, 0.40),
    }

    def __init__(self, client: OllamaClient,
                 threshold: float = 0.75) -> None:
        self.client    = client
        self.threshold = threshold

    async def detect(self, answer: str,
                     source_chunks: list[str]) -> HallucinationResult:
        claims     = self._extract_claims(answer)
        grounded   = []
        ungrounded = []

        context = " ".join(source_chunks).lower()
        for claim in claims:
            if self._is_grounded(claim, context):
                grounded.append(claim)
            else:
                ungrounded.append(claim)

        score    = len(grounded) / max(len(claims), 1)
        severity = self._classify_severity(score)

        result = HallucinationResult(
            is_hallucinated=score < self.threshold,
            severity=severity,
            ungrounded_claims=ungrounded,
            grounding_score=round(score, 4),
            details=f"{len(grounded)}/{len(claims)} claims grounded",
        )
        if result.severity in ("moderate", "critical"):
            logger.error("HALLUCINATION %s | score=%.3f ungrounded=%s",
                         severity, score, ungrounded[:2])
        return result

    def _extract_claims(self, text: str) -> list[str]:
        sentences = re.split(r"[.!?]\s+", text)
        return [s.strip() for s in sentences if len(s.split()) > 4]

    def _is_grounded(self, claim: str, context: str) -> bool:
        claim_words = set(re.findall(r"\b\w{4,}\b", claim.lower()))
        stop = {"that","this","with","from","have","been","were","will","their"}
        key_words = claim_words - stop
        if not key_words:
            return True
        overlap = sum(1 for w in key_words if w in context)
        return (overlap / len(key_words)) > 0.5

    def _classify_severity(self, score: float) -> str:
        for severity, (low, high) in self.SEVERITY_THRESHOLDS.items():
            if low <= score < high:
                return severity
        return "critical"
''',
},

20: {
"src/monitoring/llm_drift_monitor.py": '''\
"""LLM output drift monitor: tracks quality degradation over time."""
from __future__ import annotations
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class QualityObservation:
    timestamp:       str
    faithfulness:    float
    hallucination:   float
    response_length: int
    latency_ms:      float


@dataclass
class DriftReport:
    window_size:       int
    avg_faithfulness:  float
    avg_hallucination: float
    faith_trend:       str   # stable / degrading / improving
    is_drifted:        bool
    alert_level:       str   # none / warning / critical


class LLMDriftMonitor:
    """Monitors LLM output quality drift using a sliding observation window."""

    def __init__(self, window_size: int = 100,
                 faith_drop_threshold: float = 0.10,
                 hall_rise_threshold: float = 0.15) -> None:
        self._window = deque(maxlen=window_size)
        self._baseline_faith: float | None = None
        self.faith_threshold = faith_drop_threshold
        self.hall_threshold  = hall_rise_threshold

    def record(self, faithfulness: float, hallucination_score: float,
               response_length: int, latency_ms: float) -> None:
        obs = QualityObservation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            faithfulness=faithfulness,
            hallucination=hallucination_score,
            response_length=response_length,
            latency_ms=latency_ms,
        )
        self._window.append(obs)
        if len(self._window) == 50 and self._baseline_faith is None:
            self._baseline_faith = self._avg_faithfulness()
            logger.info("Baseline faithfulness set: %.4f", self._baseline_faith)

    def report(self) -> DriftReport | None:
        if len(self._window) < 10:
            return None
        avg_faith = self._avg_faithfulness()
        avg_hall  = sum(o.hallucination for o in self._window) / len(self._window)

        faith_drop = (self._baseline_faith - avg_faith) if self._baseline_faith else 0
        trend      = ("degrading" if faith_drop > 0.05
                      else "improving" if faith_drop < -0.05 else "stable")
        is_drifted = faith_drop > self.faith_threshold or avg_hall > self.hall_threshold
        alert      = "critical" if is_drifted and faith_drop > 0.20 else \
                     "warning"  if is_drifted else "none"

        return DriftReport(
            window_size=len(self._window),
            avg_faithfulness=round(avg_faith, 4),
            avg_hallucination=round(avg_hall, 4),
            faith_trend=trend,
            is_drifted=is_drifted,
            alert_level=alert,
        )

    def _avg_faithfulness(self) -> float:
        return sum(o.faithfulness for o in self._window) / len(self._window)
''',
},

# ═══════════════════════════════════════════════════════
# DAY 21-30 — Tests, load, security, docs
# ═══════════════════════════════════════════════════════
21: {
"tests/unit/test_chunker.py": '''\
"""Unit tests for MedicalTextChunker."""
import pytest
from src.ingestion.chunker import MedicalTextChunker, ChunkConfig


@pytest.fixture
def chunker():
    return MedicalTextChunker(ChunkConfig(chunk_size=50, chunk_overlap=10, min_chunk_size=5))


def test_chunks_created(chunker):
    text = "Patient presents with chest pain. " * 20
    chunks = chunker.chunk(text, "doc-1")
    assert len(chunks) > 1

def test_chunk_document_id(chunker):
    chunks = chunker.chunk("Patient has fever. Temperature 38.5.", "doc-abc")
    assert all(c.document_id == "doc-abc" for c in chunks)

def test_chunk_index_sequential(chunker):
    text = "Sentence one. Sentence two. Sentence three. Sentence four." * 5
    chunks = chunker.chunk(text, "doc-1")
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))

def test_min_chunk_size_respected(chunker):
    chunks = chunker.chunk("Short text. " * 10, "doc-1")
    assert all(len(c.content) >= 5 for c in chunks)

def test_section_detection(chunker):
    text = "Chief Complaint:\nPatient reports chest pain.\n\nPlan:\nAdmit for observation."
    chunks = chunker.chunk(text, "doc-1")
    sections = [c.section for c in chunks if c.section]
    assert len(sections) > 0
''',
},

22: {
"tests/unit/test_quality_monitor.py": '''\
"""Unit tests for LLM response quality monitor."""
import pytest
from src.monitoring.quality_monitor import ResponseQualityMonitor


@pytest.fixture
def monitor():
    return ResponseQualityMonitor(faithfulness_threshold=0.5, rouge_threshold=0.2)


def test_high_faithfulness_on_grounded_answer(monitor):
    context = ["The patient has type 2 diabetes and hypertension."]
    answer  = "The patient has diabetes and hypertension."
    score   = monitor.score(answer, context)
    assert score.faithfulness > 0.5

def test_low_faithfulness_on_hallucinated_answer(monitor):
    context = ["Blood pressure is 120/80."]
    answer  = "Patient has severe pneumonia and requires ventilation."
    score   = monitor.score(answer, context)
    assert score.faithfulness < 0.4

def test_overall_score_is_weighted(monitor):
    context   = ["Patient has fever."]
    answer    = "Patient has fever."
    reference = "The patient is febrile."
    score     = monitor.score(answer, context, reference)
    assert 0.0 <= score.overall <= 1.0

def test_empty_context_returns_zero_faithfulness(monitor):
    score = monitor.score("Any answer", [])
    assert score.faithfulness == 0.0

def test_passed_true_when_above_thresholds(monitor):
    context = ["Patient has diabetes mellitus type 2 and is on metformin."]
    answer  = "Patient has diabetes and takes metformin."
    score   = monitor.score(answer, context)
    assert isinstance(score.passed, bool)
''',
},

23: {
"tests/integration/test_rag_pipeline.py": '''\
"""Integration tests for RAG pipeline with mock Ollama and ChromaDB."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.rag.pipeline import MedicalRAGPipeline
from src.vectorstore.chroma_store import SearchResult


@pytest.fixture
def mock_ollama():
    client = AsyncMock()
    client.embed.return_value = [0.1] * 768
    client.generate.return_value = "The patient has type 2 diabetes."
    return client


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.search.return_value = [
        SearchResult(
            chunk_id="chunk-1", document_id="doc-1",
            content="Patient diagnosed with type 2 diabetes mellitus.",
            score=0.92, metadata={"page_number": 1}
        )
    ]
    return store


@pytest.fixture
def mock_embedder(mock_ollama):
    from src.vectorstore.embedder import MedicalEmbedder
    return MedicalEmbedder(mock_ollama)


@pytest.mark.asyncio
async def test_rag_returns_answer(mock_ollama, mock_store, mock_embedder):
    pipeline = MedicalRAGPipeline(mock_ollama, mock_store, mock_embedder)
    result   = await pipeline.query("What is the patient diagnosis?")
    assert result.answer != ""
    assert len(result.sources) > 0


@pytest.mark.asyncio
async def test_rag_no_results_returns_not_found(mock_ollama, mock_embedder):
    store = MagicMock()
    store.search.return_value = []
    pipeline = MedicalRAGPipeline(mock_ollama, store, mock_embedder)
    result   = await pipeline.query("What is the patient diagnosis?")
    assert "No relevant" in result.answer
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_rag_includes_citations(mock_ollama, mock_store, mock_embedder):
    pipeline = MedicalRAGPipeline(mock_ollama, mock_store, mock_embedder)
    result   = await pipeline.query("What medications is the patient on?")
    assert len(result.citations) > 0
    assert "doc-1" in result.citations[0]
''',
},

24: {
"tests/load/locustfile.py": '''\
"""Locust load test for Medical Document Intelligence API."""
import random
from locust import HttpUser, between, task

CLINICAL_QUESTIONS = [
    "What is the patient's primary diagnosis?",
    "What medications is the patient currently taking?",
    "What were the lab results?",
    "What is the treatment plan?",
    "Are there any allergies documented?",
    "What were the vital signs on admission?",
    "What procedures were performed?",
    "What is the discharge summary?",
]


class MedicalDocUser(HttpUser):
    wait_time = between(1, 3)

    @task(10)
    def query_document(self):
        payload = {
            "question": random.choice(CLINICAL_QUESTIONS),
            "doc_type": "default",
            "patient_id": f"PAT-{random.randint(1,999):06d}",
        }
        with self.client.post("/query", json=payload, catch_response=True) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "answer" not in data:
                    resp.failure("Missing answer in response")
            elif resp.status_code == 503:
                resp.failure("RAG pipeline not ready")

    @task(3)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def metrics_check(self):
        self.client.get("/metrics")
''',
},

25: {
"src/security/audit_logger.py": '''\
"""HIPAA-compliant audit logger for all document access events."""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    event_type:  str
    user_id:     str
    document_id: str | None
    patient_id:  str | None
    action:      str
    ip_address:  str | None = None
    success:     bool = True
    details:     dict = field(default_factory=dict)
    timestamp:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditLogger:
    """Immutable append-only audit log for HIPAA compliance."""

    def __init__(self, log_path: str = "logs/audit.jsonl") -> None:
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: AuditEvent) -> None:
        record = {
            "timestamp":   event.timestamp,
            "event_type":  event.event_type,
            "user_id":     event.user_id,
            "document_id": event.document_id,
            "patient_id":  event.patient_id,
            "action":      event.action,
            "ip_address":  event.ip_address,
            "success":     event.success,
            "details":     event.details,
        }
        with open(self._path, "a") as f:
            f.write(json.dumps(record) + "\n")
        logger.info("AUDIT %s | user=%s doc=%s action=%s",
                    event.event_type, event.user_id,
                    event.document_id, event.action)

    def log_access(self, user_id: str, document_id: str,
                   patient_id: str | None = None, ip: str | None = None) -> None:
        self.log(AuditEvent("DOCUMENT_ACCESS", user_id, document_id,
                            patient_id, "READ", ip_address=ip))

    def log_query(self, user_id: str, question: str,
                  patient_id: str | None = None) -> None:
        self.log(AuditEvent("RAG_QUERY", user_id, None, patient_id,
                            "QUERY", details={"question": question[:200]}))
''',
},

26: {
"tests/unit/test_hallucination_detector.py": '''\
"""Unit tests for hallucination detector."""
import pytest
from unittest.mock import AsyncMock
from src.monitoring.hallucination_detector import HallucinationDetector


@pytest.fixture
def detector():
    mock_client = AsyncMock()
    return HallucinationDetector(mock_client, threshold=0.6)


@pytest.mark.asyncio
async def test_grounded_answer_not_hallucinated(detector):
    answer  = "The patient has diabetes and hypertension."
    context = ["The patient has diabetes mellitus and hypertension.",
               "Blood pressure medication was prescribed."]
    result  = await detector.detect(answer, context)
    assert not result.is_hallucinated
    assert result.severity in ("none", "minor")


@pytest.mark.asyncio
async def test_hallucinated_answer_detected(detector):
    answer  = "Patient underwent triple bypass surgery and was placed on ECMO."
    context = ["Patient had a mild headache and was given paracetamol."]
    result  = await detector.detect(answer, context)
    assert result.grounding_score < 0.6


@pytest.mark.asyncio
async def test_empty_context_critical_severity(detector):
    result = await detector.detect("Some clinical claim about the patient.", [])
    assert result.grounding_score == 0.0


@pytest.mark.asyncio
async def test_severity_none_on_high_score(detector):
    answer  = "fever temperature elevated"
    context = ["Patient has fever with elevated temperature of 38.9 degrees."]
    result  = await detector.detect(answer, context)
    assert result.severity in ("none", "minor", "moderate")


@pytest.mark.asyncio
async def test_ungrounded_claims_listed(detector):
    answer  = "Patient has cancer. Patient needs chemotherapy. Prognosis is poor."
    context = ["Patient has a mild upper respiratory infection."]
    result  = await detector.detect(answer, context)
    assert isinstance(result.ungrounded_claims, list)
''',
},

27: {
"infra/k8s/api-deployment.yaml": '''\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: medical-doc-api
  namespace: medical-doc-intelligence
  labels:
    app: medical-doc-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: medical-doc-api
  template:
    metadata:
      labels:
        app: medical-doc-api
    spec:
      containers:
        - name: api
          image: YOUR_REGISTRY/medical-doc-api:latest
          ports:
            - containerPort: 8000
          env:
            - name: OLLAMA_BASE_URL
              value: "http://ollama-service:11434"
            - name: CHROMADB_HOST
              value: "chromadb-service"
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: medical-doc-secrets
                  key: redis-url
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: medical-doc-api-service
  namespace: medical-doc-intelligence
spec:
  selector:
    app: medical-doc-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
''',
},

28: {
"docs/api_reference.md": '''\
# API Reference — Medical Document Intelligence

Base URL: `http://localhost:8000`

---

## POST /documents/upload

Upload a medical PDF for processing.

**Request:**
```
Content-Type: multipart/form-data
file: <PDF file>
```

**Response:**
```json
{
  "message": "Document queued for processing",
  "document_id": "doc-abc123",
  "filename": "discharge_summary.pdf",
  "size_bytes": 245678
}
```

---

## POST /query

Ask a question about ingested medical documents.

**Request:**
```json
{
  "question": "What is the patient diagnosis?",
  "patient_id": "PAT-000001",
  "doc_type": "discharge_summary",
  "session_id": "session-xyz"
}
```

**Response:**
```json
{
  "question": "What is the patient diagnosis?",
  "answer": "Based on the discharge summary, the patient was diagnosed with type 2 diabetes mellitus and hypertension.",
  "citations": ["[Source 1] Doc:doc-abc123 (relevance: 0.94)"],
  "confidence": 0.92,
  "latency_ms": 1243.5
}
```

---

## GET /health

Returns API and dependency health status.

**Response:**
```json
{
  "status": "ok",
  "ollama": true,
  "rag": true
}
```

---

## GET /metrics

Prometheus metrics endpoint.

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400  | Invalid request (e.g. non-PDF file) |
| 401  | Missing or invalid API key |
| 503  | RAG pipeline not initialised |
| 500  | Internal processing error |
''',
},

29: {
"src/api/cache_manager.py": '''\
"""Two-tier response cache: L1 in-memory, L2 Redis."""
from __future__ import annotations
import hashlib
import json
import logging
from collections import OrderedDict
import redis

logger = logging.getLogger(__name__)


class ResponseCache:
    """LRU in-memory L1 cache backed by Redis L2."""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 l1_max_size: int = 256, l2_ttl: int = 3600) -> None:
        self._l1: OrderedDict[str, str] = OrderedDict()
        self._l1_max  = l1_max_size
        self._l2_ttl  = l2_ttl
        try:
            self._r = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            self._r = None
            logger.warning("Redis unavailable — L1 cache only")

    def _key(self, question: str, patient_id: str | None,
             doc_type: str) -> str:
        raw = f"{question}|{patient_id}|{doc_type}"
        return "medai:cache:" + hashlib.sha256(raw.encode()).hexdigest()

    def get(self, question: str, patient_id: str | None = None,
            doc_type: str = "default") -> dict | None:
        key = self._key(question, patient_id, doc_type)
        if key in self._l1:
            self._l1.move_to_end(key)
            return json.loads(self._l1[key])
        if self._r:
            raw = self._r.get(key)
            if raw:
                self._l1_set(key, raw)
                return json.loads(raw)
        return None

    def set(self, question: str, response: dict,
            patient_id: str | None = None,
            doc_type: str = "default") -> None:
        key  = self._key(question, patient_id, doc_type)
        data = json.dumps(response)
        self._l1_set(key, data)
        if self._r:
            self._r.setex(key, self._l2_ttl, data)

    def _l1_set(self, key: str, value: str) -> None:
        self._l1[key] = value
        self._l1.move_to_end(key)
        if len(self._l1) > self._l1_max:
            self._l1.popitem(last=False)

    def invalidate(self, document_id: str) -> None:
        """Invalidate all cache entries — called on document update."""
        pattern = "medai:cache:*"
        if self._r:
            keys = self._r.keys(pattern)
            if keys:
                self._r.delete(*keys)
        self._l1.clear()
        logger.info("Cache invalidated for document %s", document_id)
''',
},

30: {
"README.md": '''\
# Medical Document Intelligence Pipeline

[![CI](https://github.com/suzanvusal/medical-doc-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/suzanvusal/medical-doc-intelligence/actions)
[![30-Day Build](https://github.com/suzanvusal/medical-doc-intelligence/actions/workflows/daily_commit_automation.yml/badge.svg)](https://github.com/suzanvusal/medical-doc-intelligence/actions)

LLM-powered pipeline for processing medical documents — summarization, entity extraction, semantic search, and RAG-powered Q&A with hallucination detection.

## Architecture

```
Medical PDFs / Reports
        │
        ▼ PyMuPDF + Tesseract OCR
Text Extraction → PII Anonymization → Smart Chunking
        │
        ▼ Ollama (nomic-embed-text)
ChromaDB Vector Store + BM25 Index
        │
        ▼ Hybrid Search (Semantic + BM25 + RRF)
Context Assembly + Re-ranking
        │
        ▼ Ollama (llama3.2)
Structured Answer Generation
        │
        ▼ Quality Monitor
Faithfulness Check + Hallucination Detection + Drift Monitor
        │
        ▼ FastAPI REST API
Interactive Q&A + Session Management + Audit Log
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Document Processing | PyMuPDF, Tesseract OCR |
| LLM | Ollama (llama3.2) — 100% local, free |
| Embeddings | Ollama (nomic-embed-text) |
| Vector Store | ChromaDB |
| Keyword Search | BM25 (rank-bm25) |
| RAG | Custom pipeline with RRF fusion |
| Quality Monitoring | ROUGE-L, Faithfulness, Hallucination NLI |
| API | FastAPI, Celery |
| Caching | Redis (L1 + L2 two-tier) |
| Observability | Prometheus, Grafana |
| Security | AES-256, RBAC, HIPAA audit log |
| Infrastructure | Docker Compose, Kubernetes |

## Quick Start

```bash
# Start infrastructure
docker compose up -d

# Pull Ollama models (one time)
ollama pull llama3.2
ollama pull nomic-embed-text

# Start API
make serve

# Upload a document
curl -X POST http://localhost:8000/documents/upload \\
     -F "file=@discharge_summary.pdf"

# Ask a question
curl -X POST http://localhost:8000/query \\
     -H "Content-Type: application/json" \\
     -d \'{"question": "What is the patient diagnosis?"}\'
```

## Key Features

- 🔍 **Hybrid Search** — semantic + BM25 with RRF fusion for maximum recall
- 🤖 **100% Local LLM** — Ollama runs entirely on your machine, no API costs
- 🛡️ **Hallucination Detection** — every response verified against source documents
- 📊 **Drift Monitoring** — tracks quality degradation over time
- 🏥 **HIPAA-aware** — PII anonymization + immutable audit log
- 💬 **Multi-turn Sessions** — maintains conversation context in Redis

## License
MIT
''',
},
}
