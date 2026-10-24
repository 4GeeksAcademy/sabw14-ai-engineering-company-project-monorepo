import pytest
from fastapi.testclient import TestClient

from api.core.config import get_settings
from api.db.tinydb import get_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("TINYDB_PATH", str(tmp_path / "auth_db.json"))
    get_settings.cache_clear()
    get_db.cache_clear()

    from api.main import app

    with TestClient(app) as c:
        yield c

    get_db().close()
    get_settings.cache_clear()
    get_db.cache_clear()


@pytest.fixture
def register(client):
    def _register(email: str, password: str = "secret123", **profile) -> dict:
        r = client.post("/users", json={"email": email, "password": password, **profile})
        assert r.status_code == 201, r.text
        return r.json()

    return _register


@pytest.fixture
def auth_headers(client):
    def _auth_headers(email: str, password: str = "secret123") -> dict:
        r = client.post("/auth/login", data={"username": email, "password": password})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _auth_headers
