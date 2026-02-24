from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "app" / "src"))

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite://")
os.environ.setdefault("SEED_ENABLED", "false")

from app.infrastructure.db import session as db_session  # noqa: E402
from app.infrastructure.db.base import Base  # noqa: E402
import app.main as main_module  # noqa: E402
from app.main import app  # noqa: E402
import app.routes.predict as predict_route  # noqa: E402


engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

db_session.engine = engine
db_session.SessionLocal = TestingSessionLocal
main_module.engine = engine
main_module.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _disable_rabbit(monkeypatch):
    monkeypatch.setattr(predict_route, "publish_task", lambda *args, **kwargs: None)
    yield


@pytest.fixture()
def client():
    app.dependency_overrides = {}
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def register_user(client):
    def _register(email: str = "user@example.com", password: str = "test123") -> dict[str, str]:
        response = client.post("/auth/register", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _register
