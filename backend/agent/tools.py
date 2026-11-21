"""Tools the agent can call. Each returns a small JSON-safe dict."""

from datetime import date, datetime, timedelta
from typing import Optional

from langchain_core.tools import tool
from sqlmodel import Session
from thefuzz import fuzz, process

from backend.database import session_scope
from backend.models import Category, Priority, Todo
from backend.schemas import TodoCreate, TodoUpdate
from backend.services import (
    as_dict,
    clear_todos,
    create_todo,
    delete_todo,
    list_todos,
    update_todo,
)


def _as_priority(value: Optional[str]) -> Priority:
    try:
        return Priority(str(value).strip().capitalize())
    except ValueError:
        return Priority.MEDIUM


def _as_category(value: Optional[str]) -> Category:
    for category in Category:
        if str(value).strip().lower() == category.value.lower():
            return category
    return Category.GENERAL


def _as_date(value: Optional[str]) -> Optional[date]:
    """Accept ISO dates plus the short forms a model tends to produce."""
    text = str(value or "").strip().lower()
    if not text:
        return None

    today = date.today()
    if text in {"today", "now"}:
        return today
    if text == "tomorrow":
        return today + timedelta(days=1)
    if text == "yesterday":
        return today - timedelta(days=1)

    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if text in weekdays:
        ahead = (weekdays.index(text) - today.weekday()) % 7 or 7
        return today + timedelta(days=ahead)

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d %b", "%d %B", "%b %d", "%B %d"):
        try:
            parsed = datetime.strptime(text, fmt).date()
        except ValueError:
            continue
        return parsed.replace(year=today.year) if parsed.year == 1900 else parsed

    return None


def _resolve(session: Session, identifier: str) -> Optional[Todo]:
    """Find a task by id or by approximate wording."""
    key = str(identifier or "").strip().lstrip("#").strip()
    if not key:
        return None

    if key.isdigit():
        todo = session.get(Todo, int(key))
        if todo:
            return todo

    todos = list_todos(session)
    if not todos:
        return None

    match, score = process.extractOne(key, [t.text for t in todos], scorer=fuzz.WRatio)
    if match and score >= 60:
        return next(t for t in todos if t.text == match)
    return None


def _missing(identifier: str) -> dict:
    return {
        "success": False,
        "action": "not_found",
        "message": f"No task matches “{identifier}”.",
    }


@tool
def create_todo_tool(
    text: str,
    priority: str = "Medium",
    due_date: Optional[str] = None,
    category: str = "General",
) -> dict:
    """Add a task.

    Args:
        text: What needs doing.
        priority: Low, Medium or High.
        due_date: Due date as YYYY-MM-DD.
        category: University, Tech Projects, Watchlist, Personal, Work or General.
    """
    text = (text or "").strip()
    if not text:
        return {"success": False, "action": "noop", "message": "The task text was empty."}

    with session_scope() as session:
        todo = create_todo(
            session,
            TodoCreate(
                text=text[:500],
                priority=_as_priority(priority),
                category=_as_category(category),
                due_date=_as_date(due_date),
            ),
        )
        return {
            "success": True,
            "action": "created",
            "message": f"Added “{todo.text}”.",
            "todo": as_dict(todo),
        }


@tool
def update_todo_tool(
    identifier: str,
    new_text: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    category: Optional[str] = None,
    completed: Optional[bool] = None,
) -> dict:
    """Change an existing task.

    Args:
        identifier: Task id or the task's wording.
        new_text: Replacement text, if the wording changes.
        priority: Low, Medium or High.
        due_date: Due date as YYYY-MM-DD.
        category: University, Tech Projects, Watchlist, Personal, Work or General.
        completed: True to mark done, False to reopen.
    """
    with session_scope() as session:
        todo = _resolve(session, identifier)
        if not todo:
            return _missing(identifier)

        changes = TodoUpdate()
        if new_text is not None and new_text.strip():
            changes.text = new_text.strip()[:500]
        if priority is not None:
            changes.priority = _as_priority(priority)
        if category is not None:
            changes.category = _as_category(category)
        if due_date is not None:
            changes.due_date = _as_date(due_date)
        if completed is not None:
            changes.completed = completed

        if not changes.model_fields_set:
            return {"success": True, "action": "noop", "message": "Nothing to change."}

        todo = update_todo(session, todo, changes)
        return {
            "success": True,
            "action": "updated",
            "message": f"Updated “{todo.text}”.",
            "todo": as_dict(todo),
        }


@tool
def complete_todo_tool(identifier: str, completed: bool = True) -> dict:
    """Mark a task done, or reopen it with completed=False.

    Args:
        identifier: Task id or the task's wording.
        completed: True marks done. False reopens.
    """
    with session_scope() as session:
        todo = _resolve(session, identifier)
        if not todo:
            return _missing(identifier)

        todo = update_todo(session, todo, TodoUpdate(completed=completed))
        verb = "Completed" if completed else "Reopened"
        return {
            "success": True,
            "action": "completed" if completed else "reopened",
            "message": f"{verb} “{todo.text}”.",
            "todo": as_dict(todo),
        }


@tool
def delete_todo_tool(identifier: str) -> dict:
    """Delete one task.

    Args:
        identifier: Task id or the task's wording.
    """
    with session_scope() as session:
        todo = _resolve(session, identifier)
        if not todo:
            return _missing(identifier)

        text = todo.text
        delete_todo(session, todo)
        return {"success": True, "action": "deleted", "message": f"Deleted “{text}”."}


@tool
def clear_todos_tool() -> dict:
    """Delete every task. Only use when the user asks to clear the whole list."""
    with session_scope() as session:
        count = clear_todos(session)
    return {
        "success": True,
        "action": "cleared",
        "message": f"Cleared {count} task{'s' if count != 1 else ''}.",
    }


@tool
def list_todos_tool() -> dict:
    """List every task with its id, status, priority and category."""
    with session_scope() as session:
        todos = list_todos(session)
        return {
            "success": True,
            "action": "listed",
            "message": f"{len(todos)} task{'s' if len(todos) != 1 else ''} on the list.",
            "todos": [as_dict(t) for t in todos],
        }


tools = [
    create_todo_tool,
    update_todo_tool,
    complete_todo_tool,
    delete_todo_tool,
    clear_todos_tool,
    list_todos_tool,
]
