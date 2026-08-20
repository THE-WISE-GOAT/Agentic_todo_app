from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List
import os

from backend.database import engine, get_session, init_db
from backend.models import Todo, TodoCreate, TodoUpdate, Priority, Category


def get_process_command_function():
    try:
        from backend.agent.graph import process_command_with_graph
        return process_command_with_graph
    except ImportError as e:
        raise ImportError(
            f"Failed to import agent. Make sure all dependencies are installed: {e}\n"
            "Run: pip install -r requirements.txt"
        )


app = FastAPI(title="Todo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def read_root():
    return {"message": "Todo API is running"}


@app.get("/todos", response_model=List[Todo])
def get_todos(session: Session = Depends(get_session)):
    statement = select(Todo).order_by(Todo.id)
    return session.exec(statement).all()


@app.post("/todos", response_model=Todo)
def create_todo(todo: TodoCreate, session: Session = Depends(get_session)):
    db_todo = Todo(
        text=todo.text,
        priority=todo.priority or Priority.MEDIUM,
        due_date=todo.due_date,
        category=todo.category or Category.GENERAL,
    )
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoUpdate, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = todo_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(todo, key, value)

    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(todo)
    session.commit()
    return {"message": "Todo deleted successfully"}


@app.delete("/todos")
def delete_all_todos(session: Session = Depends(get_session)):
    statement = select(Todo)
    todos = session.exec(statement).all()
    for todo in todos:
        session.delete(todo)
    session.commit()
    return {"message": "All todos deleted successfully"}


@app.post("/todos/process-command")
def process_command(command: str, thread_id: str = "default"):
    try:
        process_command_with_graph = get_process_command_function()
        result = process_command_with_graph(command, thread_id)

        action = None
        todo_id = None
        todo_text = None

        if result.get("success"):
            message = result.get("message", "")
            message_lower = message.lower()

            if "created" in message_lower or "create" in message_lower:
                action = "create"
                if "todo" in result:
                    todo_text = result["todo"].get("text")
            elif "deleted" in message_lower and "all" in message_lower:
                action = "delete_all"
            elif "deleted" in message_lower:
                action = "delete"
            elif "updated" in message_lower:
                action = "update"
            elif "completed" in message_lower:
                action = "complete"
            elif "todos" in result:
                action = "list"

        return {
            "action": action,
            "todo_id": todo_id,
            "todo_text": todo_text,
            "result": result,
            "message": result.get("message", ""),
        }
    except Exception as e:
        return {
            "action": None,
            "todo_id": None,
            "todo_text": None,
            "result": {"success": False, "message": f"Error processing command: {str(e)}"},
            "message": f"Error: {str(e)}",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
