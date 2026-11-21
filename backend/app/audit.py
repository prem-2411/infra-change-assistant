from sqlalchemy.orm import Session

from .models import AuditLog


def record(db: Session, actor_id: int | None, action: str, entity: str,
           entity_id: int | None = None, details: dict | None = None) -> None:
    """Stage an audit row in the caller's transaction (the caller commits)."""
    db.add(AuditLog(actor_id=actor_id, action=action, entity=entity,
                    entity_id=entity_id, details=details or {}))
