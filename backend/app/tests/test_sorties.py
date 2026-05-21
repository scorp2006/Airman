"""Tests for the 10 required scenarios from section 11 of the spec."""

from app.tests.conftest import headers
from app.db.models import (
    Sortie, SortieStatus, Aircraft, AircraftStatus, TrainingProgress, TrainingStatus,
    Defect, AuditLog,
)


# ---------- 1. Dispatcher can release a SCHEDULED sortie ----------
def test_dispatcher_can_release_scheduled_sortie(db, client):
    r = client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200
    assert r.json()["status"] == "RELEASED"


# ---------- 2. Cadet CANNOT release a sortie ----------
def test_cadet_cannot_release_sortie(db, client):
    r = client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["cadet"]))
    assert r.status_code == 403


# ---------- 3. Cannot mark SCHEDULED sortie AIRBORNE directly ----------
def test_cannot_skip_states_scheduled_to_airborne(db, client):
    r = client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400
    assert "Invalid state transition" in r.json()["detail"]


# ---------- 4. Grounded aircraft cannot be released ----------
def test_grounded_aircraft_cannot_be_released(db, client):
    # Re-point the sortie to the grounded aircraft.
    s = db.session.query(Sortie).filter(Sortie.id == db.sortie_id).first()
    s.aircraft_id = db.aircraft_grounded_id
    db.session.commit()

    r = client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400
    assert "grounded" in r.json()["detail"].lower()


# ---------- 5. Instructor CAN submit training progress (after landing) ----------
def test_instructor_can_submit_training_progress(db, client):
    # Walk the sortie to LANDED first.
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))

    payload = {
        "sortie_id": db.sortie_id,
        "maneuver_score": 4, "communication_score": 3, "situational_awareness_score": 4,
        "remarks": "Solid effort.",
    }
    r = client.post("/training-progress", headers=headers(db.users["instructor"]), json=payload)
    assert r.status_code == 201
    assert r.json()["status"] == "SUBMITTED"


# ---------- 6. Cadet CANNOT submit training progress ----------
def test_cadet_cannot_submit_training_progress(db, client):
    payload = {
        "sortie_id": db.sortie_id,
        "maneuver_score": 4, "communication_score": 3, "situational_awareness_score": 4,
        "remarks": "Trying.",
    }
    r = client.post("/training-progress", headers=headers(db.users["cadet"]), json=payload)
    assert r.status_code == 403


# ---------- 7. CFI can approve training progress ----------
def test_cfi_can_approve_training_progress(db, client):
    # Get sortie to LANDED and submit progress.
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    submit = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id, "maneuver_score": 5, "communication_score": 4,
        "situational_awareness_score": 5, "remarks": "Excellent.",
    })
    training_id = submit.json()["id"]

    r = client.patch(f"/training-progress/{training_id}/approve", headers=headers(db.users["cfi"]))
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"


# ---------- 8. Sortie cannot close before CFI approval ----------
def test_sortie_cannot_close_before_approval(db, client):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id, "maneuver_score": 5, "communication_score": 4,
        "situational_awareness_score": 5, "remarks": "Excellent.",
    })
    # Attempt to close while only SUBMITTED, not APPROVED.
    r = client.patch(f"/sorties/{db.sortie_id}/close", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400


# ---------- 9. Aircraft becomes GROUNDED when defect is reported ----------
def test_aircraft_grounded_when_defect_created(db, client):
    payload = {
        "aircraft_id": db.aircraft_ready_id,
        "severity": "HIGH",
        "description": "Engine surging during run-up.",
    }
    r = client.post("/defects", headers=headers(db.users["maint"]), json=payload)
    assert r.status_code == 201

    aircraft = db.session.query(Aircraft).filter(Aircraft.id == db.aircraft_ready_id).first()
    db.session.refresh(aircraft)
    assert aircraft.status == AircraftStatus.GROUNDED


# ---------- 10. Audit log is created for sortie release ----------
def test_audit_log_created_for_sortie_release(db, client):
    before = db.session.query(AuditLog).filter(AuditLog.action == "SORTIE_RELEASED").count()
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    after = db.session.query(AuditLog).filter(AuditLog.action == "SORTIE_RELEASED").count()
    assert after == before + 1
