"""
tests/conftest.py
Day 23: Integration tests — full pipeline
Focus: End-to-end pipeline tests, document to answer validation
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class Conftest:
    """Implementation for conftest — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError
