"""
Routes pour la gestion des événements système.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import Event, Device
from app.schemas.event import EventResponse
from app.dependencies import get_current_user, PaginationParams, EventFilterParams, User

router = APIRouter()


@router.get("", response_model=List[EventResponse])
async def get_events(
    pagination: PaginationParams = Depends(),
    filters: EventFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère l'historique des événements avec filtres et pagination.
    - Utilisateurs normaux: uniquement les événements de leurs appareils
    - Admins: tous les événements
    """
    query = db.query(Event)
    
    # Filtrer par les devices de l'utilisateur si ce n'est pas un admin
    if current_user.role != "admin":
        user_device_ids = [d.id for d in db.query(Device.id).filter(Device.user_id == current_user.id).all()]
        query = query.filter(Event.device_id.in_(user_device_ids))
    
    # Filtres
    if filters.event_type:
        query = query.filter(Event.event_type == filters.event_type)
    
    if filters.source:
        query = query.filter(Event.source == filters.source)
    
    if filters.device_id:
        # Vérifier que le device appartient à l'utilisateur (si ce n'est pas un admin)
        if current_user.role != "admin":
            device = db.query(Device).filter(
                Device.id == filters.device_id,
                Device.user_id == current_user.id
            ).first()
            if device:
                query = query.filter(Event.device_id == filters.device_id)
            else:
                # Device n'appartient pas à l'utilisateur, retourner liste vide
                query = query.filter(Event.device_id == -1)  # Condition impossible
        else:
            # Admin peut voir tous les événements
            query = query.filter(Event.device_id == filters.device_id)
    
    # Pagination
    events = query.order_by(Event.timestamp.desc()).offset(
        pagination.skip
    ).limit(pagination.limit).all()
    
    # Enrichir avec le nom de l'appareil
    result = []
    for event in events:
        device_name = None
        if event.device_id:
            device = db.query(Device).filter(Device.id == event.device_id).first()
            device_name = device.name if device else None
        
        result.append({
            "id": event.id,
            "device_id": event.device_id,
            "device_name": device_name,
            "event_type": event.event_type,
            "value": event.value,
            "source": event.source,
            "timestamp": event.timestamp
        })
    
    return result


@router.get("/device/{device_id}", response_model=List[EventResponse])
async def get_device_events(
    device_id: int,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les événements d'un appareil spécifique.
    - Utilisateurs normaux: uniquement leurs appareils
    - Admins: tous les appareils
    """
    # Vérifier que l'appareil existe
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Appareil introuvable")
    
    # Vérifier les permissions: les utilisateurs normaux ne peuvent voir que leurs appareils
    if current_user.role != "admin" and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    events = db.query(Event).filter(
        Event.device_id == device_id
    ).order_by(Event.timestamp.desc()).offset(
        pagination.skip
    ).limit(pagination.limit).all()
    
    result = []
    for event in events:
        result.append({
            "id": event.id,
            "device_id": event.device_id,
            "device_name": device.name,
            "event_type": event.event_type,
            "value": event.value,
            "source": event.source,
            "timestamp": event.timestamp
        })
    
    return result

