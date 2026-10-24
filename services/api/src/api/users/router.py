from fastapi import APIRouter, HTTPException, Response, status

from api.auth.dependencies import CurrentUser, ensure_owner_or_admin
from api.users import service
from api.users.models import Role
from api.users.schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, current_user: CurrentUser):
    if current_user["role"] != Role.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create users")
    try:
        return service.create_user(data)
    except service.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")


@router.get("", response_model=list[UserOut])
def list_users(current_user: CurrentUser):
    return service.list_users()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, current_user: CurrentUser):
    ensure_owner_or_admin(user_id, current_user)
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: str, data: UserUpdate, current_user: CurrentUser):
    ensure_owner_or_admin(user_id, current_user)
    if data.role is not None and current_user["role"] != Role.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can change roles")

    changes = data.model_dump(mode="json", exclude_none=True)
    try:
        user = service.update_user(user_id, changes)
    except service.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, current_user: CurrentUser):
    ensure_owner_or_admin(user_id, current_user)
    if not service.delete_user(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
