"""
Routes pour la détection de présence (utilisées par Raspberry Pi).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Presence, RaspberryPi
from app.dependencies import verify_raspberry_pi, get_current_user, require_admin, User, PaginationParams
from app.services.rule_engine import RuleEngine

router = APIRouter()


class KnownMacsResponse(BaseModel):
    """Liste des MAC enregistrées (bluetooth_devices) pour filtrage côté RPi."""
    mac_addresses: List[str]


@router.get("/known-macs", response_model=KnownMacsResponse)
async def get_known_macs(
    rpi: RaspberryPi = Depends(verify_raspberry_pi),
    db: Session = Depends(get_db),
):
    """
    Liste des adresses MAC connues (bluetooth_devices actifs).
    Le script bt_presence_scan peut n'envoyer que ces MAC pour réduire le bruit.
    """
    from app.models import BluetoothDevice
    rows = db.query(BluetoothDevice.mac_address).filter(
        BluetoothDevice.is_active == True,
    ).all()
    return {"mac_addresses": [r.mac_address for r in rows]}


class PresenceCreate(BaseModel):
    """Schéma pour création d'une détection de présence."""
    device_mac_address: Optional[str] = None  # Adresse MAC du device Bluetooth
    signal_strength: Optional[int] = None  # RSSI en dBm


class PresenceResponse(BaseModel):
    """Schéma de réponse pour une détection."""
    id: int
    raspberry_pi_id: int
    raspberry_pi_name: str
    location: str
    detected_at: datetime
    device_mac_address: Optional[str] = None
    signal_strength: Optional[int] = None
    user_id: Optional[int] = None
    recorded: Optional[bool] = True  # False si MAC inconnue (non enregistrée en BDD)


@router.post("/", response_model=PresenceResponse, status_code=status.HTTP_201_CREATED)
async def create_presence(
    request: PresenceCreate,
    rpi: RaspberryPi = Depends(verify_raspberry_pi),
    db: Session = Depends(get_db)
):
    """
    Enregistre une nouvelle détection de présence Bluetooth (appelé par Raspberry Pi).
    
    Cette route déclenche automatiquement l'évaluation des règles.
    
    Args:
        request: Données de détection (device_mac_address, signal_strength)
    """
    # Vérifier qu'il n'y a pas eu de détection récente pour cette MAC (anti-rebond 5 secondes)
    from datetime import timedelta
    five_seconds_ago = datetime.now() - timedelta(seconds=5)
    
    query = db.query(Presence).filter(
        Presence.raspberry_pi_id == rpi.id,
        Presence.detected_at >= five_seconds_ago
    )
    
    # Si une MAC est fournie, filtrer aussi par MAC
    if request.device_mac_address:
        query = query.filter(Presence.device_mac_address == request.device_mac_address.upper())
    
    recent_presence = query.first()
    
    if recent_presence:
        # Retourner la détection existante (anti-rebond)
        return {
            "id": recent_presence.id,
            "raspberry_pi_id": recent_presence.raspberry_pi_id,
            "raspberry_pi_name": rpi.name,
            "location": rpi.location,
            "detected_at": recent_presence.detected_at,
            "device_mac_address": recent_presence.device_mac_address,
            "signal_strength": recent_presence.signal_strength,
            "user_id": recent_presence.user_id,
            "recorded": True,
        }
    
    # N'enregistrer que les MAC connues (bluetooth_devices) pour éviter de remplir la BDD
    # avec des dizaines d'appareils inconnus (voisins, etc.). presence_detected = utilisateur connu.
    user_id = None
    mac_known = False
    if request.device_mac_address:
        try:
            from app.models import BluetoothDevice
            bluetooth_device = db.query(BluetoothDevice).filter(
                BluetoothDevice.mac_address == request.device_mac_address.upper(),
                BluetoothDevice.is_active == True,
            ).first()
            if bluetooth_device:
                user_id = bluetooth_device.user_id
                mac_known = True
        except Exception:
            pass

    if not mac_known and request.device_mac_address:
        # MAC inconnue : ne pas insérer (éviter bruit). 200 = accepté mais non enregistré.
        return JSONResponse(
            status_code=200,
            content={
                "id": 0,
                "raspberry_pi_id": rpi.id,
                "raspberry_pi_name": rpi.name,
                "location": rpi.location,
                "detected_at": datetime.now().isoformat(),
                "device_mac_address": request.device_mac_address.upper(),
                "signal_strength": request.signal_strength,
                "user_id": None,
                "recorded": False,
            },
        )

    # Créer la détection (MAC connue → user_id rempli)
    presence = Presence(
        raspberry_pi_id=rpi.id,
        device_mac_address=request.device_mac_address.upper() if request.device_mac_address else None,
        signal_strength=request.signal_strength,
        user_id=user_id
    )
    
    db.add(presence)
    db.commit()
    db.refresh(presence)
    
    # Déclencher l'évaluation des règles
    try:
        rule_engine = RuleEngine(db)
        trigger_data = {
            "raspberry_pi_id": rpi.id,
            "location": rpi.location,
            "device_mac_address": request.device_mac_address,
            "user_id": user_id
        }
        executed_rules = await rule_engine.evaluate_rules(
            trigger_event="presence_detected",
            trigger_data=trigger_data
        )
        
        if executed_rules:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Règles exécutées après détection de présence: {len(executed_rules)}")
    except Exception as e:
        # Ne pas faire échouer l'enregistrement si les règles échouent
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de l'évaluation des règles: {e}")
    
    return {
        "id": presence.id,
        "raspberry_pi_id": presence.raspberry_pi_id,
        "raspberry_pi_name": rpi.name,
        "location": rpi.location,
        "detected_at": presence.detected_at,
        "device_mac_address": presence.device_mac_address,
        "signal_strength": presence.signal_strength,
        "user_id": presence.user_id,
        "recorded": True,
    }


@router.get("/", response_model=List[PresenceResponse])
async def get_presence_history(
    raspberry_pi_id: Optional[int] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Récupère l'historique des détections de présence (uniquement pour les admins).
    
    La détection de présence Bluetooth est une fonctionnalité technique utilisée
    pour l'automatisation en arrière-plan. Les utilisateurs normaux n'ont pas
    besoin d'accéder à ces données.
    """
    query = db.query(Presence)
    
    if raspberry_pi_id:
        query = query.filter(Presence.raspberry_pi_id == raspberry_pi_id)
    
    presences = query.order_by(
        Presence.detected_at.desc()
    ).offset(pagination.skip).limit(pagination.limit).all()
    
    result = []
    for presence in presences:
        rpi = db.query(RaspberryPi).filter(
            RaspberryPi.id == presence.raspberry_pi_id
        ).first()
        
        result.append({
            "id": presence.id,
            "raspberry_pi_id": presence.raspberry_pi_id,
            "raspberry_pi_name": rpi.name if rpi else "Unknown",
            "location": rpi.location if rpi else "Unknown",
            "detected_at": presence.detected_at,
            "device_mac_address": presence.device_mac_address,
            "signal_strength": presence.signal_strength,
            "user_id": presence.user_id
        })
    
    return result

