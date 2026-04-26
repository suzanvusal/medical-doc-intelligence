#!/usr/bin/env python3
"""
Bootstrap Script — Run ONCE locally to set up the medical-doc-intelligence repo.
"""
import argparse
import subprocess
from pathlib import Path

DIRS = [
    "src/ingestion","src/llm","src/vectorstore","src/rag",
    "src/monitoring","src/api","src/security",
    "infra/docker","infra/k8s","infra/grafana/dashboards",
    "infra/grafana/provisioning","infra/prometheus",
    "tests/unit","tests/integration","tests/load",
    "notebooks","docs/runbooks","docs/examples",
    "scripts","configs","postman",
    ".github/workflows",".automation_state","plan","templates"
]

BASE_FILES = {
"README.md": """\
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
""",

"pyproject.toml": """\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "medical-doc-intelligence"
version = "0.1.0"
description = "LLM-powered medical document intelligence pipeline with RAG"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "pymupdf>=1.23.7",
    "pytesseract>=0.3.10",
    "chromadb>=0.4.18",
    "ollama>=0.1.7",
    "httpx>=0.25.2",
    "celery[redis]>=5.3.4",
    "redis>=5.0.1",
    "asyncpg>=0.29.0",
    "prometheus-client>=0.19.0",
    "jinja2>=3.1.2",
    "pyyaml>=6.0.1",
    "python-multipart>=0.0.6",
    "langchain>=0.1.0",
    "langchain-community>=0.0.10",
    "sentence-transformers>=2.2.2",
    "rank-bm25>=0.2.2",
    "rouge-score>=0.1.2",
    "bert-score>=0.3.13",
    "nltk>=3.8.1",
    "spacy>=3.7.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.2",
    "black>=23.11.0",
    "ruff>=0.1.7",
    "mypy>=1.7.1",
    "locust>=2.19.1",
    "bandit>=1.7.6",
    "pip-audit>=2.6.1",
]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
select = ["E","F","I","N","W"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing"
""",

"docker-compose.yml": """\
version: "3.9"

services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes:
      - ollama_models:/root/.ollama
    environment:
      OLLAMA_HOST: "0.0.0.0"
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
              count: all
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      retries: 5

  chromadb:
    image: chromadb/chroma:latest
    ports: ["8001:8000"]
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      IS_PERSISTENT: "TRUE"
      PERSIST_DIRECTORY: /chroma/chroma
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7.2-alpine
    ports: ["6379:6379"]
    volumes: [redis_data:/data]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: medai
      POSTGRES_PASSWORD: medai
      POSTGRES_DB: medical_docs
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U medai"]
      interval: 10s

  api:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.api
    ports: ["8000:8000"]
    depends_on:
      ollama: {condition: service_healthy}
      chromadb: {condition: service_healthy}
      redis: {condition: service_healthy}
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      CHROMADB_HOST: chromadb
      CHROMADB_PORT: 8000
      REDIS_URL: redis://redis:6379
      DATABASE_URL: postgresql://medai:medai@postgres/medical_docs
    volumes:
      - ./data:/app/data

  prometheus:
    image: prom/prometheus:v2.47.2
    ports: ["9090:9090"]
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:10.2.2
    ports: ["3000:3000"]
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/dashboards:/etc/grafana/provisioning/dashboards

volumes:
  ollama_models:
  chroma_data:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:
""",

"Makefile": """\
.PHONY: up down logs test lint format serve pull-models

up:
\tdocker compose up -d
\t@echo "✓ Stack started"

down:
\tdocker compose down -v

pull-models:
\tollama pull llama3.2
\tollama pull nomic-embed-text
\t@echo "✓ Models ready"

serve:
\tuvicorn src.api.main:app --reload --port 8000

test:
\tpytest tests/ -v --cov=src --cov-report=term-missing

lint:
\truff check src/ tests/ --fix

format:
\tblack src/ tests/

clean:
\tfind . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
""",

"configs/base_config.yaml": """\
ollama:
  base_url: "http://localhost:11434"
  llm_model: "llama3.2"
  embedding_model: "nomic-embed-text"
  timeout_seconds: 120
  keep_alive: "10m"

chromadb:
  host: "localhost"
  port: 8001
  collection_prefix: "medical"

redis:
  url: "redis://localhost:6379"
  cache_ttl_seconds: 3600

processing:
  chunk_size: 512
  chunk_overlap: 64
  max_chunks_per_doc: 500
  ocr_enabled: true

rag:
  top_k_retrieval: 5
  rerank_top_k: 3
  min_relevance_score: 0.65
  max_context_tokens: 3000

quality:
  faithfulness_threshold: 0.75
  hallucination_alert_threshold: 0.3
  min_rouge_l: 0.3
""",

".env.example": """\
OLLAMA_BASE_URL=http://localhost:11434
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://medai:medai@localhost/medical_docs
API_KEY=your-api-key-here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
""",

".gitignore": """\
__pycache__/
*.py[cod]
.venv/
venv/
.env
*.egg-info/
dist/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
data/
*.pdf
*.faiss
chroma_db/
.DS_Store
""",

"src/__init__.py": '"""Medical Document Intelligence Pipeline."""\n__version__ = "0.1.0"\n',
"src/ingestion/__init__.py": '"""Document ingestion: PDF processing, OCR, chunking."""\n',
"src/llm/__init__.py": '"""LLM layer: Ollama client, summarization, entity extraction."""\n',
"src/vectorstore/__init__.py": '"""Vector store: ChromaDB, embeddings, search."""\n',
"src/rag/__init__.py": '"""RAG pipeline: retrieval, context building, response generation."""\n',
"src/monitoring/__init__.py": '"""Quality monitoring: faithfulness, hallucination detection, drift."""\n',
"src/api/__init__.py": '"""FastAPI REST API for document intelligence."""\n',
"src/security/__init__.py": '"""Security: encryption, audit logging, access control."""\n',
"tests/__init__.py": "",
"tests/unit/__init__.py": "",
"tests/integration/__init__.py": "",
"tests/load/__init__.py": "",
".automation_state/.gitkeep": "",
"infra/prometheus/prometheus.yml": """\
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: medical-doc-api
    static_configs:
      - targets: ["host.docker.internal:8000"]
    metrics_path: /metrics
""",
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    print("\n🚀 Bootstrapping medical-doc-intelligence repo...")
    print(f"   Remote: {args.repo}\n")

    print("📁 Creating directories...")
    for d in DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)
    print(f"   ✓ {len(DIRS)} directories created")

    print("📝 Writing base files...")
    for filepath, content in BASE_FILES.items():
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"   ✓ {len(BASE_FILES)} files written")

    print("\n🔧 Initialising Git...")
    if not Path(".git").exists():
        run(["git", "init", "-b", "main"])
    run(["git", "config", "user.name",  "MLOps Engineer"])
    run(["git", "config", "user.email", "86911143+suzanvusal@users.noreply.github.com"])
    run(["git", "remote", "remove", "origin"])
    run(["git", "remote", "add", "origin", args.repo])

    print("📦 Making initial commit...")
    run(["git", "add", "-A"])
    run(["git", "commit", "-m",
         "chore: bootstrap medical-doc-intelligence project\n\n"
         "- LLM pipeline: Ollama (llama3.2) + nomic-embed-text\n"
         "- Vector store: ChromaDB\n"
         "- RAG pipeline with hallucination detection\n"
         "- FastAPI serving + Prometheus monitoring"])

    print("🚀 Pushing to GitHub...")
    result = run(["git", "push", "-u", "origin", "main"])
    if result.returncode == 0:
        print("   ✓ Pushed successfully!")
    else:
        print("   ⚠ Push failed — check your token")
        print(f"   {result.stderr[:200]}")

    print("\n" + "="*58)
    print("  ✅ Bootstrap complete!")
    print("="*58)
    print("\nNext steps:")
    print("  1. Create GitHub repo: medical-doc-intelligence")
    print("  2. Add secret AUTOMATION_PAT in repo Settings")
    print("  3. Go to Actions → Run workflow")
    print()


if __name__ == "__main__":
    main()
