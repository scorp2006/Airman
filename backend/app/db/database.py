"""
Database connection setup using SQLAlchemy.

- `engine` is the low-level connection to PostgreSQL.
- `SessionLocal` creates short-lived DB sessions for each API request.
- `Base` is the parent class that all our table models will inherit from.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings


# Create the engine. echo=settings.DEBUG prints SQL statements when DEBUG=True.
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)

# SessionLocal is a factory: calling SessionLocal() gives a new DB session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Base is the class all our ORM models will inherit from.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that gives a request a DB session and
    cleans it up afterwards. Use with `Depends(get_db)` in routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
