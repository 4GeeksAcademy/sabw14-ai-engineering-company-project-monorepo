from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.auth.dependencies import CurrentUser
from api.auth.schemas import MeOut, MeProfile, Token
from api.core.security import create_access_token, hash_password, verify_password
from api.profiles.service import get_profile_by_user_id
from api.users.service import get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@lru_cache
def _dummy_hash() -> str:
    return hash_password("dummy-password-for-timing")


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = get_user_by_email(form.username)
    # Verify against a dummy hash when the user is missing so timing doesn't reveal registered emails.
    password_ok = verify_password(form.password, user["hashed_password"] if user else _dummy_hash())
    if not user or not password_ok or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user["id"]))


@router.get("/me", response_model=MeOut)
def me(current_user: CurrentUser):
    profile = get_profile_by_user_id(current_user["id"]) or {}
    return MeOut(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user["role"],
        profile=MeProfile(**{k: profile.get(k) for k in ("name", "phone", "address")}),
    )
