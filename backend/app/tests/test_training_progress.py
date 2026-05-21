"""
Training-progress specific tests beyond the bare RBAC.
"""

from app.tests.conftest import headers
from app.db.models import SortieStatus, TrainingStatus, Sortie


def _walk_to_landed(client, db):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))


def _submit(client, db):
    return client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 4, "communication_score": 3, "situational_awareness_score": 4,
        "remarks": "Solid.",
    })


# ---------- instructor ownership ----------

def test_only_assigned_instructor_can_submit(db, client):
    """A different instructor cannot submit progress for someone else's sortie."""
    _walk_to_landed(client, db)
    # Add a second instructor
    from app.db.models import User, UserRole
    other = User(full_name="Other Instructor", email="other-inst@t.in",
                 role=UserRole.INSTRUCTOR, base_id=1)
    db.session.add(other)
    db.session.commit()

    r = client.post("/training-progress", headers=headers(other.id), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 4, "communication_score": 3, "situational_awareness_score": 4,
        "remarks": "I am not the assigned instructor.",
    })
    assert r.status_code == 403


# ---------- sortie status gating ----------

def test_cannot_submit_training_before_landing(db, client):
    """Sortie must be LANDED to accept training submission."""
    # Sortie is still SCHEDULED
    r = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 4, "communication_score": 3, "situational_awareness_score": 4,
        "remarks": "Early submit.",
    })
    assert r.status_code == 400


# ---------- approve/reject status side-effects ----------

def test_approve_moves_sortie_to_training_approved(db, client):
    _walk_to_landed(client, db)
    tid = _submit(client, db).json()["id"]
    client.patch(f"/training-progress/{tid}/approve", headers=headers(db.users["cfi"]))

    s = db.session.query(Sortie).filter(Sortie.id == db.sortie_id).first()
    db.session.refresh(s)
    assert s.status == SortieStatus.TRAINING_APPROVED


def test_approve_sets_approved_by_and_approved_at(db, client):
    _walk_to_landed(client, db)
    tid = _submit(client, db).json()["id"]
    r = client.patch(f"/training-progress/{tid}/approve", headers=headers(db.users["cfi"]))
    body = r.json()
    assert body["approved_by"] == db.users["cfi"]
    assert body["approved_at"] is not None


def test_reject_requires_remarks(db, client):
    _walk_to_landed(client, db)
    tid = _submit(client, db).json()["id"]
    # Empty remarks
    r = client.patch(
        f"/training-progress/{tid}/reject",
        headers=headers(db.users["cfi"]),
        json={"remarks": ""},
    )
    assert r.status_code == 422


def test_cannot_approve_already_approved(db, client):
    _walk_to_landed(client, db)
    tid = _submit(client, db).json()["id"]
    client.patch(f"/training-progress/{tid}/approve", headers=headers(db.users["cfi"]))
    # Try to approve a second time
    r = client.patch(f"/training-progress/{tid}/approve", headers=headers(db.users["cfi"]))
    assert r.status_code == 400


def test_cannot_reject_already_approved(db, client):
    _walk_to_landed(client, db)
    tid = _submit(client, db).json()["id"]
    client.patch(f"/training-progress/{tid}/approve", headers=headers(db.users["cfi"]))
    r = client.patch(
        f"/training-progress/{tid}/reject",
        headers=headers(db.users["cfi"]),
        json={"remarks": "changed my mind"},
    )
    assert r.status_code == 400


# ---------- training row state on submit ----------

def test_submit_sets_training_status_submitted(db, client):
    _walk_to_landed(client, db)
    r = _submit(client, db)
    assert r.json()["status"] == "SUBMITTED"


def test_submit_records_submitted_at(db, client):
    _walk_to_landed(client, db)
    r = _submit(client, db)
    assert r.json()["submitted_at"] is not None


# ---------- training rejection adds CFI remarks ----------

def test_rejection_appends_remarks(db, client):
    _walk_to_landed(client, db)
    tid = _submit(client, db).json()["id"]
    client.patch(
        f"/training-progress/{tid}/reject",
        headers=headers(db.users["cfi"]),
        json={"remarks": "Communication needs work"},
    )

    # Fetch training back and confirm the rejection note was appended
    g = client.get(f"/training-progress/{db.sortie_id}", headers=headers(db.users["admin"]))
    assert g.status_code == 200
    assert "CFI REJECTION" in g.json()["remarks"]
    assert "Communication needs work" in g.json()["remarks"]


# ---------- get training-progress by sortie ----------

def test_cadet_can_view_own_training(db, client):
    _walk_to_landed(client, db)
    _submit(client, db)
    r = client.get(f"/training-progress/{db.sortie_id}", headers=headers(db.users["cadet"]))
    assert r.status_code == 200


def test_cadet_cannot_view_others_training(db, client):
    from app.db.models import User, UserRole
    other = User(full_name="Other Cadet 2", email="oth2@t.in", role=UserRole.CADET, base_id=1)
    db.session.add(other)
    db.session.commit()

    _walk_to_landed(client, db)
    _submit(client, db)
    r = client.get(f"/training-progress/{db.sortie_id}", headers=headers(other.id))
    assert r.status_code == 403
