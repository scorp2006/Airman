"""
Database models (the tables of our application).

Each class is one table in PostgreSQL. SQLAlchemy turns these classes into SQL.

We also define Python Enums for fixed-value fields (like statuses and roles).
Using Enums prevents typos like 'AIBORNE' instead of 'AIRBORNE'.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


# ---------- Enums (fixed sets of allowed values) ----------

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"
    INSTRUCTOR = "INSTRUCTOR"
    CFI = "CFI"
    CADET = "CADET"
    MAINTENANCE_OFFICER = "MAINTENANCE_OFFICER"


class AircraftStatus(str, enum.Enum):
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    AIRBORNE = "AIRBORNE"
    LANDED = "LANDED"
    GROUNDED = "GROUNDED"
    MAINTENANCE = "MAINTENANCE"


class SortieStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    RELEASED = "RELEASED"
    AIRBORNE = "AIRBORNE"
    LANDED = "LANDED"
    TRAINING_SUBMITTED = "TRAINING_SUBMITTED"
    TRAINING_APPROVED = "TRAINING_APPROVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    AIRCRAFT_GROUNDED = "AIRCRAFT_GROUNDED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class TrainingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DefectSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DefectStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


# ---------- Tables ----------

class User(Base):
    """A user of the system. Has one role and (optionally) a home base."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    role = Column(SAEnum(UserRole), nullable=False)
    base_id = Column(Integer, ForeignKey("bases.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships make it easy to navigate from a user to their related records.
    base = relationship("BaseLocation", back_populates="users")


class BaseLocation(Base):
    """A flight school base / airport. Renamed from `bases` to avoid clashing with SQLAlchemy's Base class."""
    __tablename__ = "bases"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    location = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="base")
    aircraft = relationship("Aircraft", back_populates="base")


class Aircraft(Base):
    """A physical aircraft in the fleet."""
    __tablename__ = "aircraft"

    id = Column(Integer, primary_key=True)
    registration = Column(String(20), unique=True, nullable=False)  # e.g. VT-ABC
    aircraft_type = Column(String(50), nullable=False)              # e.g. Cessna 172
    base_id = Column(Integer, ForeignKey("bases.id"), nullable=False)
    status = Column(SAEnum(AircraftStatus), default=AircraftStatus.READY, nullable=False)
    tbo_remaining_hours = Column(Integer, default=2000, nullable=False)  # Time Between Overhaul
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    base = relationship("BaseLocation", back_populates="aircraft")
    defects = relationship("Defect", back_populates="aircraft")


class Sortie(Base):
    """A single training flight."""
    __tablename__ = "sorties"

    id = Column(Integer, primary_key=True)
    sortie_number = Column(String(30), unique=True, nullable=False)
    cadet_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False)
    base_id = Column(Integer, ForeignKey("bases.id"), nullable=False)
    lesson_type = Column(String(50), nullable=False)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    status = Column(SAEnum(SortieStatus), default=SortieStatus.SCHEDULED, nullable=False)
    delay_minutes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    cadet = relationship("User", foreign_keys=[cadet_id])
    instructor = relationship("User", foreign_keys=[instructor_id])
    aircraft = relationship("Aircraft")
    base = relationship("BaseLocation")
    training = relationship("TrainingProgress", back_populates="sortie", uselist=False)


class TrainingProgress(Base):
    """One training-progress record per sortie."""
    __tablename__ = "training_progress"

    id = Column(Integer, primary_key=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), unique=True, nullable=False)
    cadet_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_type = Column(String(50), nullable=False)
    maneuver_score = Column(Integer, nullable=True)
    communication_score = Column(Integer, nullable=True)
    situational_awareness_score = Column(Integer, nullable=True)
    remarks = Column(Text, nullable=True)
    status = Column(SAEnum(TrainingStatus), default=TrainingStatus.DRAFT, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    sortie = relationship("Sortie", back_populates="training")


class Defect(Base):
    """A reported issue with an aircraft. While OPEN, the aircraft is grounded."""
    __tablename__ = "defects"

    id = Column(Integer, primary_key=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=True)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    severity = Column(SAEnum(DefectSeverity), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SAEnum(DefectStatus), default=DefectStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    aircraft = relationship("Aircraft", back_populates="defects")


class AuditLog(Base):
    """
    Records every important action. Once written, never modified.
    Helps prove who did what and when (regulators need this in aviation).
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)        # e.g. SORTIE_RELEASED
    entity_type = Column(String(50), nullable=False)   # e.g. Sortie, Aircraft
    entity_id = Column(Integer, nullable=False)
    old_value = Column(Text, nullable=True)            # JSON string of previous state
    new_value = Column(Text, nullable=True)            # JSON string of new state
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
