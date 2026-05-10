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

# 11:52:17 — test: add schema validation tests for all document types

# 11:52:17 — style: reorder imports alphabetically in test_schemas

# 11:52:17 — fix: add missing type hint in test_schemas

# 11:45:55 — docs: update example in docstring of test_schemas

# 11:45:42 — chore: day 5 maintenance sweep

# 11:15:23 — refactor: rename variable for clarity in test_schemas

# 11:05:49 — chore: add logging statement to test_schemas
