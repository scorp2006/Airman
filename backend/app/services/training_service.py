"""
Training-progress service: instructors submit scores, CFI approves/rejects.

Rules enforced here:
  - Only the assigned instructor of the sortie may create/submit progress.
  - Sortie must be in LANDED status before training is submitted.
  - When SUBMITTED, sortie moves to TRAINING_SUBMITTED.
  - Only a CFI may APPROVE or REJECT.
  - When APPROVED, sortie moves to TRAINING_APPROVED.
  - When REJECTED, sortie goes back to LANDED so the instructor can fix and resubmit.
"""

from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import (
    Sortie,
    SortieStatus,
    TrainingProgress,
    TrainingStatus,
    User,
    UserRole,
)
from app.services.audit_service import write_audit


def _get_training(db: Session, training_id: int) -> TrainingProgress:
    t = db.query(TrainingProgress).filter(TrainingProgress.id == training_id).first()
    if t is None:
        raise HTTPException(status_code=404, detail="Training progress not found")
    return t


def submit_training(db: Session, actor: User, data) -> TrainingProgress:
    """
    Instructor submits training scores for a sortie.
    Creates the row (if missing) and immediately marks it SUBMITTED.
    """
    sortie = db.query(Sortie).filter(Sortie.id == data.sortie_id).first()
    if sortie is None:
        raise HTTPException(status_code=404, detail="Sortie not found")

    # Only the instructor assigned to this sortie can submit.
    if actor.role != UserRole.ADMIN and sortie.instructor_id != actor.id:
        raise HTTPException(
            status_code=403,
            detail="Only the assigned instructor can submit training progress",
        )

    if sortie.status != SortieStatus.LANDED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit training progress while sortie is {sortie.status.value}",
        )

    # Reuse an existing draft row, or create a new one.
    training = db.query(TrainingProgress).filter(TrainingProgress.sortie_id == sortie.id).first()
    if training is None:
        training = TrainingProgress(
            sortie_id=sortie.id,
            cadet_id=sortie.cadet_id,
            instructor_id=sortie.instructor_id,
            lesson_type=sortie.lesson_type,
        )
        db.add(training)

    training.maneuver_score = data.maneuver_score
    training.communication_score = data.communication_score
    training.situational_awareness_score = data.situational_awareness_score
    training.remarks = data.remarks
    training.status = TrainingStatus.SUBMITTED
    training.submitted_at = datetime.utcnow()

    sortie.status = SortieStatus.TRAINING_SUBMITTED

    db.flush()
    write_audit(
        db, actor.id, "TRAINING_SUBMITTED", "TrainingProgress", training.id,
        new_value={
            "sortie_id": sortie.id,
            "maneuver_score": training.maneuver_score,
            "communication_score": training.communication_score,
            "situational_awareness_score": training.situational_awareness_score,
        },
    )
    db.commit()
    db.refresh(training)
    return training


def approve_training(db: Session, actor: User, training_id: int) -> TrainingProgress:
    """CFI approves submitted training. Sortie -> TRAINING_APPROVED."""
    training = _get_training(db, training_id)

    if actor.role not in (UserRole.CFI, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only CFI can approve training progress")

    if training.status != TrainingStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Can only approve SUBMITTED training records")

    old = {"status": training.status.value}
    training.status = TrainingStatus.APPROVED
    training.approved_by = actor.id
    training.approved_at = datetime.utcnow()

    sortie = db.query(Sortie).filter(Sortie.id == training.sortie_id).first()
    sortie.status = SortieStatus.TRAINING_APPROVED

    write_audit(db, actor.id, "TRAINING_APPROVED", "TrainingProgress", training.id,
                old_value=old, new_value={"status": training.status.value})
    db.commit()
    db.refresh(training)
    return training


def reject_training(db: Session, actor: User, training_id: int, remarks: str) -> TrainingProgress:
    """CFI rejects training with a reason. Sortie goes back to LANDED for resubmission."""
    training = _get_training(db, training_id)

    if actor.role not in (UserRole.CFI, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only CFI can reject training progress")

    if training.status != TrainingStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Can only reject SUBMITTED training records")

    old = {"status": training.status.value, "remarks": training.remarks}
    training.status = TrainingStatus.REJECTED
    # Append rejection reason to existing remarks.
    training.remarks = f"{training.remarks}\n\n[CFI REJECTION]: {remarks}"

    sortie = db.query(Sortie).filter(Sortie.id == training.sortie_id).first()
    sortie.status = SortieStatus.LANDED  # allow instructor to resubmit

    write_audit(db, actor.id, "TRAINING_REJECTED", "TrainingProgress", training.id,
                old_value=old, new_value={"status": training.status.value, "remarks": training.remarks})
    db.commit()
    db.refresh(training)
    return training
