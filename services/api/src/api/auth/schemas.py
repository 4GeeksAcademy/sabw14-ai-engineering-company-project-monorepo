from pydantic import BaseModel, EmailStr

from api.users.models import Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeProfile(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None


class MeOut(BaseModel):
    id: str
    email: EmailStr
    role: Role
    profile: MeProfile
