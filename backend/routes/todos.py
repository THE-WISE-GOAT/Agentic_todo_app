from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session

from backend.database import get_session
from backend.models import Category
from backend.schemas import (
    ClearScope,
    SortOption,
    StatusFilter,
    TodoCreate,
    TodoRead,
    TodoUpdate,
)
from backend.services import (
    clear_todos,
    create_todo,
    delete_todo,
    get_todo,
    list_todos,
    update_todo,
)

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("", response_model=list[TodoRead])
def list_route(
    status: StatusFilter = "all",
    category: Category | None = None,
    q: str | None = Query(default=None, max_length=200),
    sort: SortOption = "newest",
    session: Session = Depends(get_session),
):
    return list_todos(session, status=status, category=category, query=q, sort=sort)


@router.post("", response_model=TodoRead, status_code=201)
def create_route(payload: TodoCreate, session: Session = Depends(get_session)):
    return create_todo(session, payload)


@router.delete("")
def clear_route(status: ClearScope = "all", session: Session = Depends(get_session)):
    return {"deleted": clear_todos(session, status)}


@router.get("/{todo_id}", response_model=TodoRead)
def get_route(todo_id: int, session: Session = Depends(get_session)):
    todo = get_todo(session, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Task not found")
    return todo


@router.patch("/{todo_id}", response_model=TodoRead)
def update_route(todo_id: int, payload: TodoUpdate, session: Session = Depends(get_session)):
    todo = get_todo(session, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Task not found")
    return update_todo(session, todo, payload)


@router.delete("/{todo_id}", status_code=204)
def delete_route(todo_id: int, session: Session = Depends(get_session)):
    todo = get_todo(session, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Task not found")
    delete_todo(session, todo)
    return Response(status_code=204)
