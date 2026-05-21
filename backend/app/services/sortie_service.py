"""
Sortie service: the state machine for a sortie's lifecycle.

A sortie can only move through valid transitions. We define those transitions in
one place (ALLOWED_TRANSITIONS below) so the rules are easy to read and change.

We also keep the aircraft's status in sync:
  - sortie RELEASED  -> aircraft SCHEDULED
  - sortie AIRBORNE  -> aircraft AIRBORNE
  - sortie LANDED    -> aircraft LANDED (or back to READY if no defect)
"""

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    Sortie,
    SortieStatus,
    Aircraft,
    AircraftStatus,
    TrainingProgress,
    TrainingStatus,
    User,
    Defect,
    DefectStatus,
)
from app.services.audit_service import write_audit


# Map: from_status -> set of allowed to_statuses
ALLOWED_TRANSITIONS = {
    SortieStatus.SCHEDULED: {SortieStatus.RELEASED, SortieStatus.CANCELLED},
    SortieStatus.RELEASED: {SortieStatus.AIRBORNE, SortieStatus.CANCELLED},
    SortieStatus.AIRBORNE: {SortieStatus.LANDED},
    SortieStatus.LANDED: {SortieStatus.TRAINING_SUBMITTED, SortieStatus.AIRCRAFT_GROUNDED},
    SortieStatus.TRAINING_SUBMITTED: {SortieStatus.TRAINING_APPROVED, SortieStatus.LANDED},  # rejection sends back to LANDED
    SortieStatus.TRAINING_APPROVED: {SortieStatus.CLOSED},
}


def _check_transition(current: SortieStatus, target: SortieStatus) -> None:
    """Raise 400 if the requested transition is not allowed."""
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition: {current.value} -> {target.value}",
        )


def _get_sortie(db: Session, sortie_id: int) -> Sortie:
    sortie = db.query(Sortie).filter(Sortie.id == sortie_id).first()
    if sortie is None:
        raise HTTPException(status_code=404, detail="Sortie not found")
    return sortie


def create_sortie(db: Session, actor: User, data) -> Sortie:
    """Create a brand-new sortie in SCHEDULED status."""
    aircraft = db.query(Aircraft).filter(Aircraft.id == data.aircraft_id).first()
    if aircraft is None:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    # Rule: grounded aircraft cannot be assigned to new sorties.
    if aircraft.status == AircraftStatus.GROUNDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule a sortie on a grounded aircraft",
        )

    sortie = Sortie(
        sortie_number=data.sortie_number,
        cadet_id=data.cadet_id,
        instructor_id=data.instructor_id,
        aircraft_id=data.aircraft_id,
        base_id=data.base_id,
        lesson_type=data.lesson_type,
        scheduled_start=data.scheduled_start,
        scheduled_end=data.scheduled_end,
        status=SortieStatus.SCHEDULED,
    )
    db.add(sortie)
    db.flush()  # Get the auto-generated ID before commit.

    write_audit(
        db,
        actor_id=actor.id,
        action="SORTIE_CREATED",
        entity_type="Sortie",
        entity_id=sortie.id,
        new_value={"status": sortie.status.value, "sortie_number": sortie.sortie_number},
    )
    db.commit()
    db.refresh(sortie)
    return sortie


def release_sortie(db: Session, actor: User, sortie_id: int) -> Sortie:
    """SCHEDULED -> RELEASED. Aircraft must not be grounded."""
    sortie = _get_sortie(db, sortie_id)
    _check_transition(sortie.status, SortieStatus.RELEASED)

    aircraft = db.query(Aircraft).filter(Aircraft.id == sortie.aircraft_id).first()
    if aircraft.status == AircraftStatus.GROUNDED:
        raise HTTPException(
            status_code=400,
            detail="Cannot release sortie - aircraft is grounded",
        )

    old = {"status": sortie.status.value}
    sortie.status = SortieStatus.RELEASED
    aircraft.status = AircraftStatus.SCHEDULED

    write_audit(db, actor.id, "SORTIE_RELEASED", "Sortie", sortie.id,
                old_value=old, new_value={"status": sortie.status.value})
    db.commit()
    db.refresh(sortie)
    return sortie


