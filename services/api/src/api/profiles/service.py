from tinydb import Query

from api.db.tinydb import profiles_table
from api.profiles.schemas import ProfileUpdate


def get_profile_by_user_id(user_id: str) -> dict | None:
    return profiles_table().get(Query().user_id == user_id)


def update_profile(user_id: str, data: ProfileUpdate) -> dict | None:
    if not get_profile_by_user_id(user_id):
        return None
    changes = data.model_dump(exclude_unset=True)
    if changes:
        profiles_table().update(changes, Query().user_id == user_id)
    return get_profile_by_user_id(user_id)
