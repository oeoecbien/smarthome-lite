"""
Routes pour la gestion des appareils Bluetooth (association MAC → utilisateur).

Permet aux admins d'associer une adresse MAC Bluetooth (téléphone, montre…)
à un utilisateur (jean, mehdi…). Lorsque le RPi détecte cette MAC à portée,
la présence est enregistrée avec le user_id correspondant pour piloter l'IA.
"""

import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field

from app.database import get_db
from app.dependencies import require_admin, User
from app.models import BluetoothDevice, User as UserModel

router = APIRouter(prefix="/bluetooth-devices", tags=["Bluetooth Devices"])

# Format MAC attendu : AA:BB:CC:DD:EE:FF (majuscules)
MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def _normalize_mac(mac: str) -> str:
    """Normalise la MAC en majuscules avec deux-points."""
    return mac.strip().upper()


class BluetoothDeviceCreate(BaseModel):
    """Schéma pour associer un appareil BT à un utilisateur."""
    user_id: int = Field(..., description="ID de l'utilisateur (jean, mehdi, …)")
    mac_address: str = Field(..., min_length=17, max_length=17, description="Adresse MAC (AA:BB:CC:DD:EE:FF)")
    device_name: str | None = Field(None, max_length=100, description="Nom du device (ex: Galaxy J7 de Jean)")
    device_type: str | None = Field(None, max_length=50, description="Type: phone, watch, headphones, etc.")

    def normalize_mac(self) -> str:
        return _normalize_mac(self.mac_address)


class BluetoothDeviceResponse(BaseModel):
    """Schéma de réponse pour un appareil Bluetooth."""
    id: int
    user_id: int
    username: str
    mac_address: str
    device_name: str | None
    device_type: str | None
    is_active: bool


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
        user = db.query(UserModel).filter(UserModel.id == d.user_id).first()
        result.append({
            "id": d.id,
            "user_id": d.user_id,
            "username": user.username if user else "?",
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
    existing = db.query(BluetoothDevice).filter(BluetoothDevice.mac_address == mac).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cette adresse MAC est déjà associée à un utilisateur (id={existing.user_id})",
        )
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
