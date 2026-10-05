import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Candidate, Hall, SeatPlan
from app.services.seat_engine import CLOSED, find_violations, place_candidates, plan_to_dict, required_state

router = APIRouter(prefix="/seating", tags=["seating"])


def _roster(db: Session, hall_id: int) -> list[dict]:
    return [{"id": c.id, "name": c.name, "ticket_no": c.ticket_no, "paper_id": c.paper_id, "is_key": c.is_key}
            for c in db.scalars(select(Candidate).where(Candidate.hall_id == hall_id)).all()]


@router.post("/run")
def run_seating(hall_id: int = 1, db: Session = Depends(get_db)):
    hall = db.get(Hall, hall_id)
    if not hall:
        raise HTTPException(404, "考室不存在")
    cands = _roster(db, hall_id)
    # State is decided by the roster at this submit instant; never inherited from an old plan.
    state = required_state(cands)
    assigns, unplaced = place_candidates(hall.rows, hall.cols, hall.min_manhattan, cands)
    viols = find_violations(hall.rows, hall.cols, hall.min_manhattan, assigns)
    if state == CLOSED and unplaced:
        # Closed session seats everyone or fails as a whole: no plan is persisted.
        raise HTTPException(409, "封闭场必须全员落座")
    result = plan_to_dict(assigns, unplaced, viols, hall.rows, hall.cols, state=state)
    result["hall"] = {"id": hall.id, "name": hall.name, "min_manhattan": hall.min_manhattan}
    plan = SeatPlan(hall_id=hall_id, created_at=datetime.utcnow(), state=state,
                    result_json=json.dumps(result, ensure_ascii=False))
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"id": plan.id, **result}


@router.get("/latest")
def latest(hall_id: int = 1, db: Session = Depends(get_db)):
    plan = db.scalars(select(SeatPlan).where(SeatPlan.hall_id == hall_id).order_by(SeatPlan.id.desc())).first()
    current = required_state(_roster(db, hall_id))
    if not plan or plan.state != current:
        # Key marks changed since the stored plan: the old graph is stale, recompute now.
        return run_seating(hall_id=hall_id, db=db)
    data = json.loads(plan.result_json)
    return {"id": plan.id, **data}


@router.get("/violations")
def violations(hall_id: int = 1, db: Session = Depends(get_db)):
    data = latest(hall_id=hall_id, db=db)
    return {"hall_id": hall_id, "state": data.get("state"),
            "violations": data.get("violations", []), "unplaced": data.get("unplaced", [])}


@router.get("/stats")
def stats(hall_id: int = 1, db: Session = Depends(get_db)):
    data = latest(hall_id=hall_id, db=db)
    return {"hall_id": hall_id, "state": data.get("state"), **data.get("stats", {})}
