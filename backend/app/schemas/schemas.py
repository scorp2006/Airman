"""
Pydantic schemas: the shapes of data going IN and OUT of our API.

- Schemas ending in `Create` describe what the client must SEND to create something.
- Schemas ending in `Read` (or no suffix) describe what the API SENDS BACK.

Pydantic validates and converts the data for us, so route handlers can trust the input.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.db.models import (
    UserRole,
    AircraftStatus,
    SortieStatus,
    TrainingStatus,
    DefectSeverity,
    DefectStatus,
)


# ---------- Base / Location ----------

class BaseLocationRead(BaseModel):
    id: int
    name: str
    code: str
    location: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- User ----------

class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    base_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Mock login: pick an email, we look up the user and return them."""
    email: EmailStr


# ---------- Aircraft ----------

class AircraftRead(BaseModel):
    id: int
    registration: str
    aircraft_type: str
    base_id: int
    status: AircraftStatus
    tbo_remaining_hours: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Sortie ----------

class SortieCreate(BaseModel):
    sortie_number: str
    cadet_id: int
    instructor_id: int
    aircraft_id: int
    base_id: int
    lesson_type: str
    scheduled_start: datetime
    scheduled_end: datetime


class SortieRead(BaseModel):
    id: int
    sortie_number: str
    cadet_id: int
    instructor_id: int
    aircraft_id: int
    base_id: int
    lesson_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: SortieStatus
    delay_minutes: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Training Progress ----------

class TrainingProgressCreate(BaseModel):
    """Used by the instructor to create a draft training-progress record."""
    sortie_id: int
    # Scores must be 1..5 per the spec. ge/le = greater/less than or equal.
    maneuver_score: int = Field(ge=1, le=5)
    communication_score: int = Field(ge=1, le=5)
    situational_awareness_score: int = Field(ge=1, le=5)
    # Remarks cannot be empty per the spec. min_length=1 enforces that.
    remarks: str = Field(min_length=1)


class TrainingProgressRead(BaseModel):
    id: int
    sortie_id: int
    cadet_id: int
    instructor_id: int
    lesson_type: str
    maneuver_score: Optional[int]
    communication_score: Optional[int]
    situational_awareness_score: Optional[int]
    remarks: Optional[str]
    status: TrainingStatus
    submitted_at: Optional[datetime]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class RejectRequest(BaseModel):
    """When CFI rejects training progress, they must provide a reason."""
    remarks: str = Field(min_length=1)


# ---------- Defect ----------

class DefectCreate(BaseModel):
    aircraft_id: int
    sortie_id: Optional[int] = None
    severity: DefectSeverity
    description: str = Field(min_length=1)


class DefectRead(BaseModel):
    id: int
    aircraft_id: int
    sortie_id: Optional[int]
    reported_by: int
    severity: DefectSeverity
    description: str
    status: DefectStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Audit Log ----------

class AuditLogRead(BaseModel):
    id: int
    actor_id: int
    action: str
    entity_type: str
    entity_id: int
    old_value: Optional[str]
    new_value: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
