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
