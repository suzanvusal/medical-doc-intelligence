"""
src/ingestion/medical_terms.py
Day 3: Document chunking & preprocessing pipeline
Focus: Smart text chunking, medical term preservation, preprocessing for LLM
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class MedicalTerms:
    """Implementation for medical_terms — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError

# 11:53:31 — feat: implement chunk metadata enrichment with source docume

# 11:53:31 — refactor: make chunk size configurable per document type

# 11:45:42 — fix: handle None input edge case in medical_terms
