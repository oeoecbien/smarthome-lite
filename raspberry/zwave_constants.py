"""
Constantes et registre d'appareils Z-Wave.
Séparation : le client Z-Wave reste agnostique ; la reconnaissance des appareils
(manufacturerId, productType, productId → nom, modèle) est centralisée ici.
"""

from enum import IntEnum
from typing import Any, Dict, Optional


class CommandClass(IntEnum):
    """Command Classes Z-Wave (évite les chiffres magiques)."""
    MULTILEVEL_SWITCH = 38   # Dimmer / ampoule
    SENSOR_BINARY = 48      # Mouvement (MultiSensor 7)
    SENSOR_MULTILEVEL = 49  # Température, luminosité, humidité, UV
    BATTERY = 128


class MultilevelSensorType(IntEnum):
    """Types de capteur CC 49 (Multilevel Sensor)."""
    AIR_TEMPERATURE = 1
    ILLUMINANCE = 3
    HUMIDITY = 5
    ULTRAVIOLET = 27


# Propriétés courantes pour CC 38 (Multilevel Switch)
PROP_CURRENT_VALUE = "currentValue"
PROP_TARGET_VALUE = "targetValue"

# Niveau "ON" pour appareils 0-99 (ex. ABUS)
ON_LEVEL_FULL = 99


def _node_ids(node: Optional[Dict[str, Any]]) -> tuple:
    """Extrait (manufacturerId, productType, productId) depuis un nœud."""
    if not node:
        return (None, None, None)
    mid = node.get("manufacturerId") or node.get("manufacturer_id")
    pt = node.get("productType") or node.get("product_type")
    pid = node.get("productId") or node.get("product_id")
    if mid is not None and pt is not None and pid is not None:
        return (int(mid), int(pt), int(pid))
    dev = node.get("deviceConfig") or node.get("device_config") or {}
    if dev:
        mid = dev.get("manufacturerId") or dev.get("manufacturer_id")
        pt = dev.get("productType") or dev.get("product_type")
        pid = dev.get("productId") or dev.get("product_id")
        if mid is not None and pt is not None and pid is not None:
            return (int(mid), int(pt), int(pid))
    return (None, None, None)


# Registre : (manufacturer_id, product_type, product_id) → (device_type, device_name, device_model)
# Le client Z-Wave appelle device_info_from_node(node) et obtient ces infos sans logique marque.
DEVICE_REGISTRY: Dict[tuple, Dict[str, str]] = {
    (881, 2, 24): {
        "device_type": "aeotec_multisensor7",
        "device_name": "Aeotec MultiSensor 7",
        "device_model": "ZWA024",
    },
}


def device_info_from_node(node: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """
    Retourne device_type, device_name, device_model si le nœud est reconnu dans le registre.
    Sinon None. Le client Z-Wave reste agnostique ; la config est ici.
    """
    if not node:
        return None
    key = _node_ids(node)
    return DEVICE_REGISTRY.get(key)
