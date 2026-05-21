"""Training-progress routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import TrainingProgress, User, UserRole
from app.schemas.schemas import TrainingProgressCreate, TrainingProgressRead, RejectRequest
from app.core.security import get_current_user, require_roles
from app.services import training_service

router = APIRouter(prefix="/training-progress", tags=["training-progress"])


@router.post("", response_model=TrainingProgressRead, status_code=201)
def submit(payload: TrainingProgressCreate,
           db: Session = Depends(get_db),
           actor: User = Depends(require_roles(UserRole.INSTRUCTOR))):
    """Instructor submits training scores. Goes straight to SUBMITTED status."""
    return training_service.submit_training(db, actor, payload)


@router.get("/{sortie_id}", response_model=TrainingProgressRead)
def get_by_sortie(sortie_id: int,
                  db: Session = Depends(get_db),
                  current: User = Depends(get_current_user)):
    t = db.query(TrainingProgress).filter(TrainingProgress.sortie_id == sortie_id).first()
    if t is None:
        raise HTTPException(status_code=404, detail="No training progress for this sortie")
    # Cadet RBAC: can only see their own.
    if current.role == UserRole.CADET and t.cadet_id != current.id:
        raise HTTPException(status_code=403, detail="Cannot view another cadet's progress")
    return t


@router.patch("/{training_id}/submit", response_model=TrainingProgressRead)
def submit_existing(training_id: int,
                    db: Session = Depends(get_db),
                    actor: User = Depends(require_roles(UserRole.INSTRUCTOR))):
    """Alternate endpoint kept for spec compliance - same effect as POST when scores already exist."""
    t = db.query(TrainingProgress).filter(TrainingProgress.id == training_id).first()
    if t is None:
        raise HTTPException(status_code=404, detail="Training progress not found")
    if actor.role != UserRole.ADMIN and t.instructor_id != actor.id:
        raise HTTPException(status_code=403, detail="Not your training record")
    # Build a payload-like object from the existing row.
    class _P:
        sortie_id = t.sortie_id
        maneuver_score = t.maneuver_score
        communication_score = t.communication_score
        situational_awareness_score = t.situational_awareness_score
        remarks = t.remarks or "Resubmitted"
    return training_service.submit_training(db, actor, _P)


@router.patch("/{training_id}/approve", response_model=TrainingProgressRead)
def approve(training_id: int,
            db: Session = Depends(get_db),
            actor: User = Depends(require_roles(UserRole.CFI))):
    return training_service.approve_training(db, actor, training_id)


@router.patch("/{training_id}/reject", response_model=TrainingProgressRead)
def reject(training_id: int,
           payload: RejectRequest,
           db: Session = Depends(get_db),
           actor: User = Depends(require_roles(UserRole.CFI))):
    return training_service.reject_training(db, actor, training_id, payload.remarks)
