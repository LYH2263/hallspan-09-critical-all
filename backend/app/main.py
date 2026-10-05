from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_if_empty


def _ensure_columns() -> None:
    """Backfill columns added after the first schema (no alembic in this project)."""
    insp = inspect(engine)
    with engine.begin() as conn:
        if "is_key" not in {c["name"] for c in insp.get_columns("candidates")}:
            conn.execute(text("ALTER TABLE candidates ADD COLUMN is_key BOOLEAN NOT NULL DEFAULT FALSE"))
        if "state" not in {c["name"] for c in insp.get_columns("seat_plans")}:
            conn.execute(text("ALTER TABLE seat_plans ADD COLUMN state VARCHAR(8) NOT NULL DEFAULT 'open'"))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    if settings.seed_on_empty:
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(title="HallSpan", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
