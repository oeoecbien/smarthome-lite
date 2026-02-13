"""
Routes pour la gestion des Raspberry Pi.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import func

from app.database import get_db
from app.models import RaspberryPi, Device, User
from app.schemas.raspberry_pi import (
    RaspberryPiCreate,
    RaspberryPiUpdate,
    RaspberryPiResponse
)
from app.dependencies import get_current_user, require_admin, verify_raspberry_pi
from app.utils.auth import generate_api_key, hash_api_key
from app.services.device_service import DeviceService

router = APIRouter()
logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str | None:
    """IP du client (prise en compte X-Forwarded-For si proxy)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    if request.client:
        return request.client.host
    return None


@router.get("/heartbeat", status_code=204)
async def raspberry_pi_heartbeat(
    request: Request,
    db: Session = Depends(get_db),
    rpi: RaspberryPi = Depends(verify_raspberry_pi),
):
    """
    Appelé périodiquement par le RPi (avec X-API-Key) pour signaler qu'il est en ligne.
    Met à jour is_online = True pour ce RPi. Si l'IP réelle du client diffère de celle
    en base, met à jour ip_address pour que les prochains pings backend ciblent la bonne machine.
    Retourne 204 No Content.
    """
    # Mise à jour de l'IP si le RPi appelle depuis une adresse différente (ex. typo 10.103 vs 10.109)
    client_ip = _client_ip(request)
    if client_ip and client_ip != rpi.ip_address:
        pi = db.query(RaspberryPi).filter(RaspberryPi.id == rpi.id).first()
        if pi:
            pi.ip_address = client_ip
            db.commit()
    return None


@router.get("/available", response_model=List[dict])
async def get_available_raspberry_pis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les Raspberry Pi disponibles pour la création d'appareils.
    
    Retourne une version simplifiée (id, name, location) accessible aux utilisateurs normaux
    pour qu'ils puissent choisir un Raspberry Pi lors de la création d'un appareil.
    """
    raspberry_pis = db.query(RaspberryPi).all()
    
    return [
        {
            "id": rpi.id,
            "name": rpi.name,
            "location": rpi.location
        }
        for rpi in raspberry_pis
    ]


@router.get("", response_model=List[RaspberryPiResponse], include_in_schema=False)
@router.get("/", response_model=List[RaspberryPiResponse])
async def get_raspberry_pis(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Liste tous les Raspberry Pi enregistrés avec détails complets (uniquement pour les admins).
    
    La gestion des Raspberry Pi est une fonctionnalité technique réservée aux administrateurs.
    """
    raspberry_pis = db.query(RaspberryPi).all()
    
    result = []
    for rpi in raspberry_pis:
        # Appareils connectés (IDs pour debug admin)
        devices_on_rpi = db.query(Device.id).filter(
            Device.raspberry_pi_id == rpi.id,
            Device.deleted_at.is_(None),
        ).order_by(Device.id).all()
        device_ids = [row[0] for row in devices_on_rpi]
        device_count = len(device_ids)

        result.append({
            "id": rpi.id,
            "name": rpi.name,
            "location": rpi.location,
            "ip_address": rpi.ip_address,
            "api_key": "***" + rpi.api_key_hash[-8:] if rpi.api_key_hash else None,  # Masquer le hash
            "is_online": rpi.is_online,
            "created_at": rpi.created_at,
            "updated_at": rpi.updated_at,
            "device_count": device_count,
            "device_ids": device_ids,
        })
    
    return result


