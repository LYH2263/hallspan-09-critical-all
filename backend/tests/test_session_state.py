import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.models import Candidate, SeatPlan
from app.services.seed import seed_if_empty

CLOSED_MSG = "封闭场必须全员落座"


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    with TestClient(app) as c:
        yield c


def _plan_count() -> int:
    db = SessionLocal()
    try:
        return db.scalar(select(func.count()).select_from(SeatPlan)) or 0
    finally:
        db.close()


def _clear_all_key_marks(client: TestClient) -> None:
    for c in client.get("/api/candidates").json():
        assert client.patch(f"/api/candidates/{c['id']}", json={"is_key": False}).status_code == 200


def _drop_candidates(keep: int) -> None:
    db = SessionLocal()
    try:
        ids = db.scalars(select(Candidate.id).order_by(Candidate.id)).all()
        db.execute(delete(Candidate).where(Candidate.id.in_(ids[keep:])))
        db.commit()
    finally:
        db.close()


def test_seeded_closed_session_fails_without_plan(client):
    keys = [c for c in client.get("/api/candidates").json() if c["is_key"]]
    assert len(keys) == 1  # seed marks exactly one key candidate

    res = client.post("/api/seating/run?hall_id=1")
    assert res.status_code == 409
    assert res.json()["detail"] == CLOSED_MSG
    assert _plan_count() == 0  # whole session failed: no plan added

    stats = client.get("/api/seating/stats?hall_id=1")
    assert stats.status_code == 409
    assert stats.json()["detail"] == CLOSED_MSG
    assert _plan_count() == 0


def test_open_session_allows_partial_unplaced(client):
    _clear_all_key_marks(client)
    res = client.post("/api/seating/run?hall_id=1")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "open"
    assert body["stats"]["seated"] == 15
    assert body["stats"]["unplaced"] == 1  # tight grid: live unplaced allowed only in open session
    assert len(body["unplaced"]) == 1
    assert _plan_count() == 1

    stats = client.get("/api/seating/stats?hall_id=1").json()
    assert stats["state"] == "open"
    assert stats["unplaced"] == 1


def test_marking_key_invalidates_old_open_graph(client):
    _clear_all_key_marks(client)
    assert client.post("/api/seating/run?hall_id=1").json()["state"] == "open"
    assert _plan_count() == 1

    cand = client.get("/api/candidates").json()[0]
    assert client.patch(f"/api/candidates/{cand['id']}", json={"is_key": True}).status_code == 200

    # Next submit instant switches to closed; the stale open graph must not be served.
    res = client.get("/api/seating/latest?hall_id=1")
    assert res.status_code == 409
    assert res.json()["detail"] == CLOSED_MSG
    assert _plan_count() == 1  # failed closed run adds no plan


def test_closed_session_success_has_zero_unplaced(client):
    _drop_candidates(keep=15)  # one key remains; 15 seats are exactly enough
    res = client.post("/api/seating/run?hall_id=1")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "closed"
    assert body["stats"]["unplaced"] == 0  # closed is never half-closed
    assert body["unplaced"] == []

    db = SessionLocal()
    try:
        plan = db.scalars(select(SeatPlan).order_by(SeatPlan.id.desc())).first()
        assert plan.state == "closed"
    finally:
        db.close()


def test_unmarking_key_switches_back_to_open(client):
    _drop_candidates(keep=15)
    assert client.post("/api/seating/run?hall_id=1").json()["state"] == "closed"
    plans_after_closed = _plan_count()

    _clear_all_key_marks(client)
    res = client.get("/api/seating/latest?hall_id=1")
    assert res.status_code == 200
    assert res.json()["state"] == "open"  # mutually exclusive states, switched at next submit
    assert _plan_count() == plans_after_closed + 1
