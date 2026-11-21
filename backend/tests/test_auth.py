from app.config import settings
from app.models import User
from conftest import PASSWORD


def test_login_success_and_wrong_password(client):
    ok = client.post("/auth/login", json={"email": "eng@t.io", "password": PASSWORD})
    assert ok.status_code == 200 and ok.json()["user"]["role"] == "engineer"
    bad = client.post("/auth/login", json={"email": "eng@t.io", "password": "nope-nope-nope"})
    assert bad.status_code == 401
    unknown = client.post("/auth/login", json={"email": "ghost@t.io", "password": PASSWORD})
    assert unknown.status_code == 401 and unknown.json() == bad.json()  # no user enumeration


def test_protected_routes_need_a_valid_token(client):
    assert client.get("/requests").status_code == 401
    assert client.get("/requests", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_register_is_admin_only(client, hdr):
    body = {"name": "New", "email": "new@t.io", "password": "a-long-enough-pass", "role": "engineer"}
    assert client.post("/auth/register", json=body, headers=hdr("eng")).status_code == 403
    assert client.post("/auth/register", json=body).status_code == 401
    assert client.post("/auth/register", json=body, headers=hdr("admin")).status_code == 201
    assert client.post("/auth/register", json=body, headers=hdr("admin")).status_code == 409


def test_register_rejects_weak_password_and_unknown_role(client, hdr):
    weak = {"name": "N", "email": "n@t.io", "password": "short", "role": "engineer"}
    assert client.post("/auth/register", json=weak, headers=hdr("admin")).status_code == 422
    bad_role = {"name": "N", "email": "n@t.io", "password": "a-long-enough-pass", "role": "root"}
    assert client.post("/auth/register", json=bad_role, headers=hdr("admin")).status_code == 422


def test_passwords_are_hashed(db):
    user = db.query(User).filter_by(email="eng@t.io").one()
    assert user.password_hash != PASSWORD and user.password_hash.startswith("$2")


def test_login_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit", 3)
    codes = [client.post("/auth/login", json={"email": "eng@t.io", "password": "wrong-wrong"}).status_code
             for _ in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]
