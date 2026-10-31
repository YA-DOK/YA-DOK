
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Database connection
engine = None
SessionLocal = None

if settings.database_url:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"sslmode": ("disable" if make_url(settings.database_url).host in ("localhost", "127.0.0.1", "::1") else "require")},
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
    if SessionLocal is None:
        raise RuntimeError(
            "Database is not configured. "
            "Set DATABASE_URL in the project's .env file."
        )

    with SessionLocal() as db:
        yield db
