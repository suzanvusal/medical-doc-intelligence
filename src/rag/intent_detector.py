"""
src/rag/intent_detector.py
Day 12: Query understanding & medical NLP
Focus: Medical query parsing, intent detection, query rewriting
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class IntentDetector:
    """Implementation for intent_detector — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError

# 11:55:47 — feat: add query validation to reject non-medical queries

# 11:55:47 — test: add query understanding tests for 20 clinical question
