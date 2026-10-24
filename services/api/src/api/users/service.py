import uuid
from datetime import UTC, datetime

from passlib.hash import bcrypt
from tinydb import Query

from api.db.tinydb import profiles_table, users_table
from api.users.models import Role
from api.users.schemas import UserCreate


class EmailAlreadyExistsError(ValueError):
    pass


def get_user_by_id(user_id: str) -> dict | None:
    return users_table().get(Query().id == user_id)


def get_user_by_email(email: str) -> dict | None:
    return users_table().get(Query().email == email.lower())


def list_users() -> list[dict]:
    return users_table().all()


def create_user(data: UserCreate) -> dict:
    email = data.email.lower()
    if get_user_by_email(email):
        raise EmailAlreadyExistsError(email)

    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "hashed_password": bcrypt.hash(data.password),
        "is_active": True,
        "role": Role.user.value,
        "created_at": datetime.now(UTC).isoformat(),
    }
    users_table().insert(user)
    profiles_table().insert(
        {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "name": data.name,
            "phone": data.phone,
            "address": data.address,
        }
    )
    return user


def update_user(user_id: str, changes: dict) -> dict | None:
    if not get_user_by_id(user_id):
        return None

    if changes.get("email"):
        changes["email"] = changes["email"].lower()
        other = get_user_by_email(changes["email"])
        if other and other["id"] != user_id:
            raise EmailAlreadyExistsError(changes["email"])

    if changes:
        users_table().update(changes, Query().id == user_id)
    return get_user_by_id(user_id)


def delete_user(user_id: str) -> bool:
    removed = users_table().remove(Query().id == user_id)
    profiles_table().remove(Query().user_id == user_id)
    return bool(removed)
