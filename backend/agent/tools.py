from typing import Optional
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import Todo, Priority, Category
from langchain_core.tools import tool
from thefuzz import fuzz, process


def _get_session() -> Session:
    return next(get_session())


def _find_todo_by_text(text: str) -> Optional[Todo]:
    session = _get_session()
    todos = session.exec(select(Todo)).all()
    if not todos:
        return None
    choices = {todo.text: todo for todo in todos}
    best_match, score = process.extractOne(text, choices.keys(), scorer=fuzz.WRatio)
    if best_match and score >= 60:
        return choices[best_match]
    return None


def _find_todo_by_id_or_text(identifier: str) -> Optional[Todo]:
    session = _get_session()
    if identifier.isdigit():
        todo = session.get(Todo, int(identifier))
        if todo:
            return todo
    return _find_todo_by_text(identifier)


@tool
def create_todo_tool(
    text: str,
    priority: str = "Medium",
    due_date: Optional[str] = None,
    category: str = "General",
) -> dict:
    """Create a new todo item.

    Args:
        text: The todo description.
        priority: One of Low, Medium, High.
        due_date: Optional ISO date string (e.g. 2026-08-20).
        category: One of University, Tech Projects, Watchlist, Personal, Work, General.
    """
    session = _get_session()
    try:
        prio = Priority(priority)
    except ValueError:
        prio = Priority.MEDIUM
    try:
        cat = Category(category)
    except ValueError:
        cat = Category.GENERAL

    db_todo = Todo(
        text=text,
        priority=prio,
        due_date=due_date,
        category=cat,
    )
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return {
        "success": True,
        "todo": {
            "id": db_todo.id,
            "text": db_todo.text,
            "completed": db_todo.completed,
            "created_at": db_todo.created_at,
            "priority": db_todo.priority.value,
            "due_date": db_todo.due_date,
            "category": db_todo.category.value,
        },
        "message": f"Created todo: {text}",
    }


@tool
def delete_todo_tool(identifier: str) -> dict:
    """Delete a todo by ID or fuzzy text match.

    Args:
        identifier: Todo ID as string or descriptive text to match.
    """
    session = _get_session()
    todo = _find_todo_by_id_or_text(identifier)
    if not todo:
        return {"success": False, "message": f"Todo matching '{identifier}' not found"}

    deleted_text = todo.text
    session.delete(todo)
    session.commit()
    return {"success": True, "message": f"Deleted todo: {deleted_text}"}


@tool
def update_todo_tool(
    identifier: str,
    new_text: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    category: Optional[str] = None,
    completed: Optional[bool] = None,
) -> dict:
    """Update a todo by ID or fuzzy text match.

    Args:
        identifier: Todo ID as string or descriptive text to match.
        new_text: New description text.
        priority: One of Low, Medium, High.
        due_date: Optional ISO date string.
        category: One of University, Tech Projects, Watchlist, Personal, Work, General.
        completed: True or False.
    """
    session = _get_session()
    todo = _find_todo_by_id_or_text(identifier)
    if not todo:
        return {"success": False, "message": f"Todo matching '{identifier}' not found"}

    if new_text is not None:
        todo.text = new_text
    if priority is not None:
        try:
            todo.priority = Priority(priority)
        except ValueError:
            pass
    if due_date is not None:
        todo.due_date = due_date
    if category is not None:
        try:
            todo.category = Category(category)
        except ValueError:
            pass
    if completed is not None:
        todo.completed = completed

    session.add(todo)
    session.commit()
    session.refresh(todo)
    return {
        "success": True,
        "message": f"Updated todo {todo.id}: '{todo.text}'",
    }


@tool
def complete_todo_tool(identifier: str) -> dict:
    """Mark a todo as completed by ID or fuzzy text match.

    Args:
        identifier: Todo ID as string or descriptive text to match.
    """
    session = _get_session()
    todo = _find_todo_by_id_or_text(identifier)
    if not todo:
        return {"success": False, "message": f"Todo matching '{identifier}' not found"}

    todo.completed = True
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return {"success": True, "message": f"Marked todo as completed: {todo.text}"}


@tool
def delete_all_todos_tool() -> dict:
    """Delete all todo items."""
    session = _get_session()
    todos = session.exec(select(Todo)).all()
    for todo in todos:
        session.delete(todo)
    session.commit()
    return {"success": True, "message": "All todos deleted"}


@tool
def list_todos_tool() -> dict:
    """Get all todos with full details."""
    session = _get_session()
    todos = session.exec(select(Todo)).all()
    return {
        "success": True,
        "todos": [
            {
                "id": t.id,
                "text": t.text,
                "completed": t.completed,
                "created_at": t.created_at,
                "priority": t.priority.value,
                "due_date": t.due_date,
                "category": t.category.value,
            }
            for t in todos
        ],
        "count": len(todos),
    }


tools = [
    create_todo_tool,
    delete_todo_tool,
    update_todo_tool,
    complete_todo_tool,
    delete_all_todos_tool,
    list_todos_tool,
]
