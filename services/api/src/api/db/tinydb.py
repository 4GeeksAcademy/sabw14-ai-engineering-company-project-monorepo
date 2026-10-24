from functools import lru_cache
from pathlib import Path

from tinydb import TinyDB
from tinydb.table import Table

from api.core.config import get_settings


@lru_cache
def get_db() -> TinyDB:
    path = Path(get_settings().TINYDB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(path)


def users_table() -> Table:
    return get_db().table("users")


def profiles_table() -> Table:
    return get_db().table("profiles")
