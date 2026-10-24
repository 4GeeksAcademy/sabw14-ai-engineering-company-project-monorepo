import json
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt
from tinydb import Query

from api.core.config import get_settings
from api.db.tinydb import profiles_table, users_table


def _token(sub: str, minutes: int, key: str | None = None) -> dict:
    settings = get_settings()
    payload = {"sub": sub, "exp": datetime.now(UTC) + timedelta(minutes=minutes)}
    token = jwt.encode(payload, key or settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


# 1
def test_register_creates_user_with_default_role_and_profile(client):
    r = client.post("/users", json={"email": "a@x.com", "password": "secret123", "name": "Ana", "role": "admin"})
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "user"
    assert "hashed_password" not in body
    assert set(body) == {"id", "email", "is_active", "role", "created_at"}

    profile = profiles_table().get(Query().user_id == body["id"])
    assert profile is not None and profile["name"] == "Ana"


# 2
def test_password_is_stored_as_bcrypt_hash(client, register):
    user = register("a@x.com", "secret123")
    data = json.loads(open(get_settings().TINYDB_PATH).read())
    stored = next(u for u in data["users"].values() if u["id"] == user["id"])
    assert stored["hashed_password"].startswith("$2")
    assert stored["hashed_password"] != "secret123"
    assert "secret123" not in json.dumps(data)


# 3
def test_duplicate_email_returns_400(client, register):
    register("a@x.com")
    assert client.post("/users", json={"email": "A@x.com", "password": "secret123"}).status_code == 400


def test_short_password_returns_422(client):
    assert client.post("/users", json={"email": "a@x.com", "password": "123"}).status_code == 422


# 4
def test_invalid_role_returns_422(client, register, auth_headers):
    user = register("a@x.com")
    r = client.put(f"/users/{user['id']}", json={"role": "superadmin"}, headers=auth_headers("a@x.com"))
    assert r.status_code == 422


# 5
def test_login_success_and_wrong_password(client, register):
    register("a@x.com")
    ok = client.post("/auth/login", data={"username": "a@x.com", "password": "secret123"})
    assert ok.status_code == 200
    assert ok.json()["token_type"] == "bearer" and ok.json()["access_token"]

    bad_pw = client.post("/auth/login", data={"username": "a@x.com", "password": "wrongpass"})
    no_user = client.post("/auth/login", data={"username": "nobody@x.com", "password": "secret123"})
    assert bad_pw.status_code == no_user.status_code == 401
    assert bad_pw.json() == no_user.json()


def test_login_inactive_user_returns_401(client, register):
    user = register("a@x.com")
    users_table().update({"is_active": False}, Query().id == user["id"])
    assert client.post("/auth/login", data={"username": "a@x.com", "password": "secret123"}).status_code == 401


# 6
def test_auth_me_token_cases(client, register, auth_headers):
    user = register("a@x.com", name="Ana", phone="111")

    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401
    assert client.get("/auth/me", headers=_token(user["id"], -1)).status_code == 401
    assert client.get("/auth/me", headers=_token(user["id"], 5, key="other-key")).status_code == 401

    r = client.get("/auth/me", headers=auth_headers("a@x.com"))
    assert r.status_code == 200
    assert r.json() == {
        "id": user["id"],
        "email": "a@x.com",
        "role": "user",
        "profile": {"name": "Ana", "phone": "111", "address": None},
    }


# 7
def test_user_cannot_access_other_user(client, register, auth_headers):
    register("a@x.com")
    b = register("b@x.com")
    headers_a = auth_headers("a@x.com")

    assert client.get(f"/users/{b['id']}", headers=headers_a).status_code == 403
    assert client.put(f"/users/{b['id']}", json={"email": "h@x.com"}, headers=headers_a).status_code == 403
    assert client.delete(f"/users/{b['id']}", headers=headers_a).status_code == 403


def test_admin_can_access_other_user(client, register, auth_headers):
    admin = register("admin@x.com")
    b = register("b@x.com")
    users_table().update({"role": "admin"}, Query().id == admin["id"])
    headers = auth_headers("admin@x.com")

    assert client.get(f"/users/{b['id']}", headers=headers).status_code == 200
    r = client.put(f"/users/{b['id']}", json={"role": "manager"}, headers=headers)
    assert r.status_code == 200 and r.json()["role"] == "manager"
    assert client.get("/users/missing", headers=headers).status_code == 404


# 8
def test_non_admin_cannot_change_own_role(client, register, auth_headers):
    user = register("a@x.com")
    r = client.put(f"/users/{user['id']}", json={"role": "admin"}, headers=auth_headers("a@x.com"))
    assert r.status_code == 403


def test_update_email_already_in_use_returns_400(client, register, auth_headers):
    user = register("a@x.com")
    register("b@x.com")
    r = client.put(f"/users/{user['id']}", json={"email": "b@x.com"}, headers=auth_headers("a@x.com"))
    assert r.status_code == 400


# 9
def test_profiles_me(client, register, auth_headers):
    user = register("a@x.com", name="Ana")
    headers = auth_headers("a@x.com")

    assert client.get("/profiles/me").status_code == 401
    assert client.put("/profiles/me", json={"name": "x"}).status_code == 401

    r = client.get("/profiles/me", headers=headers)
    assert r.status_code == 200 and r.json()["name"] == "Ana" and r.json()["user_id"] == user["id"]

    r = client.put("/profiles/me", json={"phone": "555"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Ana" and r.json()["phone"] == "555"


def test_profiles_me_rejects_foreign_user_id(client, register, auth_headers):
    a = register("a@x.com")
    register("b@x.com")
    r = client.put("/profiles/me", json={"user_id": a["id"], "name": "hack"}, headers=auth_headers("b@x.com"))
    assert r.status_code == 422


# 10
def test_delete_user_also_deletes_profile(client, register, auth_headers):
    user = register("a@x.com")
    headers = auth_headers("a@x.com")
    assert profiles_table().get(Query().user_id == user["id"]) is not None

    assert client.delete(f"/users/{user['id']}", headers=headers).status_code == 204
    assert users_table().get(Query().id == user["id"]) is None
    assert profiles_table().get(Query().user_id == user["id"]) is None
    assert client.get("/auth/me", headers=headers).status_code == 401


# 11
PROTECTED_ROUTES = [
    ("GET", "/items", None),
    ("POST", "/items", {"name": "x"}),
    ("GET", "/items/{id}", None),
    ("PUT", "/items/{id}", {"name": "y"}),
    ("DELETE", "/items/{id}", None),
]


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED_ROUTES)
def test_protected_routes_require_token(client, register, auth_headers, method, path, body):
    register("a@x.com")
    headers = auth_headers("a@x.com")
    item = client.post("/items", json={"name": "Laptop"}, headers=headers).json()
    url = path.replace("{id}", item["id"])

    assert client.request(method, url, json=body).status_code == 401
    assert client.request(method, url, json=body, headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401
    assert client.request(method, url, json=body, headers=headers).status_code in (200, 201, 204)


def test_items_owner_rules(client, register, auth_headers):
    a = register("a@x.com")
    register("b@x.com")
    headers_a, headers_b = auth_headers("a@x.com"), auth_headers("b@x.com")

    assert client.post("/items", json={"name": "x", "user_uuid": "hack"}, headers=headers_a).status_code == 422
    item = client.post("/items", json={"name": "Laptop"}, headers=headers_a).json()
    assert item["user_uuid"] == a["id"]
    client.post("/items", json={"name": "Bici"}, headers=headers_b)

    assert [i["name"] for i in client.get("/items", headers=headers_a).json()] == ["Laptop"]
    assert client.get(f"/items/{item['id']}", headers=headers_b).status_code == 403
    assert client.put(f"/items/{item['id']}", json={"name": "z"}, headers=headers_b).status_code == 403
    assert client.delete(f"/items/{item['id']}", headers=headers_b).status_code == 403
    assert client.get("/items/missing", headers=headers_a).status_code == 404
