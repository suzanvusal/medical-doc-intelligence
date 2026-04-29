"""
src/llm/model_manager.py
Day 4: Ollama integration & model management
Focus: Ollama client, model pulling, health checks, model versioning
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class ModelManager:
    """Implementation for model_manager — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError
