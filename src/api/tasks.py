"""
src/api/tasks.py
Day 17: Background processing pipeline
Focus: Async document processing, Celery tasks, progress tracking
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class Tasks:
    """Implementation for tasks — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError
