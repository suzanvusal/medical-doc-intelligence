.PHONY: up down logs test lint format serve pull-models

up:
	docker compose up -d
	@echo "✓ Stack started"

down:
	docker compose down -v

pull-models:
	ollama pull llama3.2
	ollama pull nomic-embed-text
	@echo "✓ Models ready"

serve:
	uvicorn src.api.main:app --reload --port 8000

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/ --fix

format:
	black src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
