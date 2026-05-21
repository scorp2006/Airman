"""
Audit log service.

Every important action calls `write_audit(...)`. The audit log is append-only
(we never update old rows), so it forms a permanent history of who did what.
"""

import json
from typing import Optional
from sqlalchemy.orm import Session

from app.db.models import AuditLog


def write_audit(
    db: Session,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
) -> AuditLog:
    """
    Insert one row into the audit_logs table.

    old_value / new_value are stored as JSON strings so we can record any shape of data.
    The caller is responsible for db.commit() (we just add to the session here, so
    the audit gets committed in the same transaction as the actual change).
    """
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=json.dumps(old_value) if old_value is not None else None,
        new_value=json.dumps(new_value) if new_value is not None else None,
    )
    db.add(log)
    return log