def mark_airborne(db: Session, actor: User, sortie_id: int) -> Sortie:
    """RELEASED -> AIRBORNE. Records actual_start time. Aircraft becomes AIRBORNE."""
    sortie = _get_sortie(db, sortie_id)
    _check_transition(sortie.status, SortieStatus.AIRBORNE)

    aircraft = db.query(Aircraft).filter(Aircraft.id == sortie.aircraft_id).first()
    old = {"status": sortie.status.value}
    sortie.status = SortieStatus.AIRBORNE
    sortie.actual_start = datetime.utcnow()
    aircraft.status = AircraftStatus.AIRBORNE

    # Compute delay (in minutes) if we took off late.
    if sortie.actual_start > sortie.scheduled_start:
        delta = sortie.actual_start - sortie.scheduled_start
        sortie.delay_minutes = int(delta.total_seconds() // 60)

    write_audit(db, actor.id, "SORTIE_AIRBORNE", "Sortie", sortie.id,
                old_value=old, new_value={"status": sortie.status.value, "delay_minutes": sortie.delay_minutes})
    db.commit()
    db.refresh(sortie)
    return sortie


def mark_landed(db: Session, actor: User, sortie_id: int) -> Sortie:
    """AIRBORNE -> LANDED. Records actual_end. Aircraft becomes LANDED."""
    sortie = _get_sortie(db, sortie_id)
    _check_transition(sortie.status, SortieStatus.LANDED)

    aircraft = db.query(Aircraft).filter(Aircraft.id == sortie.aircraft_id).first()
    old = {"status": sortie.status.value}
    sortie.status = SortieStatus.LANDED
    sortie.actual_end = datetime.utcnow()
    aircraft.status = AircraftStatus.LANDED

    write_audit(db, actor.id, "SORTIE_LANDED", "Sortie", sortie.id,
                old_value=old, new_value={"status": sortie.status.value})
    db.commit()
    db.refresh(sortie)
    return sortie


def cancel_sortie(db: Session, actor: User, sortie_id: int) -> Sortie:
    """SCHEDULED or RELEASED -> CANCELLED."""
    sortie = _get_sortie(db, sortie_id)
    if sortie.status not in (SortieStatus.SCHEDULED, SortieStatus.RELEASED):
        raise HTTPException(status_code=400, detail="Can only cancel SCHEDULED or RELEASED sorties")

    old = {"status": sortie.status.value}
    sortie.status = SortieStatus.CANCELLED

    write_audit(db, actor.id, "SORTIE_CANCELLED", "Sortie", sortie.id,
                old_value=old, new_value={"status": sortie.status.value})
    db.commit()
    db.refresh(sortie)
    return sortie


def close_sortie(db: Session, actor: User, sortie_id: int) -> Sortie:
    """
    TRAINING_APPROVED -> CLOSED.
    The training-progress record MUST be APPROVED first - this prevents closing
    a sortie before grading is approved.
    """
    sortie = _get_sortie(db, sortie_id)

    if sortie.status != SortieStatus.TRAINING_APPROVED:
        raise HTTPException(
            status_code=400,
            detail="Cannot close sortie before training progress is approved",
        )

    # Defensive double-check: training row must exist and be APPROVED.
    training = db.query(TrainingProgress).filter(TrainingProgress.sortie_id == sortie.id).first()
    if training is None or training.status != TrainingStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail="Training progress must be approved before closing",
        )

    old = {"status": sortie.status.value}
    sortie.status = SortieStatus.CLOSED

    # If no open defect on this aircraft, return aircraft to READY.
    aircraft = db.query(Aircraft).filter(Aircraft.id == sortie.aircraft_id).first()
    has_open_defect = db.query(Defect).filter(
        Defect.aircraft_id == aircraft.id,
        Defect.status == DefectStatus.OPEN,
    ).first() is not None
    if not has_open_defect and aircraft.status != AircraftStatus.GROUNDED:
        aircraft.status = AircraftStatus.READY

    write_audit(db, actor.id, "SORTIE_CLOSED", "Sortie", sortie.id,
                old_value=old, new_value={"status": sortie.status.value})
    db.commit()
    db.refresh(sortie)
    return sortie
