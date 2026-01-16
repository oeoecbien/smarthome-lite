"""
Routes pour la gestion des appareils
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Device, User
from app.schemas.device import (
    Device as DeviceSchema,
    DeviceCreate,
    DeviceUpdate,
    DeviceState,
    DeviceBrightness,
    DeviceWithLocation
)
from app.services.device_service import DeviceService
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[DeviceWithLocation])
async def get_devices(
    location: str = None,
    type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste tous les appareils de l'utilisateur connecté avec leur localisation
    Filtres optionnels: location, type
    """
    device_service = DeviceService(db)
    devices = device_service.get_all_devices_with_location(user_id=current_user.id)
    
    # Filtres
    if location:
        devices = [d for d in devices if d["location"] == location]
    if type:
        devices = [d for d in devices if d["type"] == type]
    
    return devices

@router.get("/{device_id}", response_model=DeviceWithLocation)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un appareil spécifique par ID (uniquement si appartient à l'utilisateur)
    """
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or access denied")
    
    device_service = DeviceService(db)
    
    try:
        device_with_location = device_service.get_device_with_location(device_id, user_id=current_user.id)
        return device_with_location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/", response_model=DeviceSchema, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Créer un nouvel appareil (assigné automatiquement à l'utilisateur connecté)
    """
    # Vérifier GPIO unique par RPi
    existing = db.query(Device).filter(
        Device.raspberry_pi_id == device_data.raspberry_pi_id,
        Device.gpio_pin == device_data.gpio_pin
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"GPIO pin {device_data.gpio_pin} already used on this Raspberry Pi"
        )
    
    device = Device(
        **device_data.dict(),
        user_id=current_user.id,  # Assigner automatiquement à l'utilisateur connecté
        state=False,
        brightness=0 if device_data.type == "dimmer" else 100
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    return device

@router.put("/{device_id}/state")
async def set_device_state(
    device_id: int,
    state_data: DeviceState,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change l'état ON/OFF d'un appareil (uniquement si appartient à l'utilisateur)
    """
    # Vérifier que le device appartient à l'utilisateur
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or access denied")
    
    device_service = DeviceService(db)
    
    try:
        device = await device_service.set_device_state(
            device_id,
            state_data.state,
            source="manual"
        )
        
        # Si brightness fournie et device dimmable
        if state_data.brightness is not None and device.type in ["light", "dimmer"]:
            device = await device_service.set_device_brightness(
                device_id,
                state_data.brightness,
                source="manual"
            )
        
        return {
            "id": device.id,
            "name": device.name,
            "state": device.state,
            "brightness": device.brightness
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{device_id}/brightness")
async def set_device_brightness(
    device_id: int,
    brightness_data: DeviceBrightness,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change l'intensité d'un appareil dimmable (uniquement si appartient à l'utilisateur)
    """
    # Vérifier que le device appartient à l'utilisateur
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or access denied")
    
    device_service = DeviceService(db)
    
    try:
        device = await device_service.set_device_brightness(
            device_id,
            brightness_data.brightness,
            source="manual",
            transition=brightness_data.transition
        )
        
        return {
            "id": device.id,
            "name": device.name,
            "brightness": device.brightness,
            "state": device.state
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un appareil (uniquement si appartient à l'utilisateur)
    """
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or access denied")
    
    db.delete(device)
    db.commit()
    
    return None