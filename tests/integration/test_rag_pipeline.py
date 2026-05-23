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

# 13:54:02 — feat: add integration test report generation

# 11:19:48 — perf: cache repeated computation in test_rag_pipeline
