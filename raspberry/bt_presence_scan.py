#!/usr/bin/env python3
"""
Script de détection de présence Bluetooth sur le RPi capteur.

Deux modes de scan (BT_PRESENCE_MODE) :
- callback (défaut) : scan continu avec callback — réaction dès qu’un appareil
  envoie une annonce BLE. Plus réactif et moins gourmand qu’un scan fixe long.
- discover : scan fixe puis pause (comportement legacy, intervalle + timeout).

Dans les deux cas, les MAC détectées sont envoyées au backend (POST /api/presence).
Le backend enregistre la présence en BDD et associe l’utilisateur si la MAC est
dans bluetooth_devices. L’IA utilise presence_detected pour le scénario.

À lancer sur le RPi capteur. Configuration via .env à la racine (sae_s5/.env) :
BACKEND_URL, RASPBERRY_API_KEY.

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
import threading
import time
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

# Mode: "callback" = scan continu avec callback (recommandé), "discover" = scan fixe puis pause
BT_PRESENCE_MODE = os.environ.get("BT_PRESENCE_MODE", "callback").strip().lower()
if BT_PRESENCE_MODE not in ("callback", "discover"):
    BT_PRESENCE_MODE = "callback"

# Mode callback : pas de timeout global, le scan tourne en continu
# Mode discover : intervalle entre deux scans et durée d’un scan
SCAN_INTERVAL_SEC = int(os.environ.get("BT_PRESENCE_SCAN_INTERVAL", "45"))
SCAN_TIMEOUT_SEC = int(os.environ.get("BT_PRESENCE_SCAN_TIMEOUT", "10"))

# Ne rapporter que les appareils avec RSSI >= ce seuil (ex. -85 = plus proches seulement)
# -90 à -70 typique en intérieur ; -85 = dans la pièce, -95 = pièce d’à côté
BT_PRESENCE_RSSI_MIN = int(os.environ.get("BT_PRESENCE_RSSI_MIN", "-85"))

# Debounce local : ne pas renvoyer la même MAC au backend avant ce délai (secondes)
BT_PRESENCE_DEBOUNCE_SEC = int(os.environ.get("BT_PRESENCE_DEBOUNCE_SEC", "30"))

# Rafraîchir la liste des MAC connues (known-macs) toutes les N secondes (0 = seulement au démarrage)
BT_PRESENCE_KNOWN_MACS_REFRESH_SEC = int(os.environ.get("BT_PRESENCE_KNOWN_MACS_REFRESH_SEC", "300"))

# Si True, n’envoyer que les MAC déjà dans bluetooth_devices
PRESENCE_ONLY_KNOWN_MACS = os.environ.get("PRESENCE_ONLY_KNOWN_MACS", "0").strip().lower() in ("1", "true", "yes")

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
    s = address.replace("-", ":").upper()
    if ":" not in s and len(s) == 12:
        s = ":".join(s[i : i + 2] for i in range(0, 12, 2))
    if not MAC_COLON.match(s):
        return None
    return s


def _address_to_mac(address: str) -> str | None:
    """Convertit l'adresse BLE en format MAC 17 caractères, ou None si invalide."""
    if not address or len(address) < 12:
        return None
    s = address.strip().replace("-", ":").replace(" ", "").upper()
    if ":" not in s and len(s) == 12 and all(c in "0123456789ABCDEF" for c in s):
        s = ":".join(s[i : i + 2] for i in range(0, 12, 2))
    if len(s) != 17 or not MAC_COLON.match(s):
        return None
    return s


