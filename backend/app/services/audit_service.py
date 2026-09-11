from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.user import User


def write_audit(
    db: Session,
    action: str,
    user: User | None = None,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    details: dict | None = None,
    commit: bool = True,
) -> AuditLog:
    item = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=details,
    )
    db.add(item)
    if commit:
        db.commit()
        db.refresh(item)
    return item
