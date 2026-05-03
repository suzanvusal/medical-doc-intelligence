"""
src/ingestion/document_router.py
Day 8: Document classification & routing
Focus: Zero-shot classification, document type routing, priority scoring
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class DocumentRouter:
    """Implementation for document_router — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError
