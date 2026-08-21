from __future__ import annotations
from sqlmodel import SQLModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


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


class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text: str
    completed: bool = Field(default=False)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    priority: Priority = Field(default=Priority.MEDIUM)
    due_date: str | None = None
    category: Category = Field(default=Category.GENERAL)


class TodoCreate(SQLModel):
    text: str
    priority: Priority | None = Priority.MEDIUM
    due_date: str | None = None
    category: Category | None = Category.GENERAL


class TodoUpdate(SQLModel):
    text: str | None = None
    completed: bool | None = None
    priority: Priority | None = None
    due_date: str | None = None
    category: Category | None = None
