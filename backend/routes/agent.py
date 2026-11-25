import logging

from fastapi import APIRouter, HTTPException

from backend.agent.graph import AgentUnavailable, run_command
from backend.schemas import CommandRequest, CommandResult

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/command", response_model=CommandResult)
def command_route(payload: CommandRequest):
    try:
        return run_command(payload.command)
    except AgentUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Agent command failed")
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc
