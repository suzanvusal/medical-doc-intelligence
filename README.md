# Medical Document Intelligence Pipeline

> LLM-powered pipeline that processes medical documents, extracts clinical entities,
> enables semantic search via RAG, and monitors output quality with hallucination detection.

## Architecture

```
Medical PDFs / Reports
        │
        ▼ PDF Processor + OCR
Text Extraction + Chunking
        │
        ▼ Ollama (nomic-embed-text)
ChromaDB Vector Store
        │
        ▼ RAG Pipeline
Ollama LLM (llama3.2) → Summarize / Extract / Answer
        │
        ▼ Quality Monitor
Faithfulness Check + Hallucination Detection
        │
        ▼ FastAPI
REST API + Interactive Q&A
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Document Processing | PyMuPDF, Tesseract OCR |
| LLM Backend | Ollama (llama3.2, nomic-embed-text) |
| Vector Store | ChromaDB |
| RAG Pipeline | Custom retriever + re-ranker |
| API | FastAPI, Celery |
| Quality Monitoring | NLI-based faithfulness, ROUGE, BERTScore |
| Infrastructure | Docker Compose, Kubernetes |
| Observability | Prometheus, Grafana |

## Quick Start

```bash
# Start infrastructure
docker compose up -d

# Pull Ollama models
ollama pull llama3.2
ollama pull nomic-embed-text

# Start API
make serve

# Upload a document
curl -X POST /documents/upload -F "file=@report.pdf"

# Ask a question
curl -X POST /query -d '{"question": "What is the patient diagnosis?"}'
```

## License
MIT
