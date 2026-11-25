from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from backend.agent.graph import agent_status
from backend.database import engine, get_session
from backend.models import Category, Priority
from backend.schemas import Meta, Stats
from backend.services import get_stats

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/stats", response_model=Stats)
def stats_route(session: Session = Depends(get_session)):
    return get_stats(session)


@router.get("/meta", response_model=Meta)
def meta_route():
    return {
        "priorities": [p.value for p in Priority],
        "categories": [c.value for c in Category],
        "agent": agent_status(),
    }


@router.get("/health")
def health_route():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unavailable"
    return {"status": "ok", "database": database, "agent": agent_status()}
