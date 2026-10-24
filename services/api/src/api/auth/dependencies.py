from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from api.core.config import get_settings
from api.users.models import Role
from api.users.service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise _credentials_exception()

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise _credentials_exception()

    user = get_user_by_id(user_id)
    if not user or not user.get("is_active"):
        raise _credentials_exception()
    return user


CurrentUser = Annotated[dict, Depends(get_current_user)]


def ensure_owner_or_admin(resource_user_id: str, current_user: dict) -> None:
    if current_user["id"] != resource_user_id and current_user["role"] != Role.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
