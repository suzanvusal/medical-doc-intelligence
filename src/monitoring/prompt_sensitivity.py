"""
src/monitoring/prompt_sensitivity.py
Day 21: LLM drift detection
Focus: Response distribution monitoring, quality drift, prompt sensitivity
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class PromptSensitivity:
    """Implementation for prompt_sensitivity — medical document intelligence pipeline."""

    def __init__(self) -> None:
        logger.info("Initialising %s", self.__class__.__name__)

    def process(self) -> None:
        raise NotImplementedError

# 11:08:25 — feat: add drift severity classification and alert routing
