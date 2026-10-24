from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.auth.dependencies import CurrentUser, ensure_owner_or_admin, get_current_user
from api.items import service
from api.items.schemas import ItemCreate, ItemOut, ItemUpdate
from api.users.models import Role

router = APIRouter(prefix="/items", tags=["items"], dependencies=[Depends(get_current_user)])


def _get_owned_item(item_id: str, current_user: dict) -> dict:
    item = service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    ensure_owner_or_admin(item["user_uuid"], current_user)
    return item


@router.get("", response_model=list[ItemOut])
def list_items(current_user: CurrentUser):
    if current_user["role"] == Role.admin.value:
        return service.list_items()
    return service.list_items(current_user["id"])


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemCreate, current_user: CurrentUser):
    return service.create_item(data, user_uuid=current_user["id"])


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: str, current_user: CurrentUser):
    return _get_owned_item(item_id, current_user)


@router.put("/{item_id}", response_model=ItemOut)
def update_item(item_id: str, data: ItemUpdate, current_user: CurrentUser):
    _get_owned_item(item_id, current_user)
    return service.update_item(item_id, data)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: str, current_user: CurrentUser):
    _get_owned_item(item_id, current_user)
    service.delete_item(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
