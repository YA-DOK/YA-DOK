
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Database connection
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"},
)


# Database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
)


# Base class for database models
class Base(DeclarativeBase):
    pass


# Dependency for FastAPI endpoints
def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
