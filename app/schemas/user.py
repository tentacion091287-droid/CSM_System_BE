import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, computed_field
from app.models.user import UserRole


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def name(self) -> str:
        return self.full_name

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class RoleUpdate(BaseModel):
    role: UserRole


class PaginatedUsers(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int
