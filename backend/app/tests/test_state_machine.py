"""
Exhaustive state-machine tests.

For each (from_status, action) combination we verify that valid transitions
succeed and invalid ones return HTTP 400 with the right error message.
"""

from app.tests.conftest import headers
from app.db.models import Sortie, SortieStatus, Aircraft


def _set_sortie_status(db, status: SortieStatus):
    s = db.session.query(Sortie).filter(Sortie.id == db.sortie_id).first()
    s.status = status
    db.session.commit()


# ---------- valid transitions ----------

def test_scheduled_to_released_ok(db, client):
    r = client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200


def test_scheduled_to_cancelled_ok(db, client):
    r = client.patch(f"/sorties/{db.sortie_id}/cancel", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"


def test_released_to_airborne_ok(db, client):
    _set_sortie_status(db, SortieStatus.RELEASED)
    r = client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200


def test_released_to_cancelled_ok(db, client):
    _set_sortie_status(db, SortieStatus.RELEASED)
    r = client.patch(f"/sorties/{db.sortie_id}/cancel", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200


def test_airborne_to_landed_ok(db, client):
    _set_sortie_status(db, SortieStatus.AIRBORNE)
    r = client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200


# ---------- invalid transitions ----------

def test_scheduled_to_airborne_rejected(db, client):
    r = client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400
    assert "Invalid state transition" in r.json()["detail"]


def test_scheduled_to_landed_rejected(db, client):
    r = client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400


def test_released_to_landed_rejected(db, client):
    _set_sortie_status(db, SortieStatus.RELEASED)
    r = client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400


def test_landed_cannot_be_re_released(db, client):
    _set_sortie_status(db, SortieStatus.LANDED)
    r = client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400


def test_cancelled_sortie_cannot_be_released(db, client):
    _set_sortie_status(db, SortieStatus.CANCELLED)
    r = client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400


def test_closed_sortie_cannot_be_reopened(db, client):
    _set_sortie_status(db, SortieStatus.CLOSED)
    r = client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400


def test_airborne_cannot_be_cancelled(db, client):
    _set_sortie_status(db, SortieStatus.AIRBORNE)
    r = client.patch(f"/sorties/{db.sortie_id}/cancel", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400


# ---------- close-sortie rules ----------

def test_close_requires_training_approved(db, client):
    """Cannot close from SCHEDULED, RELEASED, AIRBORNE, LANDED, TRAINING_SUBMITTED."""
    for status in (SortieStatus.SCHEDULED, SortieStatus.RELEASED, SortieStatus.AIRBORNE,
                   SortieStatus.LANDED, SortieStatus.TRAINING_SUBMITTED):
        _set_sortie_status(db, status)
        r = client.patch(f"/sorties/{db.sortie_id}/close", headers=headers(db.users["dispatcher"]))
        assert r.status_code == 400, f"Close from {status.value} should fail"


def test_close_succeeds_from_training_approved(db, client):
    """The only valid path to CLOSED is from TRAINING_APPROVED."""
    # Walk full happy path
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    submit = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 5, "communication_score": 4, "situational_awareness_score": 5,
        "remarks": "Excellent.",
    })
    training_id = submit.json()["id"]
    client.patch(f"/training-progress/{training_id}/approve", headers=headers(db.users["cfi"]))

    r = client.patch(f"/sorties/{db.sortie_id}/close", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200
    assert r.json()["status"] == "CLOSED"


# ---------- training reject loops back to LANDED ----------

def test_training_reject_loops_sortie_back_to_landed(db, client):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    submit = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 2, "communication_score": 2, "situational_awareness_score": 2,
        "remarks": "Needs work.",
    })
    tid = submit.json()["id"]

    r = client.patch(
        f"/training-progress/{tid}/reject",
        headers=headers(db.users["cfi"]),
        json={"remarks": "Scores too low for approval"},
    )
    assert r.status_code == 200

    # Sortie should be LANDED again so instructor can resubmit
    s = client.get(f"/sorties/{db.sortie_id}", headers=headers(db.users["admin"])).json()
    assert s["status"] == "LANDED"


# ---------- aircraft status sync ----------

def test_releasing_sortie_marks_aircraft_scheduled(db, client):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    a = db.session.query(Aircraft).filter(Aircraft.id == db.aircraft_ready_id).first()
    db.session.refresh(a)
    assert a.status.value == "SCHEDULED"


def test_airborne_sortie_marks_aircraft_airborne(db, client):
    _set_sortie_status(db, SortieStatus.RELEASED)
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    a = db.session.query(Aircraft).filter(Aircraft.id == db.aircraft_ready_id).first()
    db.session.refresh(a)
    assert a.status.value == "AIRBORNE"


def test_landed_sortie_marks_aircraft_landed(db, client):
    _set_sortie_status(db, SortieStatus.AIRBORNE)
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    a = db.session.query(Aircraft).filter(Aircraft.id == db.aircraft_ready_id).first()
    db.session.refresh(a)
    assert a.status.value == "LANDED"
