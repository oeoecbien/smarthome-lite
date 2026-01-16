"""
Routes d'administration - Accessibles uniquement aux administrateurs
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from app.database import get_db
from app.dependencies import get_current_user, require_admin, User
from app.models import Device, User as UserModel, Event, SmartDimmingAdjustment, RaspberryPi

router = APIRouter()


@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Statistiques globales du système (uniquement pour les admins).
    """
    # Nombre total d'utilisateurs
    total_users = db.query(func.count(UserModel.id)).scalar()
    
    # Nombre total d'appareils
    total_devices = db.query(func.count(Device.id)).scalar()
    
    # Appareils par type
    devices_by_type = db.query(
        Device.type,
        func.count(Device.id).label('count')
    ).group_by(Device.type).all()
    devices_by_type_dict = {d.type: d.count for d in devices_by_type}
    
    # Appareils par état
    devices_on = db.query(func.count(Device.id)).filter(Device.state == True).scalar()
    devices_off = total_devices - devices_on
    
    # Événements aujourd'hui
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    events_today = db.query(func.count(Event.id)).filter(
        Event.timestamp >= today_start
    ).scalar()
    
    # Ajustements Smart Dimming aujourd'hui
    adjustments_today = db.query(func.count(SmartDimmingAdjustment.id)).filter(
        SmartDimmingAdjustment.adjusted_at >= today_start
    ).scalar()
    
    # Raspberry Pi en ligne
    raspberry_pis_online = db.query(func.count(RaspberryPi.id)).filter(
        RaspberryPi.is_online == True
    ).scalar()
    total_raspberry_pis = db.query(func.count(RaspberryPi.id)).scalar()
    
    return {
        "users": {
            "total": total_users
        },
        "devices": {
            "total": total_devices,
            "by_type": devices_by_type_dict,
            "on": devices_on,
            "off": devices_off
        },
        "events": {
            "today": events_today
        },
        "smart_dimming": {
            "adjustments_today": adjustments_today
        },
        "raspberry_pis": {
            "total": total_raspberry_pis,
            "online": raspberry_pis_online,
            "offline": total_raspberry_pis - raspberry_pis_online
        }
    }


@router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Liste tous les utilisateurs (uniquement pour les admins).
    """
    users = db.query(UserModel).all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "device_count": db.query(func.count(Device.id)).filter(
                Device.user_id == user.id
            ).scalar()
        }
        for user in users
    ]


# Note: Les endpoints /api/admin/devices/all et /api/admin/events/all ont été supprimés
# car redondants avec /api/devices/ et /api/events/ qui filtrent déjà par rôle admin.
