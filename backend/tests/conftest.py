import os
from pathlib import Path

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./.test-data/test.db"
os.environ["REDIS_URL"] = "redis://localhost:6399/15"
os.environ["CRAWLER_ENABLED"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-only-with-32-bytes-minimum"
os.environ["OPENAI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    test_path = Path(".test-data/test.db")
    if test_path.exists():
        test_path.unlink()
    if test_path.parent.exists() and not any(test_path.parent.iterdir()):
        test_path.parent.rmdir()
