"""Defect routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Defect, User, UserRole
from app.schemas.schemas import DefectCreate, DefectRead
from app.core.security import get_current_user, require_roles
from app.services import aircraft_service

router = APIRouter(prefix="/defects", tags=["defects"])


@router.post("", response_model=DefectRead, status_code=201)
def create(payload: DefectCreate,
           db: Session = Depends(get_db),
           actor: User = Depends(require_roles(UserRole.MAINTENANCE_OFFICER, UserRole.INSTRUCTOR))):
    return aircraft_service.create_defect(db, actor, payload)


@router.get("", response_model=List[DefectRead])
def list_defects(db: Session = Depends(get_db),
                 _: User = Depends(get_current_user)):
    return db.query(Defect).order_by(Defect.created_at.desc()).all()


@router.get("/{defect_id}", response_model=DefectRead)
def get_defect(defect_id: int,
               db: Session = Depends(get_db),
               _: User = Depends(get_current_user)):
    d = db.query(Defect).filter(Defect.id == defect_id).first()
    if d is None:
        raise HTTPException(status_code=404, detail="Defect not found")
    return d


@router.patch("/{defect_id}/resolve", response_model=DefectRead)
def resolve(defect_id: int,
            db: Session = Depends(get_db),
            actor: User = Depends(require_roles(UserRole.MAINTENANCE_OFFICER))):
    return aircraft_service.resolve_defect(db, actor, defect_id)
