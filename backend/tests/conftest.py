import os

# Must be set before the app is imported (settings are read at import time).
os.environ.update({
    "DATABASE_URL": "sqlite:///./test.db",
    "SECRET_KEY": "test-secret-key-test-secret-key-0123456789",
    "ANTHROPIC_API_KEY": "",
    "LOGIN_RATE_LIMIT": "1000",
    "REVIEW_RATE_LIMIT": "1000",
})

from types import SimpleNamespace  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.observability import metrics  # noqa: E402
from app.ratelimit import reset_limits  # noqa: E402
from app.security import create_token, hash_password  # noqa: E402
from app.seed import seed  # noqa: E402

PASSWORD = "correct-horse-battery"
_HASH = hash_password(PASSWORD)  # hash once: bcrypt is deliberately slow
USERS = {
    "admin": ("admin@t.io", "admin"),
    "eng": ("eng@t.io", "engineer"),
    "eng2": ("eng2@t.io", "engineer"),
    "appr": ("appr@t.io", "approver"),
}


@pytest.fixture()
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        seed(s)
        for key, (email, role) in USERS.items():
            s.add(User(name=key.title(), email=email, password_hash=_HASH, role=role))
        s.commit()
    reset_limits()
    metrics.reset()
    with SessionLocal() as s:
        yield s


@pytest.fixture()
def client(db):
    return TestClient(app)


@pytest.fixture()
def hdr(db):
    def make(key: str) -> dict:
        user = db.query(User).filter_by(email=USERS[key][0]).one()
        token = create_token(user)
        db.rollback()  # end the read transaction so it never blocks writers on SQLite
        return {"Authorization": f"Bearer {token}"}

    return make


# ---- fake LLM client -------------------------------------------------------------------------

def tool_use(name, args, tool_id="t1"):
    return SimpleNamespace(type="tool_use", name=name, input=args, id=tool_id)


class FakeMessages:
    def __init__(self, script):
        self.script, self.calls = list(script), []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(content=item, usage=SimpleNamespace(input_tokens=10, output_tokens=5))


class FakeClient:
    def __init__(self, script):
        self.messages = FakeMessages(script)


def good_plan(request_id, **over):
    args = {"request_id": request_id, "summary": "Low-risk dev change that follows policy.",
            "risks": ["None significant"], "steps": ["Apply change", "Verify"],
            "risk_assessment": "low", "recommendation": "approve"}
    args.update(over)
    return [tool_use("propose_plan", args)]


REQUEST_BODY = {"type": "open_port", "target": "prod-db-01:5432", "risk_level": "high",
                "justification": "Open Postgres to the contractor from anywhere on the internet."}
