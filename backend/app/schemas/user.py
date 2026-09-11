from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

Role = Literal["OPERATOR", "SUPERVISOR", "ADMIN"]


class UserRead(BaseModel):
    id: int
    username: str
    full_name: str
    role: Role
    active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    full_name: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8, max_length=72)
    role: Role = "OPERATOR"


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    full_name: str | None = Field(default=None, min_length=3, max_length=150)
    role: Role | None = None
    active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)


class AuditLogRead(BaseModel):
    id: int
    user_id: int | None
    username: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