@router.get("/{rpi_id}", response_model=RaspberryPiResponse)
async def get_raspberry_pi(
    rpi_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Récupère un Raspberry Pi spécifique (uniquement pour les admins).
    """
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == rpi_id).first()
    if not rpi:
        raise HTTPException(status_code=404, detail="Raspberry Pi introuvable")
    
    device_count = db.query(func.count(Device.id)).filter(
        Device.raspberry_pi_id == rpi.id
    ).scalar()
    
    return {
        "id": rpi.id,
        "name": rpi.name,
        "location": rpi.location,
        "ip_address": rpi.ip_address,
        "api_key": "***" + rpi.api_key_hash[-8:] if rpi.api_key_hash else None,  # Masquer le hash
        "is_online": rpi.is_online,
        "created_at": rpi.created_at,
        "updated_at": rpi.updated_at,
        "device_count": device_count
    }


@router.get("/{rpi_id}/nodes/{node_id}/sensor")
async def get_raspberry_pi_node_sensor(
    rpi_id: int,
    node_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Données capteur d'un nœud Z-Wave sur ce Raspberry Pi.
    Compatible Aeotec MultiSensor 7 (ZWA024) : mouvement, température, humidité,
    luminosité, UV, batterie. Proxy vers le RPi GET /api/nodes/{node_id}/sensor.
    Accessible à tout utilisateur authentifié.
    """
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == rpi_id).first()
    if not rpi:
        raise HTTPException(status_code=404, detail="Raspberry Pi introuvable")
    if node_id < 1 or node_id > 255:
        raise HTTPException(status_code=400, detail="node_id doit être entre 1 et 255")
    logger.info("GET sensor: rpi_id=%s rpi=%s node_id=%s", rpi_id, rpi.name, node_id)
    device_service = DeviceService(db)
    try:
        data = await device_service.get_sensor_data_from_rpi(rpi, node_id)
        logger.info("GET sensor OK: rpi_id=%s node_id=%s", rpi_id, node_id)
        return data
    except Exception as e:
        logger.warning("GET sensor failed: rpi_id=%s node_id=%s err=%s", rpi_id, node_id, e)
        err = str(e).strip()
        if "timeout" in err.lower() and "capteur" in err.lower():
            detail = (
                "Lecture du capteur en timeout (appareil Z-Wave sur pile possible). "
                "Le RPi est peut-être en ligne. Attendez quelques secondes puis cliquez sur « Rafraîchir maintenant »."
            )
        elif "not responding" in err or "Timeout" in err.lower():
            detail = (
                f"Le Raspberry Pi « {rpi.name} » n'a pas répondu à temps. "
                "Vérifiez que l'API Flask (port 5000) tourne sur le RPi et que le backend peut le joindre."
            )
        elif "401" in err or "API key" in err.lower():
            detail = (
                "Clé API invalide ou manquante. Configurez RASPBERRY_PI_API_KEY dans le .env du backend "
                "avec la même valeur que RASPBERRY_API_KEY sur le RPi."
            )
        else:
            detail = f"Capteur indisponible : {err}"
        raise HTTPException(status_code=502, detail=detail)


SENSOR_STREAM_INTERVAL_SEC = 5


async def _sensor_stream_generator(rpi_id: int, node_id: int) -> AsyncGenerator[str, None]:
    """
    Génère des événements SSE avec les données capteur.
    Cadence : un événement toutes les 5 s (sleep = 5 - durée_fetch pour viser 5 s entre deux envois).
    """
    import time
    from app.database import SessionLocal
    logger.info("Sensor stream started: rpi_id=%s node_id=%s", rpi_id, node_id)
    try:
        while True:
            t0 = time.monotonic()
            try:
                db = SessionLocal()
                try:
                    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == rpi_id).first()
                    if not rpi:
                        logger.warning("Sensor stream: RPi id=%s introuvable", rpi_id)
                        yield f"data: {json.dumps({'error': 'Raspberry Pi introuvable'})}\n\n"
                        return
                    device_service = DeviceService(db)
                    data = await device_service.get_sensor_data_from_rpi(rpi, node_id)
                    payload = {"success": True, **data}
                    yield f"data: {json.dumps(payload)}\n\n"
                    logger.debug("Sensor stream event sent: rpi_id=%s node_id=%s motion=%s", rpi_id, node_id, data.get("motion"))
                finally:
                    db.close()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Sensor stream error: rpi_id=%s node_id=%s err=%s", rpi_id, node_id, e)
                yield f"data: {json.dumps({'error': str(e), 'success': False})}\n\n"
            elapsed = time.monotonic() - t0
            wait = max(0.0, SENSOR_STREAM_INTERVAL_SEC - elapsed)
            try:
                if wait > 0:
                    await asyncio.sleep(wait)
            except asyncio.CancelledError:
                break
    except asyncio.CancelledError:
        pass
    logger.info("Sensor stream ended: rpi_id=%s node_id=%s", rpi_id, node_id)


