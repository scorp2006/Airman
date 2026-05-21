"""Aircraft routes."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Aircraft, User, UserRole
from app.schemas.schemas import AircraftRead
from app.core.security import get_current_user, require_roles
from app.services import aircraft_service

router = APIRouter(prefix="/aircraft", tags=["aircraft"])


@router.get("", response_model=List[AircraftRead])
def list_aircraft(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Aircraft).all()


@router.get("/{aircraft_id}", response_model=AircraftRead)
def get_aircraft(aircraft_id: int, db: Session = Depends(get_db),
                 _: User = Depends(get_current_user)):
    from fastapi import HTTPException
    a = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if a is None:
        raise HTTPException(status_code=404, detail="Aircraft not found")
    return a


@router.patch("/{aircraft_id}/ground", response_model=AircraftRead)
def ground(aircraft_id: int,
           db: Session = Depends(get_db),
           actor: User = Depends(require_roles(UserRole.MAINTENANCE_OFFICER))):
    return aircraft_service.ground_aircraft(db, actor, aircraft_id)


@router.patch("/{aircraft_id}/ready", response_model=AircraftRead)
def ready(aircraft_id: int,
          db: Session = Depends(get_db),
          actor: User = Depends(require_roles(UserRole.MAINTENANCE_OFFICER))):
    return aircraft_service.mark_ready(db, actor, aircraft_id)
