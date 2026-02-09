"""
Routes pour la gestion des appareils
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

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
from app.config import BRIGHTNESS_MAX

router = APIRouter()

@router.get("/", response_model=List[DeviceWithLocation])
async def get_devices(
    location: str = None,
    type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les appareils avec leur localisation.
    - Utilisateurs normaux: voient uniquement leurs appareils
    - Admins: voient tous les appareils
    Filtres optionnels: location, type
    """
    device_service = DeviceService(db)
    # Les admins voient tous les appareils, les utilisateurs normaux uniquement les leurs
    user_id = None if current_user.role == "admin" else current_user.id
    devices = device_service.get_all_devices_with_location(user_id=user_id)
    
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
    Récupère un appareil spécifique par ID.
    - Utilisateurs normaux: uniquement leurs appareils
    - Admins: tous les appareils
    """
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.deleted_at.is_(None),
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Vérifier les permissions: les utilisateurs normaux ne peuvent voir que leurs appareils
    if current_user.role != "admin" and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    device_service = DeviceService(db)
    
    try:
        # Les admins peuvent voir tous les appareils, les utilisateurs normaux uniquement les leurs
        user_id = None if current_user.role == "admin" else current_user.id
        device_with_location = device_service.get_device_with_location(device_id, user_id=user_id)
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
    from app.models import RaspberryPi
    
    # Vérifier que le Raspberry Pi existe
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == device_data.raspberry_pi_id).first()
    if not rpi:
        raise HTTPException(
            status_code=404,
            detail=f"Raspberry Pi avec l'ID {device_data.raspberry_pi_id} introuvable"
        )
    
    # Vérifier GPIO unique par RPi (uniquement parmi les appareils non supprimés)
    existing = db.query(Device).filter(
        Device.raspberry_pi_id == device_data.raspberry_pi_id,
        Device.gpio_pin == device_data.gpio_pin,
        Device.deleted_at.is_(None),
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
        brightness=0 if device_data.type == "dimmer" else BRIGHTNESS_MAX
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    return device

@router.get("/{device_id}/state")
async def get_device_state(
    device_id: int,
    sync: bool = Query(False, description="Rafraîchir l'état depuis le RPi (lampe réelle)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    État actuel de l'appareil (state, brightness).
    - Par défaut : valeur en base (celle du dernier contrôle).
    - Avec ?sync=true : lecture depuis le RPi puis mise à jour en base (état réel de la lampe).
    Utilisable par le front mobile pour afficher l'état à jour.
    """
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.deleted_at.is_(None),
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if current_user.role != "admin" and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if sync:
        device_service = DeviceService(db)
        updated = await device_service.sync_device_state_from_rpi(device_id)
        if updated:
            device = updated
    return {
        "id": device.id,
        "name": device.name,
        "state": device.state,
        "brightness": min(100, max(0, device.brightness)),
    }


@router.put("/{device_id}/state")
async def set_device_state(
    device_id: int,
    state_data: DeviceState,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change l'état ON/OFF d'un appareil.
    - Utilisateurs normaux: uniquement leurs appareils
    - Admins: tous les appareils
    """
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.deleted_at.is_(None),
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Vérifier les permissions: les utilisateurs normaux ne peuvent modifier que leurs appareils
    if current_user.role != "admin" and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    device_service = DeviceService(db)
    
    try:
        device = await device_service.set_device_state(
            device_id,
            state_data.state,
            source="manual"
        )
        
        # À l'allumage (light/dimmer) : appliquer la luminosité envoyée par le client,
        # ou reprendre celle stockée en base. Si la valeur stockée est 0 (lampe était éteinte),
        # utiliser une luminosité par défaut pour éviter d'éteindre juste après l'allumage.
        if (
            state_data.state
            and device.type in ["light", "dimmer"]
        ):
            brightness_to_apply = (
                state_data.brightness
                if state_data.brightness is not None
                else (device.brightness if device.brightness > 0 else BRIGHTNESS_MAX)
            )
            device = await device_service.set_device_brightness(
                device_id,
                brightness_to_apply,
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
    brightness_data: Optional[DeviceBrightness] = Body(None),
    intensity: Optional[float] = Query(None, ge=0, le=99, description="Intensité 0-99 ou 0-1 (sera converti)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change l'intensité d'un appareil dimmable.
    Accepte soit un body JSON { "brightness": 0-100, "transition"?: number }
    soit un paramètre de requête intensity (0-99 ou 0-1).
    - Utilisateurs normaux: uniquement leurs appareils
    - Admins: tous les appareils
    """
    if brightness_data is not None:
        # Frontend envoie 0-100 ; on garde 0-100 en base, le service envoie 0-99 au RPi
        brightness = max(0, min(100, brightness_data.brightness))
        transition = brightness_data.transition
    elif intensity is not None:
        # Accepter 0-1 (ex: 0.5) ou 0-99
        brightness = int(round(intensity * BRIGHTNESS_MAX)) if intensity <= 1 else int(round(intensity))
        brightness = max(0, min(100, brightness))
        transition = None
    else:
        raise HTTPException(
            status_code=422,
            detail="Fournir soit un body avec 'brightness' (0-100), soit le paramètre de requête 'intensity'."
        )

    device = db.query(Device).filter(
        Device.id == device_id,
        Device.deleted_at.is_(None),
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Vérifier les permissions: les utilisateurs normaux ne peuvent modifier que leurs appareils
    if current_user.role != "admin" and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    device_service = DeviceService(db)
    
    try:
        device = await device_service.set_device_brightness(
            device_id,
            brightness,
            source="manual",
            transition=transition
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
    Supprime un appareil.
    - Utilisateurs normaux: uniquement leurs appareils
    - Admins: tous les appareils
    """
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.deleted_at.is_(None),
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Vérifier les permissions: les utilisateurs normaux ne peuvent supprimer que leurs appareils
    if current_user.role != "admin" and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(device)
    db.commit()
    
    return None