@router.get("/{rpi_id}/nodes/{node_id}/sensor/stream")
async def stream_raspberry_pi_node_sensor(
    rpi_id: int,
    node_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Flux temps réel des données capteur (Server-Sent Events).
    Envoie un événement toutes les 5 secondes. Fermez la connexion pour arrêter.
    """
    logger.info("GET sensor/stream: rpi_id=%s node_id=%s", rpi_id, node_id)
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == rpi_id).first()
    if not rpi:
        raise HTTPException(status_code=404, detail="Raspberry Pi introuvable")
    if node_id < 1 or node_id > 255:
        raise HTTPException(status_code=400, detail="node_id doit être entre 1 et 255")
    return StreamingResponse(
        _sensor_stream_generator(rpi_id, node_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class RegisterSensorBody(BaseModel):
    """Corps pour enregistrer un capteur Z-Wave (ex. MultiSense / MultiSensor 7)."""
    node_id: int
    name: Optional[str] = None


@router.post("/{rpi_id}/register-sensor", status_code=status.HTTP_201_CREATED)
async def register_sensor(
    rpi_id: int,
    body: RegisterSensorBody,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Enregistre un détecteur Z-Wave (MultiSense, MultiSensor 7, etc.) comme Device type sensor.
    Permet ensuite de lier une lampe à ce capteur (controlled_by_sensor_id + sensor_rules)
    pour que la lampe réagisse au mouvement (allumage + extinction après X s).
    """
    from app.config import BRIGHTNESS_MAX

    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == rpi_id).first()
    if not rpi:
        raise HTTPException(status_code=404, detail="Raspberry Pi introuvable")

    node_id = body.node_id
    if not 1 <= node_id <= 255:
        raise HTTPException(status_code=400, detail="node_id doit être entre 1 et 255")

    existing = db.query(Device).filter(
        Device.raspberry_pi_id == rpi_id,
        Device.gpio_pin == node_id,
        Device.deleted_at.is_(None),
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un appareil existe déjà sur ce RPi avec gpio_pin={node_id} (device_id={existing.id})",
        )

    admin_user_obj = db.query(User).filter(User.role == "admin").first()
    if not admin_user_obj:
        raise HTTPException(status_code=500, detail="Aucun utilisateur admin en base")

    name = body.name or f"Détecteur (node {node_id})"
    device = Device(
        user_id=admin_user_obj.id,
        raspberry_pi_id=rpi_id,
        name=name,
        type="sensor",
        gpio_pin=node_id,
        state=False,
        brightness=0,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return {
        "id": device.id,
        "name": device.name,
        "type": device.type,
        "gpio_pin": device.gpio_pin,
        "raspberry_pi_id": rpi_id,
        "message": "Détecteur enregistré. Configurez une lampe avec controlled_by_sensor_id et sensor_rules pour réagir au mouvement.",
    }


@router.post("/", response_model=RaspberryPiResponse, status_code=status.HTTP_201_CREATED)
async def create_raspberry_pi(
    rpi_data: RaspberryPiCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Enregistre un nouveau Raspberry Pi (uniquement pour les admins).
    """
    # Vérifier que l'IP n'est pas déjà utilisée
    existing = db.query(RaspberryPi).filter(
        RaspberryPi.ip_address == rpi_data.ip_address
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un Raspberry Pi avec l'IP {rpi_data.ip_address} existe déjà"
        )
    
    # Générer une clé API unique et la hasher
    api_key_plain = generate_api_key()
    api_key_hash = hash_api_key(api_key_plain)
    
    # Créer le Raspberry Pi
    rpi = RaspberryPi(
        name=rpi_data.name,
        location=rpi_data.location,
        ip_address=rpi_data.ip_address,
        api_key_hash=api_key_hash,
        is_online=False
    )
    
    db.add(rpi)
    db.commit()
    db.refresh(rpi)
    
    # Retourner la clé en clair UNIQUEMENT lors de la création
    # Elle ne sera plus jamais accessible après
    return {
        "id": rpi.id,
        "name": rpi.name,
        "location": rpi.location,
        "ip_address": rpi.ip_address,
        "api_key": api_key_plain,  # Clé en clair UNIQUEMENT à la création
        "is_online": rpi.is_online,
        "created_at": rpi.created_at,
        "updated_at": rpi.updated_at,
        "device_count": 0,
        "warning": "IMPORTANT: Sauvegardez cette clé API maintenant. Elle ne sera plus jamais affichée."
    }


@router.put("/{rpi_id}", response_model=RaspberryPiResponse)
async def update_raspberry_pi(
    rpi_id: int,
    rpi_data: RaspberryPiUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Met à jour un Raspberry Pi (uniquement pour les admins).
    """
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == rpi_id).first()
    if not rpi:
        raise HTTPException(status_code=404, detail="Raspberry Pi introuvable")
    
    if rpi_data.name is not None:
        rpi.name = rpi_data.name
    if rpi_data.location is not None:
        rpi.location = rpi_data.location
    if rpi_data.ip_address is not None:
        # Vérifier que la nouvelle IP n'est pas déjà utilisée
        existing = db.query(RaspberryPi).filter(
            RaspberryPi.ip_address == rpi_data.ip_address,
            RaspberryPi.id != rpi_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Un Raspberry Pi avec l'IP {rpi_data.ip_address} existe déjà"
            )
        rpi.ip_address = rpi_data.ip_address
    if rpi_data.is_online is not None:
        rpi.is_online = rpi_data.is_online
    if rpi_data.api_key is not None and rpi_data.api_key.strip():
        rpi.api_key_hash = hash_api_key(rpi_data.api_key.strip())
    
    db.commit()
    db.refresh(rpi)
    
    device_count = db.query(func.count(Device.id)).filter(
        Device.raspberry_pi_id == rpi.id
    ).scalar()
    
    return {
        "id": rpi.id,
        "name": rpi.name,
        "location": rpi.location,
        "ip_address": rpi.ip_address,
        "api_key": "***" + rpi.api_key_hash[-8:] if rpi.api_key_hash else None,  # Masquer le hash
        "is_online": rpi.is_online,
        "created_at": rpi.created_at,
        "updated_at": rpi.updated_at,
        "device_count": device_count
    }

