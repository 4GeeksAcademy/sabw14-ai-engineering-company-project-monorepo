import argparse
import getpass
import sys

from pydantic import ValidationError

from api.users import service
from api.users.models import Role
from api.users.schemas import UserCreate


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin user in TinyDB")
    parser.add_argument("email")
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        sys.exit("Passwords do not match")

    try:
        user = service.create_user(UserCreate(email=args.email, password=password), role=Role.admin)
    except ValidationError as e:
        sys.exit(str(e))
    except service.EmailAlreadyExistsError:
        sys.exit("Email already registered")
    print(f"Admin created: {user['email']} ({user['id']})")


if __name__ == "__main__":
    main()
