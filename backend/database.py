from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from backend.config import DATABASE_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)


def init_db() -> None:
    from backend import models  # noqa: F401  register tables

    if _is_sqlite:
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    SQLModel.metadata.create_all(engine)


def get_session():
    """Request-scoped session."""
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope():
    """Session for code outside a request, like agent tools."""
    with Session(engine) as session:
        yield session
