from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from api.users.models import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None
    phone: str | None = None
    address: str | None = None

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes")
        return v


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: Role | None = None


class UserOut(BaseModel):
    id: str
    email: EmailStr
    is_active: bool
    role: Role
    created_at: datetime
