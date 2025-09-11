"""Simple in-memory audit log utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class AuditEntry:
    """Structure representing an audit log entry."""

    timestamp: datetime
    user_id: int
    action: str
    detail: Optional[str] = None


audit_log: List[AuditEntry] = []


def log_action(user_id: int, action: str, detail: str | None = None) -> AuditEntry:
    """Record an action in the in-memory ``audit_log`` and return the entry."""

    entry = AuditEntry(timestamp=datetime.utcnow(), user_id=user_id, action=action, detail=detail)
    audit_log.append(entry)
    return entry


def get_logs() -> List[AuditEntry]:
    """Return a copy of the audit log entries."""

    return list(audit_log)
