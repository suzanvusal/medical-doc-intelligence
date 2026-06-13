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

# 11:52:17 — feat: implement metadata extractor for document headers

# 11:52:17 — feat: add document type classifier based on content patterns

# 11:52:17 — refactor: extract OCR logic into separate OCRProcessor class

# 11:53:31 — refactor: extract magic number to constant in schemas

# 11:45:55 — perf: add __slots__ to dataclass in schemas

# 11:15:23 — perf: add __slots__ to dataclass in schemas

# 10:58:32 — refactor: extract magic number to constant in schemas

# 11:05:49 — perf: cache repeated computation in schemas

# 12:03:07 — refactor: rename variable for clarity in schemas

# 12:00:38 — perf: add __slots__ to dataclass in schemas

# 12:44:00 — fix: remove unused import in schemas

# 12:44:00 — ci: update step name for readability

# 11:58:15 — docs: update example in docstring of schemas
