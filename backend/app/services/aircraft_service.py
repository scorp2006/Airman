"""
Aircraft service: ground / mark ready actions, defect handling.

Rules:
  - Aircraft can only be marked READY if NO OPEN defects exist.
  - Creating a defect automatically grounds the aircraft.
  - Resolving the last open defect does NOT auto-ready (Maintenance still does final check).
"""

from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import (
    Aircraft,
    AircraftStatus,
    Defect,
    DefectStatus,
    User,
    UserRole,
    Sortie,
    SortieStatus,
)
from app.services.audit_service import write_audit


def _get_aircraft(db: Session, aircraft_id: int) -> Aircraft:
    a = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if a is None:
        raise HTTPException(status_code=404, detail="Aircraft not found")
    return a


def ground_aircraft(db: Session, actor: User, aircraft_id: int) -> Aircraft:
    """Maintenance officer grounds an aircraft."""
    aircraft = _get_aircraft(db, aircraft_id)
    old = {"status": aircraft.status.value}
    aircraft.status = AircraftStatus.GROUNDED
    write_audit(db, actor.id, "AIRCRAFT_GROUNDED", "Aircraft", aircraft.id,
                old_value=old, new_value={"status": aircraft.status.value})
    db.commit()
    db.refresh(aircraft)
    return aircraft


def mark_ready(db: Session, actor: User, aircraft_id: int) -> Aircraft:
    """Maintenance officer marks aircraft ready - only if no OPEN defects."""
    aircraft = _get_aircraft(db, aircraft_id)

    open_count = db.query(Defect).filter(
        Defect.aircraft_id == aircraft.id,
        Defect.status == DefectStatus.OPEN,
    ).count()
    if open_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mark aircraft READY - {open_count} open defect(s) remain",
        )

    old = {"status": aircraft.status.value}
    aircraft.status = AircraftStatus.READY
    write_audit(db, actor.id, "AIRCRAFT_READY", "Aircraft", aircraft.id,
                old_value=old, new_value={"status": aircraft.status.value})
    db.commit()
    db.refresh(aircraft)
    return aircraft


def create_defect(db: Session, actor: User, data) -> Defect:
    """Report a defect. Aircraft auto-grounds."""
    aircraft = _get_aircraft(db, data.aircraft_id)

    defect = Defect(
        aircraft_id=data.aircraft_id,
        sortie_id=data.sortie_id,
        reported_by=actor.id,
        severity=data.severity,
        description=data.description,
        status=DefectStatus.OPEN,
    )
    db.add(defect)
    db.flush()

    # Grounding the aircraft is the most important side effect.
    aircraft_old = {"status": aircraft.status.value}
    aircraft.status = AircraftStatus.GROUNDED

    # If the defect is tied to a sortie that just landed, mark sortie AIRCRAFT_GROUNDED.
    if data.sortie_id is not None:
        sortie = db.query(Sortie).filter(Sortie.id == data.sortie_id).first()
        if sortie is not None and sortie.status == SortieStatus.LANDED:
            sortie.status = SortieStatus.AIRCRAFT_GROUNDED

    write_audit(db, actor.id, "DEFECT_CREATED", "Defect", defect.id,
                new_value={"aircraft_id": defect.aircraft_id, "severity": defect.severity.value})
    write_audit(db, actor.id, "AIRCRAFT_GROUNDED", "Aircraft", aircraft.id,
                old_value=aircraft_old, new_value={"status": aircraft.status.value})
    db.commit()
    db.refresh(defect)
    return defect


def resolve_defect(db: Session, actor: User, defect_id: int) -> Defect:
    """Resolve a defect. Aircraft stays GROUNDED until mark_ready is called."""
    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    if defect is None:
        raise HTTPException(status_code=404, detail="Defect not found")
    if defect.status == DefectStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Defect already resolved")

    old = {"status": defect.status.value}
    defect.status = DefectStatus.RESOLVED

    write_audit(db, actor.id, "DEFECT_RESOLVED", "Defect", defect.id,
                old_value=old, new_value={"status": defect.status.value})
    db.commit()
    db.refresh(defect)
    return defect
