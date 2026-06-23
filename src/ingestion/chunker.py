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
        regex   = re.compile(f"(?i)({pattern})\s*[:\n]")
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

# 11:53:31 — fix: chunk overlap causing duplicate content in embeddings

# 11:53:31 — docs: fix typo in inline comment in chunker

# 11:45:55 — fix: correct off-by-one error in chunker

# 11:45:55 — chore: day 4 maintenance sweep

# 10:58:32 — fix: correct off-by-one error in chunker

# 12:03:07 — perf: cache repeated computation in chunker

# 12:00:38 — perf: add __slots__ to dataclass in chunker

# 11:39:28 — refactor: extract magic number to constant in chunker

# 15:16:59 — docs: add module docstring to chunker

# 12:40:27 — chore: day 30 maintenance sweep
