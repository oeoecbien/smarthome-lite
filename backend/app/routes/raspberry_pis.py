"""
Routes pour la gestion des Raspberry Pi.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
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
        # Compter les appareils
        device_count = db.query(func.count(Device.id)).filter(
            Device.raspberry_pi_id == rpi.id
        ).scalar()
        
        result.append({
            "id": rpi.id,
            "name": rpi.name,
            "location": rpi.location,
            "ip_address": rpi.ip_address,
            "api_key": "***" + rpi.api_key_hash[-8:] if rpi.api_key_hash else None,  # Masquer le hash
            "is_online": rpi.is_online,
            "created_at": rpi.created_at,
            "updated_at": rpi.updated_at,
            "device_count": device_count
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
    admin_user: User = Depends(require_admin),
):
    """
    Données capteur d'un nœud Z-Wave sur ce Raspberry Pi.
    Compatible Aeotec MultiSensor 7 (ZWA024) : mouvement, température, humidité,
    luminosité, UV, batterie. Proxy vers le RPi GET /api/nodes/{node_id}/sensor.
    """
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == rpi_id).first()
    if not rpi:
        raise HTTPException(status_code=404, detail="Raspberry Pi introuvable")
    if node_id < 1 or node_id > 255:
        raise HTTPException(status_code=400, detail="node_id doit être entre 1 et 255")
    device_service = DeviceService(db)
    try:
        data = await device_service.get_sensor_data_from_rpi(rpi, node_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Capteur indisponible : {str(e)}")


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

