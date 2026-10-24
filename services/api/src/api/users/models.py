from enum import Enum


class Role(str, Enum):
    admin = "admin"
    manager = "manager"
    user = "user"
