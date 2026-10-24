from pydantic import BaseModel, ConfigDict


class ProfileOut(BaseModel):
    id: str
    user_id: str
    name: str | None = None
    phone: str | None = None
    address: str | None = None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    phone: str | None = None
    address: str | None = None
