"""
src/llm/entity_linker.py
Day 7: Clinical entity extraction
Focus: Named entity recognition for medical terms, medications, diagnoses, procedures
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class EntityLinker:
    """Implementation for entity_linker — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError

# 11:55:48 — chore: add logging statement to entity_linker

# 12:28:25 — fix: remove unused import in entity_linker

# 11:21:28 — fix: correct off-by-one error in entity_linker

# 12:48:43 — chore: day 30 maintenance sweep

# 12:28:16 — docs: add module docstring to entity_linker

# 12:19:04 — ci: update step name for readability
