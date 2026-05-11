"""
src/api/routers/documents.py
Day 16: FastAPI REST API — core endpoints
Focus: Document upload, process, query endpoints, request validation
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class Documents:
    """Implementation for documents — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError
