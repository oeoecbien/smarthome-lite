"""
Routes pour la détection de présence (utilisées par Raspberry Pi).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import func
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
    device_mac_address: Optional[str] = None  # Adresse MAC du device Bluetooth (ou identifiant BLE)
    device_name: Optional[str] = None  # Nom BLE annoncé par l'appareil (ex: Galaxy A52)
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
        _mac_norm = request.device_mac_address.strip().replace("-", ":").upper()
        query = query.filter(Presence.device_mac_address == _mac_norm)
    
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
    
    # Toujours enregistrer la présence. Si la MAC n'est pas dans bluetooth_devices, l'ajouter
    # automatiquement (user_id=None) pour que "tous les devices détectés" soient dans la liste.
    # Format canonique MAC (AA:BB:CC:DD:EE:FF) pour matcher même si la BDD a été remplie avec des tirets
    mac_upper = (request.device_mac_address.strip().replace("-", ":").replace(" ", "").upper()) if request.device_mac_address else None
    if mac_upper and len(mac_upper) == 12 and mac_upper.isalnum():
        mac_upper = ":".join(mac_upper[i : i + 2] for i in range(0, 12, 2))
    user_id = None
    if mac_upper:
        try:
            from app.models import BluetoothDevice
            # Retrouver l'appareil qu'il soit stocké avec : ou - (admin peut avoir saisi 94-7B-E7-...)
            bluetooth_device = db.query(BluetoothDevice).filter(
                func.replace(BluetoothDevice.mac_address, "-", ":") == mac_upper,
                BluetoothDevice.is_active == True,
            ).first()
            if bluetooth_device:
                user_id = bluetooth_device.user_id
            else:
                # Auto-ajout : tout device détecté est ajouté à bluetooth_devices (user_id=None)
                new_device = BluetoothDevice(
                    mac_address=mac_upper,
                    user_id=None,
                    device_name="Auto-détecté",
                    device_type=None,
                    is_active=True,
                )
                db.add(new_device)
                db.commit()
        except Exception:
            db.rollback()
            pass

    # Créer la détection (MAC connue ou venant d'être auto-ajoutée)
    presence = Presence(
        raspberry_pi_id=rpi.id,
        device_mac_address=mac_upper,
        device_name=(request.device_name or "").strip() or None,
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


class RecentDetectionItem(BaseModel):
    """Une détection récente pour affichage « Lier à mon compte »."""
    device_mac_address: str
    device_name: Optional[str] = None
    signal_strength: Optional[int] = None
    detected_at: datetime
    raspberry_pi_name: str
    location: str


@router.get("/recent", response_model=List[RecentDetectionItem])
async def get_recent_detections(
    minutes: int = 2,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste les appareils détectés récemment (dernières N minutes).
    Permet à l'utilisateur de lier un appareil à son compte sans saisir la MAC :
    « Ces appareils viennent d'être détectés → cliquez pour lier à mon compte ».
    """
    from datetime import timedelta
    since = datetime.now() - timedelta(minutes=min(minutes, 60))
    rows = (
        db.query(Presence, RaspberryPi)
        .join(RaspberryPi, Presence.raspberry_pi_id == RaspberryPi.id)
        .filter(
            Presence.detected_at >= since,
            Presence.device_mac_address.isnot(None),
            Presence.device_mac_address != "",
        )
        .order_by(Presence.detected_at.desc())
        .limit(100)
        .all()
    )
    seen_macs: set[str] = set()
    result = []
    for presence, rpi in rows:
        mac = (presence.device_mac_address or "").strip()
        if not mac or mac in seen_macs:
            continue
        seen_macs.add(mac)
        result.append({
            "device_mac_address": mac,
            "device_name": (presence.device_name or "").strip() or None,
            "signal_strength": presence.signal_strength,
            "detected_at": presence.detected_at,
            "raspberry_pi_name": rpi.name,
            "location": rpi.location or "",
        })
    return result


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