def fetch_known_macs() -> set[str]:
    """Récupère la liste des MAC enregistrées (Admin → Appareils BT). Vide si désactivé ou erreur."""
    if not BACKEND_URL or not RASPBERRY_API_KEY:
        return set()
    import requests
    url = f"{BACKEND_URL}/api/presence/known-macs"
    headers = {"X-API-Key": RASPBERRY_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return set(data.get("mac_addresses", []))
    except Exception as e:
        logger.debug("known-macs: %s", e)
    return set()


def send_presence(mac: str, signal_strength: int = -70, device_name: str | None = None) -> tuple[bool, bool]:
    """
    Envoie une détection au backend. Retourne (succès, enregistré).
    Bloquant (requests) : à appeler via asyncio.to_thread en mode callback.
    """
    if not BACKEND_URL or not RASPBERRY_API_KEY:
        logger.error("BACKEND_URL et RASPBERRY_API_KEY doivent être définis")
        return False, False
    import requests
    url = f"{BACKEND_URL}/api/presence"
    headers = {
        "X-API-Key": RASPBERRY_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"device_mac_address": mac, "signal_strength": signal_strength}
    if device_name:
        payload["device_name"] = device_name[:100]
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=5)
        if r.status_code in (200, 201):
            data = r.json() if r.text else {}
            recorded = data.get("recorded", r.status_code == 201)
            return True, recorded
        logger.warning("POST %s -> %s %s", url, r.status_code, (r.text or "")[:200])
    except Exception as e:
        logger.warning("POST presence failed: %s", e)
    return False, False


# --- Mode discover (legacy) : scan fixe puis pause ---

async def scan_ble() -> list[tuple[str, int, str | None]]:
    """Retourne une liste de (mac, rssi, name) pour chaque device BLE détecté."""
    try:
        from bleak import BleakScanner
    except ImportError:
        logger.warning("bleak non installé: pip install bleak")
        return []

    devices = await BleakScanner.discover(timeout=float(SCAN_TIMEOUT_SEC))
    result = []
    for d in devices:
        mac = normalize_mac(d.address) or _address_to_mac(d.address)
        if not mac:
            continue
        rssi = getattr(d, "rssi", None)
        if rssi is None and hasattr(d, "metadata") and isinstance(d.metadata, dict):
            rssi = d.metadata.get("rssi")
        rssi = int(rssi) if rssi is not None else -70
        name = (getattr(d, "name", None) or "").strip() or None
        if name and len(name) > 100:
            name = name[:97] + "..."
        result.append((mac, rssi, name))
    return result


async def run_loop_discover(known_macs: set[str]):
    """Boucle legacy : scan discover(timeout) puis sleep(interval)."""
    while True:
        try:
            seen = await scan_ble()
            if PRESENCE_ONLY_KNOWN_MACS and known_macs:
                seen = [(mac, rssi, name) for mac, rssi, name in seen if mac in known_macs]
            for mac, rssi, name in seen:
                if rssi < BT_PRESENCE_RSSI_MIN:
                    continue
                ok, recorded = await asyncio.to_thread(send_presence, mac, rssi, name)
                if ok and recorded:
                    logger.info("Présence enregistrée: %s (RSSI %s)%s", mac, rssi, f" [{name}]" if name else "")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("Erreur scan: %s", e)
        await asyncio.sleep(SCAN_INTERVAL_SEC)


# --- Mode callback : scan continu, réaction à chaque annonce ---

# Dernière fois qu’on a envoyé cette MAC au backend (debounce local)
# Lock threading car le callback peut être appelé depuis un thread BlueZ
_last_sent: dict[str, float] = {}
_debounce_lock = threading.Lock()


def _should_send_mac(mac: str) -> bool:
    """True si on peut envoyer cette MAC (debounce écoulé)."""
    now = time.monotonic()
    with _debounce_lock:
        last = _last_sent.get(mac, 0)
        if now - last < BT_PRESENCE_DEBOUNCE_SEC:
            return False
        _last_sent[mac] = now
        return True


def _detection_callback(device, advertisement_data):
    """
    Appelé à chaque annonce BLE (mode callback).
    Filtre MAC, RSSI, known_macs ; debounce ; envoi en thread pour ne pas bloquer.
    """
    mac = normalize_mac(device.address) or _address_to_mac(device.address)
    if not mac:
        return
    rssi = getattr(advertisement_data, "rssi", None)
    if rssi is None and hasattr(device, "rssi"):
        rssi = device.rssi
    rssi = int(rssi) if rssi is not None else -70
    if rssi < BT_PRESENCE_RSSI_MIN:
        return
    name = (getattr(device, "name", None) or getattr(advertisement_data, "local_name", None) or "").strip() or None
    if name and len(name) > 100:
        name = name[:97] + "..."

    # Filtre known_macs (lecture partagée, pas de lock pour éviter blocage)
    known = _known_macs_ref
    if PRESENCE_ONLY_KNOWN_MACS and known and mac not in known:
        return
    if not _should_send_mac(mac):
        return

    _schedule_send(mac, rssi, name)


