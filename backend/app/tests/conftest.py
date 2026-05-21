"""
Shared pytest fixtures.

We use an in-memory SQLite database for tests so they run fast and don't touch
the real Postgres database. The SAME SQLAlchemy models work on both engines.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from app.main import app
from app.db.database import Base, get_db
from app.db.models import (
    User, UserRole, BaseLocation, Aircraft, AircraftStatus,
    Sortie, SortieStatus,
)


# In-memory SQLite shared across the whole test session.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Replace the real DB with the test DB for ALL routes.
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """Fresh DB per test: drop everything, recreate, seed minimum fixtures, yield, drop."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    base = BaseLocation(name="Test Base", code="TST")
    session.add(base)
    session.flush()

    users = {
        "admin": User(full_name="Admin", email="admin@t.in", role=UserRole.ADMIN, base_id=base.id),
        "dispatcher": User(full_name="Disp", email="d@t.in", role=UserRole.DISPATCHER, base_id=base.id),
        "instructor": User(full_name="Inst", email="i@t.in", role=UserRole.INSTRUCTOR, base_id=base.id),
        "cfi": User(full_name="CFI", email="cfi@t.in", role=UserRole.CFI, base_id=base.id),
        "cadet": User(full_name="Cadet", email="c@t.in", role=UserRole.CADET, base_id=base.id),
        "maint": User(full_name="Maint", email="m@t.in", role=UserRole.MAINTENANCE_OFFICER, base_id=base.id),
    }
    session.add_all(users.values())
    session.flush()

    aircraft_ready = Aircraft(registration="VT-RDY", aircraft_type="Cessna 172", base_id=base.id,
                              status=AircraftStatus.READY)
    aircraft_grounded = Aircraft(registration="VT-GRD", aircraft_type="Piper PA-28", base_id=base.id,
                                 status=AircraftStatus.GROUNDED)
    session.add_all([aircraft_ready, aircraft_grounded])
    session.flush()

    now = datetime.utcnow()
    sortie = Sortie(
        sortie_number="T-001",
        cadet_id=users["cadet"].id,
        instructor_id=users["instructor"].id,
        aircraft_id=aircraft_ready.id,
        base_id=base.id,
        lesson_type="Test",
        scheduled_start=now + timedelta(hours=1),
        scheduled_end=now + timedelta(hours=2),
        status=SortieStatus.SCHEDULED,
    )
    session.add(sortie)
    session.commit()

    # Pack everything tests need into a small object.
    class Ctx:
        pass
    ctx = Ctx()
    ctx.session = session
    ctx.users = {k: v.id for k, v in users.items()}
    ctx.aircraft_ready_id = aircraft_ready.id
    ctx.aircraft_grounded_id = aircraft_grounded.id
    ctx.sortie_id = sortie.id
    yield ctx

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def headers(user_id: int) -> dict:
    """Helper: build the auth header for a given user id."""
    return {"X-User-Id": str(user_id)}
