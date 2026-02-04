"""
Routes pour la gestion des appareils Bluetooth (association MAC → utilisateur).

Permet aux admins d'associer une adresse MAC Bluetooth (téléphone, montre…)
à un utilisateur (jean, mehdi…). Lorsque le RPi détecte cette MAC à portée,
la présence est enregistrée avec le user_id correspondant pour piloter l'IA.
"""

import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field

from app.database import get_db
from app.dependencies import require_admin, get_current_user, User
from app.models import BluetoothDevice, User as UserModel

# Router admin : /api/admin/bluetooth-devices (liste/création/suppression par un admin)
router = APIRouter(prefix="/bluetooth-devices", tags=["Bluetooth Devices"])

# Router utilisateur connecté : /api/bluetooth-devices/me (ajouter / lister / supprimer ses propres appareils)
router_me = APIRouter(prefix="/bluetooth-devices", tags=["Bluetooth Devices - Mon compte"])

# Format MAC attendu : AA:BB:CC:DD:EE:FF (majuscules)
MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def _normalize_mac(mac: str) -> str:
    """Normalise la MAC au format canonique AA:BB:CC:DD:EE:FF (majuscules, deux-points)."""
    s = mac.strip().replace("-", ":").replace(" ", "").upper()
    if len(s) == 12 and all(c in "0123456789ABCDEF" for c in s):
        s = ":".join(s[i : i + 2] for i in range(0, 12, 2))
    return s


class BluetoothDeviceCreate(BaseModel):
    """Schéma pour associer un appareil BT à un utilisateur."""
    user_id: int = Field(..., description="ID de l'utilisateur (jean, mehdi, …)")
    mac_address: str = Field(..., min_length=12, max_length=17, description="Adresse MAC (AA:BB:CC:DD:EE:FF ou 94-7B-E7-A1-E7-A0)")
    device_name: str | None = Field(None, max_length=100, description="Nom du device (ex: Galaxy J7 de Jean)")
    device_type: str | None = Field(None, max_length=50, description="Type: phone, watch, headphones, etc.")

    def normalize_mac(self) -> str:
        return _normalize_mac(self.mac_address)


class BluetoothDeviceResponse(BaseModel):
    """Schéma de réponse pour un appareil Bluetooth."""
    id: int
    user_id: int | None  # None si appareil auto-détecté non encore assigné
    username: str
    mac_address: str
    device_name: str | None
    device_type: str | None
    is_active: bool


class MyBluetoothDeviceCreate(BaseModel):
    """Schéma pour qu'un utilisateur connecté enregistre son propre appareil (MAC → son compte)."""
    mac_address: str = Field(..., min_length=12, max_length=17, description="Adresse MAC (AA:BB:CC:DD:EE:FF ou 94-7B-E7-A1-E7-A0)")
    device_name: str | None = Field(None, max_length=100, description="Nom du device (ex: Mon Galaxy)")
    device_type: str | None = Field(None, max_length=50, description="Type: phone, watch, headphones, etc.")

    def normalize_mac(self) -> str:
        return _normalize_mac(self.mac_address)


