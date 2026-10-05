from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Candidate

router = APIRouter(prefix="/candidates", tags=["candidates"])


class KeyMark(BaseModel):
    is_key: bool


def _row(r: Candidate) -> dict:
    return {"id": r.id, "hall_id": r.hall_id, "name": r.name, "ticket_no": r.ticket_no,
            "paper_id": r.paper_id, "is_key": r.is_key}


@router.get("")
def list_candidates(db: Session = Depends(get_db)):
    return [_row(r) for r in db.scalars(select(Candidate).order_by(Candidate.id)).all()]


@router.patch("/{candidate_id}")
def set_key_mark(candidate_id: int, body: KeyMark, db: Session = Depends(get_db)):
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "考生不存在")
    cand.is_key = body.is_key
    db.commit()
    db.refresh(cand)
    return _row(cand)
