"""
src/llm/medical_ontology.py
Day 7: Clinical entity extraction
Focus: Named entity recognition for medical terms, medications, diagnoses, procedures
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class MedicalOntology:
    """Implementation for medical_ontology — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError

# 10:58:32 — feat: add entity relationship extraction (medication→diagnos
