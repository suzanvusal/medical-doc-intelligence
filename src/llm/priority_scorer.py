"""
src/llm/priority_scorer.py
Day 8: Document classification & routing
Focus: Zero-shot classification, document type routing, priority scoring
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class PriorityScorer:
    """Implementation for priority_scorer — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError

# 11:00:02 — test: add classifier tests with 10 document type samples
