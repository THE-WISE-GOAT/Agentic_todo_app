from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Category(str, Enum):
    UNIVERSITY = "University"
    TECH_PROJECTS = "Tech Projects"
    WATCHLIST = "Watchlist"
    PERSONAL = "Personal"
    WORK = "Work"
    GENERAL = "General"


def now() -> datetime:
    # Naive local time keeps dates readable in the UI and simple in SQLite.
    return datetime.now()


class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text: str = Field(max_length=500)
    completed: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=now, index=True)
    priority: Priority = Field(default=Priority.MEDIUM)
    due_date: date | None = None
    category: Category = Field(default=Category.GENERAL, index=True)
