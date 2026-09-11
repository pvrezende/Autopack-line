from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from app.core.security import hash_password, require_roles
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.user import AuditLogRead, UserCreate, UserRead, UserUpdate
from app.services.audit_service import write_audit

router = APIRouter(tags=["Users"])
admin_only = require_roles("ADMIN")


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return list(db.scalars(select(User).order_by(User.full_name, User.username)).all())


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), actor: User = Depends(admin_only)):
    username = payload.username.strip().lower()
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=409, detail="Nome de usuário já cadastrado")
    item = User(username=username, full_name=payload.full_name.strip(), password_hash=hash_password(payload.password), role=payload.role, active=True)
    db.add(item); db.flush()
    write_audit(db, "USER_CREATED", user=actor, entity_type="USER", entity_id=item.id, details={"username": item.username, "role": item.role}, commit=False)
    db.commit(); db.refresh(item)
    return item


@router.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), actor: User = Depends(admin_only)):
    item = db.get(User, user_id)
    if not item: raise HTTPException(status_code=404, detail="Usuário não encontrado")
    data = payload.model_dump(exclude_unset=True)
    if item.id == actor.id and data.get("active") is False:
        raise HTTPException(status_code=400, detail="Você não pode desativar seu próprio usuário")
    if item.id == actor.id and data.get("role") and data["role"] != "ADMIN":
        raise HTTPException(status_code=400, detail="Você não pode remover seu próprio perfil de administrador")
    if "username" in data:
        new_username = data["username"].strip().lower()
        duplicate = db.scalar(select(User).where(User.username == new_username, User.id != item.id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Nome de usuário já cadastrado")
        item.username = new_username
    if "full_name" in data: item.full_name = data["full_name"].strip()
    if "role" in data: item.role = data["role"]
    if "active" in data: item.active = data["active"]
    if data.get("password"): item.password_hash = hash_password(data["password"])
    db.flush()
    write_audit(db, "USER_UPDATED", user=actor, entity_type="USER", entity_id=item.id, details={"username": item.username, "role": item.role, "active": item.active, "password_reset": bool(data.get("password"))}, commit=False)
    db.commit(); db.refresh(item)
    return item


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), actor: User = Depends(admin_only)):
    item = db.get(User, user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if item.id == actor.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir seu próprio usuário")

    if item.role == "ADMIN" and item.active:
        active_admins = db.scalar(
            select(func.count()).select_from(User).where(User.role == "ADMIN", User.active.is_(True))
        ) or 0
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="Não é possível excluir o último administrador ativo")

    deleted_username = item.username
    deleted_role = item.role

    # Preserva o histórico: remove apenas o vínculo FK com o usuário que será excluído.
    # O campo username permanece gravado em audit_logs para rastreabilidade.
    db.execute(update(AuditLog).where(AuditLog.user_id == item.id).values(user_id=None))
    db.delete(item)
    db.flush()
    write_audit(
        db,
        "USER_DELETED",
        user=actor,
        entity_type="USER",
        entity_id=user_id,
        details={"username": deleted_username, "role": deleted_role},
        commit=False,
    )
    db.commit()
    return None


@router.get("/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(limit: int = Query(100, ge=10, le=500), db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all())
