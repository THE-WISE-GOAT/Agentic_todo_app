from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
import os

DATABASE_URL = "sqlite:///./todos.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def init_db():
    """Create all tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Yield a database session for FastAPI dependencies."""
    with Session(engine) as session:
        yield session
