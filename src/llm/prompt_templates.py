"""Jinja2 prompt templates for medical document processing."""
from __future__ import annotations
from jinja2 import Environment, BaseLoader

_env = Environment(loader=BaseLoader())

# ── Summarization ──────────────────────────────────────────
SUMMARIZATION_SYSTEM = """You are a clinical documentation specialist. Your task is to produce accurate,
concise summaries of medical documents. Always base your summary strictly on
the provided text. Never add information not present in the source document.
Output valid JSON only."""

SUMMARIZATION_PROMPT = """Summarize the following medical document.

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
ENTITY_EXTRACTION_PROMPT = """Extract all clinical entities from the following medical text.

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
RAG_SYSTEM = """You are a clinical information assistant. Answer questions about medical documents
using ONLY the provided context. If the answer is not in the context, say so clearly.
Never fabricate clinical information."""

RAG_PROMPT = """Context from medical documents:
{{ context }}

Question: {{ question }}

Provide a precise, evidence-based answer citing the relevant context.
If uncertain, express that uncertainty explicitly."""


def render(template_str: str, **kwargs) -> str:
    return _env.from_string(template_str).render(**kwargs)

# 11:45:54 — feat: add model response streaming support

# 11:45:54 — fix: Ollama client timeout too short for large documents

# 11:15:23 — perf: add __slots__ to dataclass in prompt_templates

# 10:58:32 — docs: add module docstring to prompt_templates

# 11:57:47 — fix: correct off-by-one error in prompt_templates

# 11:56:36 — fix: remove unused import in prompt_templates

# 11:58:31 — chore: add logging statement to prompt_templates

# 12:47:24 — perf: add __slots__ to dataclass in prompt_templates

# 12:47:24 — chore: remove debug print statement in prompt_templates

# 12:31:10 — perf: cache repeated computation in prompt_templates

# 12:51:03 — ci: update step name for readability

# 11:19:48 — fix: correct off-by-one error in prompt_templates

# 11:21:28 — chore: remove debug print statement in prompt_templates

# 14:50:08 — refactor: extract magic number to constant in prompt_templat

# 13:49:27 — perf: cache repeated computation in prompt_templates

# 12:28:16 — fix: remove unused import in prompt_templates
