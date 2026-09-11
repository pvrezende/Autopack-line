from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, LoginRequest, LoginResponse, UserRead
from app.services.audit_service import write_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    user = db.scalar(select(User).where(User.username == username))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        write_audit(db, "LOGIN_FAILED", details={"username": username})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")
    user.last_login_at = datetime.utcnow()
    db.flush()
    token = create_access_token(user)
    write_audit(db, "LOGIN", user=user, entity_type="USER", entity_id=user.id, commit=False)
    db.commit()
    db.refresh(user)
    return LoginResponse(access_token=token, user=user)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="A nova senha deve ser diferente da senha atual")
    user.password_hash = hash_password(payload.new_password)
    db.flush()
    write_audit(db, "PASSWORD_CHANGED", user=user, entity_type="USER", entity_id=user.id, commit=False)
    db.commit()
    return {"status": "ok"}
