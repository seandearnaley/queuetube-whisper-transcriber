from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import db
from app.api import create_app
from app.db import Base
import app.models  # noqa: F401


@pytest.fixture()
def test_app(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path}/test.db"
    engine = create_engine(
        database_url, connect_args={"check_same_thread": False}, pool_pre_ping=True
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db.engine = engine
    db.SessionLocal = TestingSessionLocal

    Base.metadata.create_all(bind=engine)
    app = create_app()
    return app


@pytest.fixture()
def client(test_app):
    return TestClient(test_app)


@pytest.fixture()
def db_session():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()
