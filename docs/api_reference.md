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
