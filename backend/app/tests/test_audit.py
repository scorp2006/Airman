"""
Audit log tests.

Every important action must write an audit log row in the same transaction
as the change. We verify both that rows are written and the filter API works.
"""

from app.tests.conftest import headers
from app.db.models import AuditLog


def _count_audit(db, action: str) -> int:
    return db.session.query(AuditLog).filter(AuditLog.action == action).count()


def _walk_to_landed(client, db):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))


# ---------- audit row created for each action ----------

def test_audit_for_sortie_creation(db, client):
    before = _count_audit(db, "SORTIE_CREATED")
    client.post("/sorties", headers=headers(db.users["dispatcher"]), json={
        "sortie_number": "AUD-001",
        "cadet_id": db.users["cadet"],
        "instructor_id": db.users["instructor"],
        "aircraft_id": db.aircraft_ready_id,
        "base_id": 1,
        "lesson_type": "Test",
        "scheduled_start": "2026-12-31T10:00:00",
        "scheduled_end": "2026-12-31T11:00:00",
    })
    assert _count_audit(db, "SORTIE_CREATED") == before + 1


def test_audit_for_sortie_airborne(db, client):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    before = _count_audit(db, "SORTIE_AIRBORNE")
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    assert _count_audit(db, "SORTIE_AIRBORNE") == before + 1


def test_audit_for_sortie_landed(db, client):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    before = _count_audit(db, "SORTIE_LANDED")
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    assert _count_audit(db, "SORTIE_LANDED") == before + 1


def test_audit_for_sortie_cancelled(db, client):
    before = _count_audit(db, "SORTIE_CANCELLED")
    client.patch(f"/sorties/{db.sortie_id}/cancel", headers=headers(db.users["dispatcher"]))
    assert _count_audit(db, "SORTIE_CANCELLED") == before + 1


def test_audit_for_sortie_closed(db, client):
    _walk_to_landed(client, db)
    submit = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 5, "communication_score": 4, "situational_awareness_score": 5,
        "remarks": "x.",
    })
    client.patch(f"/training-progress/{submit.json()['id']}/approve", headers=headers(db.users["cfi"]))

    before = _count_audit(db, "SORTIE_CLOSED")
    client.patch(f"/sorties/{db.sortie_id}/close", headers=headers(db.users["dispatcher"]))
    assert _count_audit(db, "SORTIE_CLOSED") == before + 1


def test_audit_for_aircraft_grounded(db, client):
    before = _count_audit(db, "AIRCRAFT_GROUNDED")
    client.patch(f"/aircraft/{db.aircraft_ready_id}/ground", headers=headers(db.users["maint"]))
    assert _count_audit(db, "AIRCRAFT_GROUNDED") == before + 1


def test_audit_for_aircraft_ready(db, client):
    """Mark ready (no defects on aircraft_ready_id) -> audit row."""
    # First ground it
    client.patch(f"/aircraft/{db.aircraft_ready_id}/ground", headers=headers(db.users["maint"]))
    before = _count_audit(db, "AIRCRAFT_READY")
    client.patch(f"/aircraft/{db.aircraft_ready_id}/ready", headers=headers(db.users["maint"]))
    assert _count_audit(db, "AIRCRAFT_READY") == before + 1


def test_audit_for_training_submitted(db, client):
    _walk_to_landed(client, db)
    before = _count_audit(db, "TRAINING_SUBMITTED")
    client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 4, "communication_score": 3, "situational_awareness_score": 4,
        "remarks": "x.",
    })
    assert _count_audit(db, "TRAINING_SUBMITTED") == before + 1


def test_audit_for_training_approved(db, client):
    _walk_to_landed(client, db)
    submit = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 4, "communication_score": 3, "situational_awareness_score": 4,
        "remarks": "x.",
    })
    before = _count_audit(db, "TRAINING_APPROVED")
    client.patch(f"/training-progress/{submit.json()['id']}/approve", headers=headers(db.users["cfi"]))
    assert _count_audit(db, "TRAINING_APPROVED") == before + 1


def test_audit_for_training_rejected(db, client):
    _walk_to_landed(client, db)
    submit = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 2, "communication_score": 2, "situational_awareness_score": 2,
        "remarks": "low.",
    })
    before = _count_audit(db, "TRAINING_REJECTED")
    client.patch(
        f"/training-progress/{submit.json()['id']}/reject",
        headers=headers(db.users["cfi"]),
        json={"remarks": "Scores too low."},
    )
    assert _count_audit(db, "TRAINING_REJECTED") == before + 1


def test_audit_for_defect_created(db, client):
    before = _count_audit(db, "DEFECT_CREATED")
    client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "LOW",
        "description": "Test",
    })
    assert _count_audit(db, "DEFECT_CREATED") == before + 1


def test_audit_for_defect_resolved(db, client):
    create = client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "LOW",
        "description": "x",
    })
    before = _count_audit(db, "DEFECT_RESOLVED")
    client.patch(f"/defects/{create.json()['id']}/resolve", headers=headers(db.users["maint"]))
    assert _count_audit(db, "DEFECT_RESOLVED") == before + 1


# ---------- audit log filter API ----------

def test_audit_filter_by_entity_type(db, client):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    r = client.get("/audit-logs", headers=headers(db.users["admin"]), params={"entity_type": "Sortie"})
    assert r.status_code == 200
    assert all(log["entity_type"] == "Sortie" for log in r.json())


def test_audit_filter_by_action(db, client):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    r = client.get("/audit-logs", headers=headers(db.users["admin"]), params={"action": "SORTIE_RELEASED"})
    assert r.status_code == 200
    assert all(log["action"] == "SORTIE_RELEASED" for log in r.json())


def test_audit_filter_by_actor(db, client):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    r = client.get("/audit-logs", headers=headers(db.users["admin"]), params={"actor_id": db.users["dispatcher"]})
    assert r.status_code == 200
    assert all(log["actor_id"] == db.users["dispatcher"] for log in r.json())


def test_audit_log_records_actor_id_correctly(db, client):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    r = client.get("/audit-logs", headers=headers(db.users["admin"]), params={"action": "SORTIE_RELEASED"})
    most_recent = r.json()[0]
    assert most_recent["actor_id"] == db.users["dispatcher"]


def test_audit_log_records_old_and_new_values(db, client):
    """Sortie release should record old=SCHEDULED, new=RELEASED."""
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    r = client.get("/audit-logs", headers=headers(db.users["admin"]), params={"action": "SORTIE_RELEASED"})
    most_recent = r.json()[0]
    assert "SCHEDULED" in (most_recent["old_value"] or "")
    assert "RELEASED" in (most_recent["new_value"] or "")
