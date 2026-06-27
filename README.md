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
curl -X POST http://localhost:8000/documents/upload \
     -F "file=@discharge_summary.pdf"

# Ask a question
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the patient diagnosis?"}'
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

# 11:41:14 — chore: tag v1.0.0 release with full changelog
