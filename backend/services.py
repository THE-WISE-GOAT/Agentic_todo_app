from datetime import date

from sqlalchemy import case, func
from sqlmodel import Session, select

from backend.models import Category, Priority, Todo
from backend.schemas import TodoCreate, TodoUpdate


def list_todos(
    session: Session,
    *,
    status: str = "all",
    category: Category | None = None,
    query: str | None = None,
    sort: str = "newest",
) -> list[Todo]:
    stmt = select(Todo)

    if status == "open":
        stmt = stmt.where(Todo.completed == False)  # noqa: E712
    elif status == "done":
        stmt = stmt.where(Todo.completed == True)  # noqa: E712

    if category is not None:
        stmt = stmt.where(Todo.category == category)

    if query:
        stmt = stmt.where(Todo.text.icontains(query, autoescape=True))

    if sort == "due":
        stmt = stmt.order_by(Todo.due_date.is_(None), Todo.due_date, Todo.created_at.desc())
    elif sort == "priority":
        rank = case(
            (Todo.priority == Priority.HIGH, 0),
            (Todo.priority == Priority.MEDIUM, 1),
            else_=2,
        )
        stmt = stmt.order_by(rank, Todo.created_at.desc())
    else:
        stmt = stmt.order_by(Todo.created_at.desc(), Todo.id.desc())

    return list(session.exec(stmt).all())


def get_todo(session: Session, todo_id: int) -> Todo | None:
    return session.get(Todo, todo_id)


def create_todo(session: Session, data: TodoCreate) -> Todo:
    todo = Todo(**data.model_dump())
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


def update_todo(session: Session, todo: Todo, data: TodoUpdate) -> Todo:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(todo, key, value)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


def delete_todo(session: Session, todo: Todo) -> None:
    session.delete(todo)
    session.commit()


def clear_todos(session: Session, status: str = "all") -> int:
    stmt = select(Todo)
    if status == "done":
        stmt = stmt.where(Todo.completed == True)  # noqa: E712
    todos = session.exec(stmt).all()
    for todo in todos:
        session.delete(todo)
    session.commit()
    return len(todos)


def get_stats(session: Session) -> dict[str, int]:
    total = session.exec(select(func.count()).select_from(Todo)).one()
    done = session.exec(
        select(func.count()).select_from(Todo).where(Todo.completed == True)  # noqa: E712
    ).one()
    overdue = session.exec(
        select(func.count())
        .select_from(Todo)
        .where(
            Todo.completed == False,  # noqa: E712
            Todo.due_date.is_not(None),
            Todo.due_date < date.today(),
        )
    ).one()
    return {"total": total, "done": done, "open": total - done, "overdue": overdue}


def as_dict(todo: Todo) -> dict:
    return {
        "id": todo.id,
        "text": todo.text,
        "completed": todo.completed,
        "created_at": todo.created_at.isoformat(),
        "priority": todo.priority.value,
        "due_date": todo.due_date.isoformat() if todo.due_date else None,
        "category": todo.category.value,
    }