@router.get("/", response_model=List[BluetoothDeviceResponse])
async def list_bluetooth_devices(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Liste tous les appareils Bluetooth enregistrés (MAC → utilisateur).

    Uniquement pour les admins. Permet de gérer quels téléphones / montres
    sont associés à quels utilisateurs pour la détection de présence.
    """
    devices = db.query(BluetoothDevice).filter(BluetoothDevice.is_active == True).all()
    result = []
    for d in devices:
        user = db.query(UserModel).filter(UserModel.id == d.user_id).first() if d.user_id else None
        result.append({
            "id": d.id,
            "user_id": d.user_id,
            "username": user.username if user else "Non assigné",
            "mac_address": d.mac_address,
            "device_name": d.device_name,
            "device_type": d.device_type,
            "is_active": d.is_active,
        })
    return result


@router.post("/", response_model=BluetoothDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_bluetooth_device(
    body: BluetoothDeviceCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Associe une adresse MAC Bluetooth à un utilisateur.

    Lorsque le RPi capteur détecte cette MAC à portée, la présence sera
    enregistrée avec ce user_id, et l'IA pourra utiliser la présence (jean, mehdi…).
    """
    mac = body.normalize_mac()
    if not MAC_REGEX.match(mac):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format MAC invalide. Attendu: AA:BB:CC:DD:EE:FF (ex: 94:7B:E7:A1:E7:A0)",
        )
    user = db.query(UserModel).filter(UserModel.id == body.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )
    existing = db.query(BluetoothDevice).filter(
        func.replace(BluetoothDevice.mac_address, "-", ":") == mac,
    ).first()
    if existing:
        if existing.user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cette adresse MAC est déjà associée à un utilisateur (id={existing.user_id})",
            )
        # Appareil auto-détecté (user_id=None) : assigner l'utilisateur et normaliser la MAC en BDD
        existing.user_id = body.user_id
        existing.mac_address = mac
        existing.device_name = body.device_name or existing.device_name
        existing.device_type = body.device_type or existing.device_type
        db.commit()
        db.refresh(existing)
        user = db.query(UserModel).filter(UserModel.id == body.user_id).first()
        return {
            "id": existing.id,
            "user_id": existing.user_id,
            "username": user.username if user else "?",
            "mac_address": existing.mac_address,
            "device_name": existing.device_name,
            "device_type": existing.device_type,
            "is_active": existing.is_active,
        }
    device = BluetoothDevice(
        user_id=body.user_id,
        mac_address=mac,
        device_name=body.device_name or None,
        device_type=body.device_type or None,
        is_active=True,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return {
        "id": device.id,
        "user_id": device.user_id,
        "username": user.username,
        "mac_address": device.mac_address,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "is_active": device.is_active,
    }


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bluetooth_device(
    device_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Supprime l'association MAC → utilisateur (l'adresse pourra être réassociée plus tard)."""
    device = db.query(BluetoothDevice).filter(BluetoothDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appareil Bluetooth introuvable")
    db.delete(device)
    db.commit()
    return None


# ---------- Routes pour utilisateur connecté (apps connectées) : ajouter ses propres appareils ----------

@router_me.get("/me", response_model=List[BluetoothDeviceResponse])
async def list_my_bluetooth_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste les appareils Bluetooth enregistrés pour l'utilisateur connecté.

    Permet aux apps connectées (web, mobile) d'afficher les appareils que l'utilisateur
    a associés à son compte pour la détection de présence.
    """
    devices = (
        db.query(BluetoothDevice)
        .filter(BluetoothDevice.user_id == current_user.id, BluetoothDevice.is_active == True)
        .all()
    )
    return [
        {
            "id": d.id,
            "user_id": d.user_id,
            "username": current_user.username,
            "mac_address": d.mac_address,
            "device_name": d.device_name,
            "device_type": d.device_type,
            "is_active": d.is_active,
        }
        for d in devices
    ]


@router_me.post("/me", response_model=BluetoothDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_my_bluetooth_device(
    body: MyBluetoothDeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enregistre un appareil Bluetooth pour l'utilisateur connecté (son téléphone, sa montre…).

    Les apps connectées peuvent appeler cet endpoint pour ajouter la MAC de l'appareil
    dans bluetooth_devices, associée au compte de l'utilisateur. La présence sera ensuite
    détectée par le RPi et enregistrée avec ce compte.
    """
    mac = body.normalize_mac()
    if not MAC_REGEX.match(mac):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format MAC invalide. Attendu: AA:BB:CC:DD:EE:FF (ex: 94:7B:E7:A1:E7:A0)",
        )
    existing = db.query(BluetoothDevice).filter(
        func.replace(BluetoothDevice.mac_address, "-", ":") == mac,
    ).first()
    if existing:
        if existing.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cet appareil est déjà enregistré sur votre compte.",
            )
        if existing.user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cette adresse MAC est déjà associée à un autre compte.",
            )
        # Appareil auto-détecté (user_id=None) : l'utilisateur le réclame, normaliser la MAC en BDD
        existing.user_id = current_user.id
        existing.mac_address = mac
        existing.device_name = body.device_name or existing.device_name
        existing.device_type = body.device_type or existing.device_type
        db.commit()
        db.refresh(existing)
        return {
            "id": existing.id,
            "user_id": existing.user_id,
            "username": current_user.username,
            "mac_address": existing.mac_address,
            "device_name": existing.device_name,
            "device_type": existing.device_type,
            "is_active": existing.is_active,
        }
    device = BluetoothDevice(
        user_id=current_user.id,
        mac_address=mac,
        device_name=body.device_name or None,
        device_type=body.device_type or None,
        is_active=True,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return {
        "id": device.id,
        "user_id": device.user_id,
        "username": current_user.username,
        "mac_address": device.mac_address,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "is_active": device.is_active,
    }


@router_me.delete("/me/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_bluetooth_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supprime un appareil Bluetooth du compte de l'utilisateur connecté (uniquement si il lui appartient)."""
    device = db.query(BluetoothDevice).filter(BluetoothDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appareil Bluetooth introuvable")
    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que vos propres appareils.",
        )
    db.delete(device)
    db.commit()
    return None
