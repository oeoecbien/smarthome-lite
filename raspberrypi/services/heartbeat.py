"""
Service de heartbeat périodique pour indiquer que le Raspberry Pi est en ligne.
"""

import logging
import threading
import time

import config
from services.backend_client import BackendClient

logger = logging.getLogger(__name__)


class HeartbeatService:
    """
    Service qui envoie périodiquement un heartbeat au backend
    pour indiquer que le Raspberry Pi est en ligne.
    """
    
    def __init__(self, backend_client: BackendClient):
        self.backend_client = backend_client
        self.interval = config.HEARTBEAT_INTERVAL
        self.thread = None
        self.running = False
    
    def start(self):
        """Démarre le service de heartbeat."""
        if self.running:
            logger.warning("Heartbeat service déjà démarré")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()
        logger.info(f"Heartbeat service démarré (intervalle: {self.interval}s)")
    
    def stop(self):
        """Arrête le service de heartbeat."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Heartbeat service arrêté")
    
    def _heartbeat_loop(self):
        """Boucle principale du heartbeat."""
        while self.running:
            try:
                success = self.backend_client.send_heartbeat()
                if success:
                    logger.debug("Heartbeat envoyé avec succès")
                else:
                    logger.warning("Échec du heartbeat")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du heartbeat: {e}")
            
            # Attendre l'intervalle avant le prochain heartbeat
            time.sleep(self.interval)
