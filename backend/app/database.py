"""
Configuration de la connexion à la base de données PostgreSQL.
Utilise SQLAlchemy 2.0.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dépendance FastAPI pour injection de session de base de données.
    La session est automatiquement fermée après la requête.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialise la base de données (crée les tables si nécessaire).
    Applique les migrations optionnelles (colonnes ajoutées après coup).
    """
    Base.metadata.create_all(bind=engine)
    # Migration: colonne smart_dimming_paused_until sur devices (si absente)
    from sqlalchemy import text
    with engine.connect() as conn:
        if conn.execute(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'devices' AND column_name = 'smart_dimming_paused_until'"
            )
        ).scalar() is None:
            conn.execute(text("ALTER TABLE devices ADD COLUMN smart_dimming_paused_until TIMESTAMP WITH TIME ZONE"))
            conn.commit()
