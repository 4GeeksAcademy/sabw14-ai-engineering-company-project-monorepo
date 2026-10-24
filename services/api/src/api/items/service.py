import uuid
from datetime import UTC, datetime

from tinydb import Query

from api.db.tinydb import items_table
from api.items.schemas import ItemCreate, ItemUpdate


def list_items(user_uuid: str | None = None) -> list[dict]:
    if user_uuid is None:
        return items_table().all()
    return items_table().search(Query().user_uuid == user_uuid)


def get_item(item_id: str) -> dict | None:
    return items_table().get(Query().id == item_id)


def create_item(data: ItemCreate, user_uuid: str) -> dict:
    item = {
        "id": str(uuid.uuid4()),
        "user_uuid": user_uuid,
        "name": data.name,
        "description": data.description,
        "created_at": datetime.now(UTC).isoformat(),
    }
    items_table().insert(item)
    return item


def update_item(item_id: str, data: ItemUpdate) -> dict | None:
    changes = data.model_dump(exclude_unset=True)
    if changes:
        items_table().update(changes, Query().id == item_id)
    return get_item(item_id)


def delete_item(item_id: str) -> bool:
    return bool(items_table().remove(Query().id == item_id))
