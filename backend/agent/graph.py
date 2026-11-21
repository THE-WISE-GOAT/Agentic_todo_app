"""LangGraph agent that turns one sentence into todo operations."""

import json
import logging
import time
from datetime import date
from functools import lru_cache

import httpx
from langchain_core.messages import ToolMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from backend.agent.tools import tools
from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from backend.database import session_scope
from backend.services import list_todos

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You manage a single todo list by calling tools.

Today is {today}. Dates use YYYY-MM-DD.

Rules:
- For an existing task, find its id in the list below. Pass either the id or the user's wording as identifier.
- Handle compound requests by calling several tools in one turn.
- Do not claim an action you did not call a tool for.
- Finish with one short sentence for the user.
"""


class AgentUnavailable(RuntimeError):
    pass


_health = {"checked": 0.0, "ok": False}


def agent_status(force: bool = False) -> dict:
    """Cached Ollama check, so the UI can warn before a run fails."""
    if force or time.monotonic() - _health["checked"] > 10:
        try:
            response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=1.2)
            _health.update(checked=time.monotonic(), ok=response.is_success)
        except httpx.HTTPError:
            _health.update(checked=time.monotonic(), ok=False)
    return {"available": _health["ok"], "model": OLLAMA_MODEL, "base_url": OLLAMA_BASE_URL}


def _system_message(_state) -> list:
    with session_scope() as session:
        todos = list_todos(session)

    if todos:
        lines = "\n".join(
            f"#{t.id} {t.text} — {t.priority.value}, {t.category.value}, "
            f"{'done' if t.completed else 'open'}"
            f"{f', due {t.due_date.isoformat()}' if t.due_date else ''}"
            for t in todos
        )
    else:
        lines = "(empty)"

    prompt = SYSTEM_PROMPT.format(today=date.today().isoformat())
    return [("system", f"{prompt}\nCurrent tasks:\n{lines}")]


@lru_cache(maxsize=1)
def get_graph():
    model = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    return create_react_agent(model=model, tools=tools, state_modifier=_system_message)


def _payload(content) -> dict | None:
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except ValueError:
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def _offline() -> AgentUnavailable:
    return AgentUnavailable(
        f"Ollama isn't responding at {OLLAMA_BASE_URL}. "
        f"Start it with `ollama serve`, then `ollama pull {OLLAMA_MODEL}`."
    )


def run_command(command: str) -> dict:
    if not agent_status()["available"]:
        raise _offline()

    try:
        state = get_graph().invoke(
            {"messages": [("user", command)]},
            {"recursion_limit": 20},
        )
    except httpx.HTTPError as exc:
        _health["ok"] = False
        log.warning("Ollama request failed: %s", exc)
        raise _offline() from exc

    steps = []
    for message in state.get("messages", []):
        if isinstance(message, ToolMessage):
            data = _payload(message.content)
            if data:
                steps.append(data)

    if steps:
        last = steps[-1]
        messages = [s["message"] for s in steps if s.get("message")]
        return {
            "ok": all(bool(s.get("success")) for s in steps),
            "action": last.get("action", "none"),
            "message": " · ".join(messages) or "Done.",
            "todo": last.get("todo"),
            "todos": last.get("todos"),
            "steps": [
                {
                    "ok": bool(s.get("success")),
                    "action": s.get("action", "none"),
                    "message": s.get("message", ""),
                }
                for s in steps
            ],
        }

    reply = state.get("messages", [])
    text = getattr(reply[-1], "content", "") if reply else ""
    return {
        "ok": True,
        "action": "none",
        "message": str(text).strip() or "Nothing to change.",
        "steps": [],
    }
