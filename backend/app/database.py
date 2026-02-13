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
    Crée les tables si besoin et applique les migrations (idempotentes).
    """
    from sqlalchemy import text

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # Colonne smart_dimming_paused_until sur devices
        if conn.execute(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'devices' AND column_name = 'smart_dimming_paused_until'"
            )
        ).scalar() is None:
            conn.execute(text("ALTER TABLE devices ADD COLUMN smart_dimming_paused_until TIMESTAMP WITH TIME ZONE"))
            conn.commit()

        # Table system_settings
        if conn.execute(
            text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'system_settings'"
            )
        ).scalar() is None:
            conn.execute(text(
                "CREATE TABLE system_settings ("
                "key VARCHAR(100) PRIMARY KEY, "
                "value TEXT NOT NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            ))
            conn.commit()

        # light_readings : sensor_type accepte 'simulated'
        conn.execute(text("ALTER TABLE light_readings DROP CONSTRAINT IF EXISTS check_sensor_type"))
        conn.execute(text(
            "ALTER TABLE light_readings ADD CONSTRAINT check_sensor_type "
            "CHECK (sensor_type IN ('BH1750', 'LDR', 'simulated'))"
        ))
        conn.commit()

        # events : source accepte 'smart_dimming_ml'
        conn.execute(text("ALTER TABLE events DROP CONSTRAINT IF EXISTS check_event_source"))
        conn.execute(text(
            "ALTER TABLE events ADD CONSTRAINT check_event_source "
            "CHECK (source IS NULL OR source IN ('manual', 'automatic', 'ai', 'system', 'smart_dimming', 'smart_dimming_ml'))"
        ))
        conn.commit()
