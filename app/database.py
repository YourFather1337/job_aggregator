from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import DATABASE_URL
from app.models import Base

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # необходимо для SQLite
)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: выдаёт сессию БД и закрывает её после запроса."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()