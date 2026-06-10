"""Two-tier response cache: L1 in-memory, L2 Redis."""
from __future__ import annotations
import hashlib
import json
import logging
from collections import OrderedDict
import redis

logger = logging.getLogger(__name__)


class ResponseCache:
    """LRU in-memory L1 cache backed by Redis L2."""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 l1_max_size: int = 256, l2_ttl: int = 3600) -> None:
        self._l1: OrderedDict[str, str] = OrderedDict()
        self._l1_max  = l1_max_size
        self._l2_ttl  = l2_ttl
        try:
            self._r = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            self._r = None
            logger.warning("Redis unavailable — L1 cache only")

    def _key(self, question: str, patient_id: str | None,
             doc_type: str) -> str:
        raw = f"{question}|{patient_id}|{doc_type}"
        return "medai:cache:" + hashlib.sha256(raw.encode()).hexdigest()

    def get(self, question: str, patient_id: str | None = None,
            doc_type: str = "default") -> dict | None:
        key = self._key(question, patient_id, doc_type)
        if key in self._l1:
            self._l1.move_to_end(key)
            return json.loads(self._l1[key])
        if self._r:
            raw = self._r.get(key)
            if raw:
                self._l1_set(key, raw)
                return json.loads(raw)
        return None

    def set(self, question: str, response: dict,
            patient_id: str | None = None,
            doc_type: str = "default") -> None:
        key  = self._key(question, patient_id, doc_type)
        data = json.dumps(response)
        self._l1_set(key, data)
        if self._r:
            self._r.setex(key, self._l2_ttl, data)

    def _l1_set(self, key: str, value: str) -> None:
        self._l1[key] = value
        self._l1.move_to_end(key)
        if len(self._l1) > self._l1_max:
            self._l1.popitem(last=False)

    def invalidate(self, document_id: str) -> None:
        """Invalidate all cache entries — called on document update."""
        pattern = "medai:cache:*"
        if self._r:
            keys = self._r.keys(pattern)
            if keys:
                self._r.delete(*keys)
        self._l1.clear()
        logger.info("Cache invalidated for document %s", document_id)

# 11:21:28 — style: run black formatter on cache_manager

# 12:50:26 — refactor: rename variable for clarity in cache_manager

# 12:50:26 — chore: day 30 maintenance sweep

# 11:55:46 — chore: remove debug print statement in cache_manager

# 13:38:25 — test: add assertion for return type in cache_manager
