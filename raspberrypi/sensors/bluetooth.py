"""
Module de gestion de la détection Bluetooth pour identification des personnes.
Scan Bluetooth périodique pour détection de présence.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta

try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    try:
        from bluetooth import bluetooth as bluetooth_module
        BLUETOOTH_AVAILABLE = True
    except ImportError:
        BLUETOOTH_AVAILABLE = False
        logging.warning("pybluez non disponible, utilisation de bleak en fallback")

# Fallback vers bleak si pybluez n'est pas disponible
if not BLUETOOTH_AVAILABLE:
    try:
        from bleak import BleakScanner
        BLEAK_AVAILABLE = True
    except ImportError:
        BLEAK_AVAILABLE = False
        logging.error("Aucune bibliothèque Bluetooth disponible (pybluez ou bleak)")

import config
from services.backend_client import BackendClient

logger = logging.getLogger(__name__)


class BluetoothSensor:
    """
    Gestion du scan Bluetooth pour détection de présence.
    
    Scanne périodiquement les devices Bluetooth à proximité et envoie
    les détections au backend avec l'adresse MAC et la force du signal (RSSI).
    """
    
    def __init__(self, backend_client: BackendClient):
        self.backend_client = backend_client
        self.thread = None
        self.running = False
        
        # Configuration
        self.scan_interval = getattr(config, 'BLUETOOTH_SCAN_INTERVAL', 30)  # Secondes entre chaque scan
        self.scan_duration = getattr(config, 'BLUETOOTH_SCAN_DURATION', 10)  # Durée du scan en secondes
        self.rssi_threshold = getattr(config, 'BLUETOOTH_RSSI_THRESHOLD', -80)  # RSSI minimum (dBm)
        self.known_devices = getattr(config, 'BLUETOOTH_KNOWN_DEVICES', [])  # Liste des MAC à surveiller (optionnel)
        
        # État
        self.last_detected_devices: Set[str] = set()  # MAC addresses détectées au dernier scan
        self.device_last_seen: Dict[str, datetime] = {}  # Dernière détection par MAC
        self.debounce_time = 60  # Secondes avant de considérer une absence
        
        logger.info(f"Capteur Bluetooth initialisé (scan toutes les {self.scan_interval}s)")
    
    def start(self):
        """Démarre la surveillance Bluetooth."""
        if self.running:
            logger.warning("Bluetooth sensor déjà démarré")
            return
        
        if not BLUETOOTH_AVAILABLE and not BLEAK_AVAILABLE:
            logger.error("Impossible de démarrer: aucune bibliothèque Bluetooth disponible")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.thread.start()
        logger.info("Surveillance Bluetooth démarrée")
    
    def stop(self):
        """Arrête la surveillance Bluetooth."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Surveillance Bluetooth arrêtée")
    
    def _scan_loop(self):
        """Boucle principale de scan Bluetooth."""
        while self.running:
            try:
                # Effectuer un scan
                devices = self._perform_scan()
                
                if devices:
                    self._process_detections(devices)
                
                # Attendre avant le prochain scan
                time.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Erreur lors du scan Bluetooth: {e}", exc_info=True)
                time.sleep(self.scan_interval)
    
    def _perform_scan(self) -> List[Dict[str, any]]:
        """
        Effectue un scan Bluetooth et retourne la liste des devices détectés.
        
        Returns:
            Liste de dicts avec 'mac_address' et 'rssi'
        """
        devices = []
        
        try:
            if BLUETOOTH_AVAILABLE:
                # Utiliser pybluez (Bluetooth Classic)
                logger.debug("Scan Bluetooth Classic (pybluez)...")
                nearby_devices = bluetooth.discover_devices(
                    duration=self.scan_duration,
                    lookup_names=False,
                    flush_cache=True
                )
                
                for mac_address in nearby_devices:
                    try:
                        # Obtenir le RSSI (force du signal)
                        rssi = bluetooth.read_rssi(mac_address)
                        if rssi is None:
                            rssi = -100  # Valeur par défaut si non disponible
                        
                        # Filtrer par RSSI threshold
                        if rssi >= self.rssi_threshold:
                            devices.append({
                                'mac_address': mac_address.upper(),
                                'rssi': rssi
                            })
                    except Exception as e:
                        logger.debug(f"Erreur lors de la lecture RSSI pour {mac_address}: {e}")
                        # Inclure quand même le device sans RSSI
                        devices.append({
                            'mac_address': mac_address.upper(),
                            'rssi': -100
                        })
            
            elif BLEAK_AVAILABLE:
                # Utiliser bleak (Bluetooth Low Energy)
                logger.debug("Scan Bluetooth Low Energy (bleak)...")
                import asyncio
                
                async def scan():
                    detected = []
                    scanner = BleakScanner()
                    found_devices = await scanner.discover(timeout=self.scan_duration)
                    
                    for device in found_devices:
                        if device.rssi and device.rssi >= self.rssi_threshold:
                            detected.append({
                                'mac_address': device.address.upper(),
                                'rssi': device.rssi
                            })
                    return detected
                
                # Exécuter le scan asynchrone
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                devices = loop.run_until_complete(scan())
                loop.close()
            
        except Exception as e:
            logger.error(f"Erreur lors du scan Bluetooth: {e}", exc_info=True)
        
        return devices
    
    def _process_detections(self, devices: List[Dict[str, any]]):
        """
        Traite les détections et envoie au backend.
        
        Args:
            devices: Liste des devices détectés
        """
        current_macs = {d['mac_address'] for d in devices}
        now = datetime.now()
        
        # Filtrer par known_devices si configuré
        if self.known_devices:
            current_macs = {mac for mac in current_macs if mac in self.known_devices}
        
        # Détecter les nouvelles présences (apparitions)
        new_devices = current_macs - self.last_detected_devices
        
        # Détecter les absences (disparitions après debounce_time)
        disappeared_devices = set()
        for mac in self.last_detected_devices - current_macs:
            if mac in self.device_last_seen:
                time_since_last_seen = (now - self.device_last_seen[mac]).total_seconds()
                if time_since_last_seen >= self.debounce_time:
                    disappeared_devices.add(mac)
        
        # Mettre à jour l'état
        for device in devices:
            mac = device['mac_address']
            if mac in current_macs:
                self.device_last_seen[mac] = now
        
        # Envoyer les nouvelles détections
        for device in devices:
            mac = device['mac_address']
            rssi = device['rssi']
            
            if mac in new_devices:
                logger.info(f"Device Bluetooth détecté: {mac} (RSSI: {rssi} dBm)")
                self.backend_client.send_bluetooth_detection(mac, rssi)
        
        # Mettre à jour la liste des devices détectés
        self.last_detected_devices = current_macs
        
        # Nettoyer les devices absents depuis trop longtemps
        expired_macs = {
            mac for mac, last_seen in self.device_last_seen.items()
            if (now - last_seen).total_seconds() > self.debounce_time * 2
        }
        for mac in expired_macs:
            self.device_last_seen.pop(mac, None)
            self.last_detected_devices.discard(mac)
    
    def get_current_devices(self) -> List[str]:
        """
        Retourne la liste des MAC addresses actuellement détectées.
        
        Returns:
            Liste des adresses MAC
        """
        return list(self.last_detected_devices)
