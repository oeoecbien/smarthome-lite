"""
Client HTTP pour communication avec le backend.
"""

import logging
import time
import requests
from typing import Optional, Dict, Any
from queue import Queue, Empty
import threading

import config

logger = logging.getLogger(__name__)


class BackendClient:
    """
    Client HTTP pour communiquer avec le backend FastAPI.
    Gère l'authentification, les timeouts, les reconnexions et la queue de messages.
    """
    
    def __init__(self):
        self.backend_url = config.BACKEND_URL.rstrip('/')
        self.api_key = config.API_KEY
        self.timeout = config.BACKEND_TIMEOUT
        self.retry_attempts = config.BACKEND_RETRY_ATTEMPTS
        self.retry_delay = config.BACKEND_RETRY_DELAY
        
        # Queue pour stocker les événements en cas de perte de connexion
        self.event_queue = Queue()
        
        # Thread pour traiter la queue en arrière-plan
        self.queue_thread = None
        self.queue_running = False
        
        # Headers par défaut
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def start_queue_processor(self):
        """Démarre le thread de traitement de la queue."""
        if not self.queue_running:
            self.queue_running = True
            self.queue_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.queue_thread.start()
            logger.info("Queue processor démarré")
    
    def stop_queue_processor(self):
        """Arrête le thread de traitement de la queue."""
        self.queue_running = False
        if self.queue_thread:
            self.queue_thread.join(timeout=5)
            logger.info("Queue processor arrêté")
    
    def _process_queue(self):
        """Traite les événements en attente dans la queue."""
        while self.queue_running:
            try:
                # Récupérer un événement de la queue (timeout 1 seconde)
                try:
                    event = self.event_queue.get(timeout=1)
                except Empty:
                    continue
                
                # Tenter d'envoyer l'événement
                success = self._send_event_direct(event)
                
                if success:
                    self.event_queue.task_done()
                    logger.debug(f"Événement envoyé depuis la queue: {event.get('type', 'unknown')}")
                else:
                    # Remettre l'événement dans la queue pour réessayer plus tard
                    self.event_queue.put(event)
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"Erreur dans le traitement de la queue: {e}")
                time.sleep(self.retry_delay)
    
    def _send_event_direct(self, event: Dict[str, Any]) -> bool:
        """
        Envoie un événement directement au backend (sans queue).
        
        Returns:
            True si succès, False sinon
        """
        endpoint = event.get("endpoint")
        data = event.get("data")
        
        if not endpoint:
            logger.error("Événement sans endpoint")
            return False
        
        url = f"{self.backend_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    url,
                    json=data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.debug(f"Événement envoyé avec succès: {endpoint}")
                return True
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout lors de l'envoi à {endpoint} (tentative {attempt + 1}/{self.retry_attempts})")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Erreur de connexion à {endpoint} (tentative {attempt + 1}/{self.retry_attempts})")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"Erreur HTTP {e.response.status_code} lors de l'envoi à {endpoint}: {e}")
                return False  # Ne pas réessayer pour les erreurs HTTP (4xx, 5xx)
                
            except Exception as e:
                logger.error(f"Erreur inattendue lors de l'envoi à {endpoint}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
        
        return False
    
    def send_presence_detection(self) -> bool:
        """
        Envoie une détection de présence au backend.
        
        Returns:
            True si envoyé avec succès, False sinon
        """
        event = {
            "type": "presence",
            "endpoint": "/api/presence",
            "data": {}
        }
        
        # Tenter d'envoyer directement
        if self._send_event_direct(event):
            return True
        
        # Si échec, mettre dans la queue
        self.event_queue.put(event)
        logger.info("Détection de présence mise en queue")
        return False
    
    def send_light_reading(self, lux_value: float) -> bool:
        """
        Envoie une mesure de luminosité au backend.
        
        Args:
            lux_value: Valeur de luminosité en lux
            
        Returns:
            True si envoyé avec succès, False sinon
        """
        event = {
            "type": "light_reading",
            "endpoint": "/api/light-readings",
            "data": {
                "lux_value": lux_value
            }
        }
        
        # Tenter d'envoyer directement
        if self._send_event_direct(event):
            return True
        
        # Si échec, mettre dans la queue
        self.event_queue.put(event)
        logger.info(f"Mesure de luminosité mise en queue: {lux_value} lux")
        return False
    
    def send_heartbeat(self) -> bool:
        """
        Envoie un heartbeat au backend pour indiquer que le Raspberry Pi est en ligne.
        
        Note: Le backend met à jour automatiquement is_online via le heartbeat.
        Cette méthode peut être étendue si un endpoint dédié est créé.
        
        Returns:
            True si succès, False sinon
        """
        # Pour l'instant, le heartbeat est géré implicitement via les autres appels
        # Si un endpoint dédié est créé, l'utiliser ici
        try:
            # Test de connectivité simple
            response = requests.get(
                f"{self.backend_url}/health",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.debug(f"Heartbeat échoué: {e}")
            return False
    
    def get_queue_size(self) -> int:
        """Retourne le nombre d'événements en attente dans la queue."""
        return self.event_queue.qsize()
