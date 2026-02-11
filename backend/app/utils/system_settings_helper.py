"""
Helper pour lire/écrire les paramètres système persistés en BDD.
Utilisé par le Smart Dimming (smart_dimming_enabled) pour survivre aux redémarrages.
"""
from sqlalchemy.orm import Session

from app.config import settings
from app.models import SystemSetting


def get_smart_dimming_enabled(db: Session) -> bool:
    """
    Retourne si le Smart Dimming est activé.
    Lit d'abord la BDD (system_settings), sinon fallback sur la config (.env).
    """
    row = db.query(SystemSetting).filter(SystemSetting.key == "smart_dimming_enabled").first()
    if row is None:
        return settings.smart_dimming_enabled
    return row.value.strip().lower() in ("true", "1", "yes")


def set_smart_dimming_enabled(db: Session, enabled: bool) -> None:
    """
    Persiste l'état activé/désactivé du Smart Dimming en BDD.
    """
    value = "true" if enabled else "false"
    row = db.query(SystemSetting).filter(SystemSetting.key == "smart_dimming_enabled").first()
    if row is None:
        db.add(SystemSetting(key="smart_dimming_enabled", value=value))
    else:
        row.value = value
    db.commit()
