#!/usr/bin/env python3
"""
Script de détection de présence Bluetooth sur le RPi capteur.

Scanne périodiquement les appareils BLE à portée et envoie chaque MAC détectée
au backend (POST /api/presence). Le backend enregistre la présence en BDD et
associe l'utilisateur si la MAC est dans bluetooth_devices (jean, mehdi…).
L'IA utilise ensuite presence_detected pour le scénario.

À lancer sur le RPi capteur (ex. 10.109.150.133). Configuration via .env à la
racine du projet (sae_s5/.env) : BACKEND_URL, RASPBERRY_API_KEY.

Usage:
  cd sae_s5 && python raspberry/bt_presence_scan.py
  # ou sur le RPi après déploiement :
  export BACKEND_URL=http://10.109.150.75:8000
  export RASPBERRY_API_KEY=smarthome2025
  python3 bt_presence_scan.py
"""

import asyncio
import logging
import os
import re
import sys
from pathlib import Path

# Charger .env à la racine du projet (sae_s5)
_root = Path(__file__).resolve().parent.parent
_env = _root / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(_env)
except ImportError:
    pass

BACKEND_URL = os.environ.get("BACKEND_URL", "").rstrip("/")
RASPBERRY_API_KEY = os.environ.get("RASPBERRY_API_KEY", "").strip()
SCAN_INTERVAL_SEC = int(os.environ.get("BT_PRESENCE_SCAN_INTERVAL", "45"))
SCAN_TIMEOUT_SEC = int(os.environ.get("BT_PRESENCE_SCAN_TIMEOUT", "10"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Format MAC backend : AA:BB:CC:DD:EE:FF
MAC_COLON = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def normalize_mac(address: str) -> str | None:
    """Retourne la MAC au format AA:BB:CC:DD:EE:FF ou None si invalide."""
    if not address or len(address) < 17:
        return None
    # Bleak peut renvoyer AA:BB:CC:DD:EE:FF ou AABBCCDDEEFF
    s = address.replace("-", ":").upper()
    if ":" not in s and len(s) == 12:
        s = ":".join(s[i : i + 2] for i in range(0, 12, 2))
    if not MAC_COLON.match(s):
        return None
    return s


async def scan_ble() -> list[tuple[str, int]]:
    """Retourne une liste de (mac, rssi) pour chaque device BLE détecté."""
    try:
        from bleak import BleakScanner
    except ImportError:
        logger.warning("bleak non installé: pip install bleak")
        return []

    devices = await BleakScanner.discover(timeout=float(SCAN_TIMEOUT_SEC))
    result = []
    for d in devices:
        mac = normalize_mac(d.address)
        if mac:
            rssi = getattr(d, "rssi", None)
            if rssi is None and hasattr(d, "metadata") and isinstance(d.metadata, dict):
                rssi = d.metadata.get("rssi")
            result.append((mac, int(rssi) if rssi is not None else -70))
    return result


def send_presence(mac: str, signal_strength: int = -70) -> bool:
    """Envoie une détection de présence au backend. Retourne True si succès."""
    if not BACKEND_URL or not RASPBERRY_API_KEY:
        logger.error("BACKEND_URL et RASPBERRY_API_KEY doivent être définis")
        return False
    import requests
    url = f"{BACKEND_URL}/api/presence"
    headers = {
        "X-API-Key": RASPBERRY_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"device_mac_address": mac, "signal_strength": signal_strength}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=5)
        if r.status_code in (200, 201):
            return True
        logger.warning("POST %s -> %s %s", url, r.status_code, r.text[:200])
    except Exception as e:
        logger.warning("POST presence failed: %s", e)
    return False


async def run_loop():
    if not BACKEND_URL or not RASPBERRY_API_KEY:
        logger.error("Configurez BACKEND_URL et RASPBERRY_API_KEY (fichier .env ou variables d'environnement)")
        sys.exit(1)
    logger.info("Démarrage scan BT -> %s (intervalle %s s)", BACKEND_URL, SCAN_INTERVAL_SEC)
    while True:
        try:
            seen = await scan_ble()
            for mac, rssi in seen:
                if send_presence(mac, rssi):
                    logger.info("Présence envoyée: %s (RSSI %s)", mac, rssi)
            if not seen:
                logger.debug("Aucun appareil BLE détecté")
        except Exception as e:
            logger.exception("Erreur scan: %s", e)
        await asyncio.sleep(SCAN_INTERVAL_SEC)


def main():
    asyncio.run(run_loop())


if __name__ == "__main__":
    main()
