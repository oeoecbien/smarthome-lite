"""
Routes pour la gestion des Raspberry Pi.
"""

from fastapi import APIRouter, Depends, HTTPException, status
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
from app.dependencies import get_current_user
from app.utils.auth import generate_api_key

router = APIRouter()


@router.get("/", response_model=List[RaspberryPiResponse])
async def get_raspberry_pis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste tous les Raspberry Pi enregistrés.
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
            "api_key": rpi.api_key,
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
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un Raspberry Pi spécifique.
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
        "api_key": rpi.api_key,
        "is_online": rpi.is_online,
        "created_at": rpi.created_at,
        "updated_at": rpi.updated_at,
        "device_count": device_count
    }


@router.post("/", response_model=RaspberryPiResponse, status_code=status.HTTP_201_CREATED)
async def create_raspberry_pi(
    rpi_data: RaspberryPiCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enregistre un nouveau Raspberry Pi.
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
    
    # Générer une clé API unique
    api_key = generate_api_key()
    
    # Créer le Raspberry Pi
    rpi = RaspberryPi(
        name=rpi_data.name,
        location=rpi_data.location,
        ip_address=rpi_data.ip_address,
        api_key=api_key,
        is_online=False
    )
    
    db.add(rpi)
    db.commit()
    db.refresh(rpi)
    
    return {
        "id": rpi.id,
        "name": rpi.name,
        "location": rpi.location,
        "ip_address": rpi.ip_address,
        "api_key": rpi.api_key,
        "is_online": rpi.is_online,
        "created_at": rpi.created_at,
        "updated_at": rpi.updated_at,
        "device_count": 0
    }


@router.put("/{rpi_id}", response_model=RaspberryPiResponse)
async def update_raspberry_pi(
    rpi_id: int,
    rpi_data: RaspberryPiUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour un Raspberry Pi.
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
        "api_key": rpi.api_key,
        "is_online": rpi.is_online,
        "created_at": rpi.created_at,
        "updated_at": rpi.updated_at,
        "device_count": device_count
    }

