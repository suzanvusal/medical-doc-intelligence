"""HIPAA-compliant audit logger for all document access events."""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    event_type:  str
    user_id:     str
    document_id: str | None
    patient_id:  str | None
    action:      str
    ip_address:  str | None = None
    success:     bool = True
    details:     dict = field(default_factory=dict)
    timestamp:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditLogger:
    """Immutable append-only audit log for HIPAA compliance."""

    def __init__(self, log_path: str = "logs/audit.jsonl") -> None:
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: AuditEvent) -> None:
        record = {
            "timestamp":   event.timestamp,
            "event_type":  event.event_type,
            "user_id":     event.user_id,
            "document_id": event.document_id,
            "patient_id":  event.patient_id,
            "action":      event.action,
            "ip_address":  event.ip_address,
            "success":     event.success,
            "details":     event.details,
        }
        with open(self._path, "a") as f:
            f.write(json.dumps(record) + "
")
        logger.info("AUDIT %s | user=%s doc=%s action=%s",
                    event.event_type, event.user_id,
                    event.document_id, event.action)

    def log_access(self, user_id: str, document_id: str,
                   patient_id: str | None = None, ip: str | None = None) -> None:
        self.log(AuditEvent("DOCUMENT_ACCESS", user_id, document_id,
                            patient_id, "READ", ip_address=ip))

    def log_query(self, user_id: str, question: str,
                  patient_id: str | None = None) -> None:
        self.log(AuditEvent("RAG_QUERY", user_id, None, patient_id,
                            "QUERY", details={"question": question[:200]}))

# 12:31:10 — fix: audit log missing user_id on anonymous API calls

# 11:19:47 — docs: update example in docstring of audit_logger