# Référence partagée pour known_macs et event loop (remplies par run_loop_callback)
_known_macs_ref: set[str] = set()
_main_loop: asyncio.AbstractEventLoop | None = None


async def _send_presence_async(mac: str, rssi: int, name: str | None):
    ok, recorded = await asyncio.to_thread(send_presence, mac, rssi, name)
    if ok and recorded:
        logger.info("Présence enregistrée: %s (RSSI %s)%s", mac, rssi, f" [{name}]" if name else "")


def _schedule_send(mac: str, rssi: int, name: str | None):
    """Planifie l'envoi sur la boucle principale (callback peut être dans un autre thread)."""
    loop = _main_loop
    if loop is None or not loop.is_running():
        return
    asyncio.run_coroutine_threadsafe(_send_presence_async(mac, rssi, name), loop)


async def _refresh_known_macs_periodically():
    """Met à jour la liste des MAC connues périodiquement."""
    if not PRESENCE_ONLY_KNOWN_MACS or BT_PRESENCE_KNOWN_MACS_REFRESH_SEC <= 0:
        return
    while True:
        await asyncio.sleep(BT_PRESENCE_KNOWN_MACS_REFRESH_SEC)
        try:
            new_macs = await asyncio.to_thread(fetch_known_macs)
            _known_macs_ref.clear()
            _known_macs_ref.update(new_macs)
            logger.debug("Known MACs rafraîchies: %s", len(new_macs))
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.debug("refresh known_macs: %s", e)


async def run_loop_callback():
    """Scan continu avec BleakScanner(detection_callback=...)."""
    try:
        from bleak import BleakScanner
    except ImportError:
        logger.warning("bleak non installé: pip install bleak")
        return

    global _known_macs_ref, _main_loop
    _main_loop = asyncio.get_running_loop()
    if PRESENCE_ONLY_KNOWN_MACS:
        _known_macs_ref = await asyncio.to_thread(fetch_known_macs)
        logger.info(
            "Scan BT continu (callback) -> %s. MAC connues: %s. RSSI >= %s, debounce %ss",
            BACKEND_URL, list(_known_macs_ref) or "(aucune)", BT_PRESENCE_RSSI_MIN, BT_PRESENCE_DEBOUNCE_SEC
        )
    else:
        logger.info(
            "Scan BT continu (callback) -> %s. Toutes les MAC. RSSI >= %s, debounce %ss",
            BACKEND_URL, BT_PRESENCE_RSSI_MIN, BT_PRESENCE_DEBOUNCE_SEC
        )

    refresh_task = asyncio.create_task(_refresh_known_macs_periodically())
    try:
        scanner = BleakScanner(detection_callback=_detection_callback)
        async with scanner:
            await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        refresh_task.cancel()
        try:
            await refresh_task
        except asyncio.CancelledError:
            pass


async def run_loop():
    if not BACKEND_URL or not RASPBERRY_API_KEY:
        logger.error("Configurez BACKEND_URL et RASPBERRY_API_KEY (fichier .env ou variables d'environnement)")
        sys.exit(1)

    if BT_PRESENCE_MODE == "discover":
        known_macs = set()
        if PRESENCE_ONLY_KNOWN_MACS:
            known_macs = await asyncio.to_thread(fetch_known_macs)
            logger.info(
                "Démarrage scan BT (discover) -> %s (intervalle %s s, timeout %s s). MAC connues uniquement: %s",
                BACKEND_URL, SCAN_INTERVAL_SEC, SCAN_TIMEOUT_SEC, list(known_macs) or "(aucune)"
            )
        else:
            logger.info(
                "Démarrage scan BT (discover) -> %s (intervalle %s s). Toutes les MAC envoyées",
                BACKEND_URL, SCAN_INTERVAL_SEC
            )
        await run_loop_discover(known_macs)
    else:
        await run_loop_callback()


def main():
    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        logger.info("Arrêt demandé.")
        sys.exit(0)


if __name__ == "__main__":
    main()
