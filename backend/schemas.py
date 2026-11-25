from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from backend.models import Category, Priority


class TextFields(SQLModel):
    @field_validator("text", check_fields=False)
    @classmethod
    def _clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Task text cannot be empty")
        return value


class TodoCreate(TextFields):
    text: str = Field(min_length=1, max_length=500)
    priority: Priority = Priority.MEDIUM
    category: Category = Category.GENERAL
    due_date: date | None = None


class TodoUpdate(TextFields):
    text: str | None = Field(default=None, min_length=1, max_length=500)
    completed: bool | None = None
    priority: Priority | None = None
    category: Category | None = None
    due_date: date | None = None


class TodoRead(SQLModel):
    id: int
    text: str
    completed: bool
    created_at: datetime
    priority: Priority
    due_date: date | None
    category: Category


class Stats(SQLModel):
    total: int
    open: int
    done: int
    overdue: int


class CommandRequest(SQLModel):
    command: str = Field(min_length=1, max_length=500)

    @field_validator("command")
    @classmethod
    def _clean(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Command cannot be empty")
        return value


class CommandStep(SQLModel):
    ok: bool
    action: str
    message: str


class CommandResult(SQLModel):
    ok: bool
    action: str
    message: str
    todo: dict | None = None
    todos: list[dict] | None = None
    steps: list[CommandStep] = []


class AgentStatus(SQLModel):
    available: bool
    model: str
    base_url: str


class Meta(SQLModel):
    priorities: list[str]
    categories: list[str]
    agent: AgentStatus


SortOption = Literal["newest", "due", "priority"]
StatusFilter = Literal["all", "open", "done"]
ClearScope = Literal["all", "done"]
