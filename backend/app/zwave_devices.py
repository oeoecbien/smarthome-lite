"""
Registre des appareils Z-Wave connus par le backend.

Permet d'identifier les nœuds (manufacturerId, productType, productId) et d'exposer
leurs capacités (capteurs, types de valeurs). Utilisé pour la documentation et
l'API capteurs (ex. Aeotec MultiSensor 7).
"""

from typing import Any, Dict, List, Optional

# Aeotec Ltd. MultiSensor 7 (ZWA024)
# Manufacturer ID: 881, Product Type: 2, Product ID: 24
# FW v1.6.7, SDK 7.12.2
AEOTEC_MULTISENSOR7 = {
    "manufacturer_id": 881,
    "manufacturer_name": "Aeotec Ltd.",
    "product_type": 2,
    "product_id": 24,
    "model": "ZWA024",
    "name": "MultiSensor 7",
    "full_name": "Aeotec MultiSensor 7",
    "description": "Capteur multi (mouvement, température, humidité, luminosité, UV, batterie)",
    "command_classes": {
        "binary_sensor": 48,   # Motion
        "multilevel_sensor": 49,  # Air temperature, Illuminance, Humidity, Ultraviolet
        "battery": 128,
        "configuration": 112,
        "notification": 113,
        "version": 134,
        "wake_up": 132,
    },
    "sensor_capabilities": [
        "motion",
        "temperature_c",
        "humidity",
        "illuminance_lux",
        "ultraviolet",
        "battery_percent",
    ],
}

# Registre : clé = (manufacturer_id, product_type, product_id)
ZWAVE_KNOWN_DEVICES: Dict[tuple, Dict[str, Any]] = {
    (AEOTEC_MULTISENSOR7["manufacturer_id"], AEOTEC_MULTISENSOR7["product_type"], AEOTEC_MULTISENSOR7["product_id"]): AEOTEC_MULTISENSOR7,
}


def get_known_device(manufacturer_id: int, product_type: int, product_id: int) -> Optional[Dict[str, Any]]:
    """Retourne la définition d'un appareil connu ou None."""
    key = (int(manufacturer_id), int(product_type), int(product_id))
    return ZWAVE_KNOWN_DEVICES.get(key)


def is_aeotec_multisensor7(manufacturer_id: int, product_type: int, product_id: int) -> bool:
    """Vérifie si l'appareil est un Aeotec MultiSensor 7 (ZWA024)."""
    dev = get_known_device(manufacturer_id, product_type, product_id)
    return dev is not None and dev.get("model") == "ZWA024"


def list_known_devices() -> List[Dict[str, Any]]:
    """Liste des appareils Z-Wave connus (pour doc / admin)."""
    return [
        {
            "manufacturer_id": d["manufacturer_id"],
            "manufacturer_name": d["manufacturer_name"],
            "product_type": d["product_type"],
            "product_id": d["product_id"],
            "model": d["model"],
            "name": d["name"],
            "full_name": d["full_name"],
            "sensor_capabilities": d.get("sensor_capabilities", []),
        }
        for d in ZWAVE_KNOWN_DEVICES.values()
    ]
