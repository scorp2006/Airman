"""Sortie routes - the heart of the workflow."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Sortie, User, UserRole
from app.schemas.schemas import SortieCreate, SortieRead
from app.core.security import get_current_user, require_roles
from app.services import sortie_service

router = APIRouter(prefix="/sorties", tags=["sorties"])


@router.post("", response_model=SortieRead, status_code=201)
def create_sortie(payload: SortieCreate,
                  db: Session = Depends(get_db),
                  actor: User = Depends(require_roles(UserRole.DISPATCHER))):
    return sortie_service.create_sortie(db, actor, payload)


@router.get("", response_model=List[SortieRead])
def list_sorties(db: Session = Depends(get_db),
                 current: User = Depends(get_current_user)):
    """
    Cadets see only their own sorties.
    Instructors see their assigned sorties.
    Everyone else sees all.
    """
    query = db.query(Sortie)
    if current.role == UserRole.CADET:
        query = query.filter(Sortie.cadet_id == current.id)
    elif current.role == UserRole.INSTRUCTOR:
        query = query.filter(Sortie.instructor_id == current.id)
    return query.order_by(Sortie.scheduled_start.desc()).all()


@router.get("/{sortie_id}", response_model=SortieRead)
def get_sortie(sortie_id: int,
               db: Session = Depends(get_db),
               current: User = Depends(get_current_user)):
    s = db.query(Sortie).filter(Sortie.id == sortie_id).first()
    if s is None:
        raise HTTPException(status_code=404, detail="Sortie not found")
    # Cadets can only see their own.
    if current.role == UserRole.CADET and s.cadet_id != current.id:
        raise HTTPException(status_code=403, detail="Cannot view another cadet's sortie")
    return s


@router.patch("/{sortie_id}/release", response_model=SortieRead)
def release(sortie_id: int,
            db: Session = Depends(get_db),
            actor: User = Depends(require_roles(UserRole.DISPATCHER))):
    return sortie_service.release_sortie(db, actor, sortie_id)


@router.patch("/{sortie_id}/airborne", response_model=SortieRead)
def airborne(sortie_id: int,
             db: Session = Depends(get_db),
             actor: User = Depends(require_roles(UserRole.DISPATCHER))):
    return sortie_service.mark_airborne(db, actor, sortie_id)


@router.patch("/{sortie_id}/landed", response_model=SortieRead)
def landed(sortie_id: int,
           db: Session = Depends(get_db),
           actor: User = Depends(require_roles(UserRole.DISPATCHER))):
    return sortie_service.mark_landed(db, actor, sortie_id)


@router.patch("/{sortie_id}/cancel", response_model=SortieRead)
def cancel(sortie_id: int,
           db: Session = Depends(get_db),
           actor: User = Depends(require_roles(UserRole.DISPATCHER))):
    return sortie_service.cancel_sortie(db, actor, sortie_id)


@router.patch("/{sortie_id}/close", response_model=SortieRead)
def close(sortie_id: int,
          db: Session = Depends(get_db),
          actor: User = Depends(require_roles(UserRole.DISPATCHER, UserRole.CFI))):
    return sortie_service.close_sortie(db, actor, sortie_id)
