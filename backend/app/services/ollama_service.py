"""
Service client pour l'API Ollama (IA générative).
"""

import logging
import httpx
import time
from typing import Optional, Dict, List, Any
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Service pour communiquer avec le serveur Ollama et générer du texte.
    """
    
    def __init__(self):
        """Initialise le service Ollama."""
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout
        self.enabled = self.base_url is not None and self.base_url.strip() != ""
        
        if not self.enabled:
            logger.warning("Ollama non configuré (OLLAMA_BASE_URL non défini)")
        else:
            logger.info(f"Ollama service initialisé: {self.base_url} (modèle: {self.model})")
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Effectue une requête HTTP vers l'API Ollama.
        
        Args:
            endpoint: Endpoint de l'API (ex: "/api/generate")
            data: Données JSON à envoyer
            
        Returns:
            Réponse JSON ou None en cas d'erreur
        """
        if not self.enabled:
            logger.debug("Ollama non configuré, requête ignorée")
            return None
        
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.warning(f"Timeout lors de la requête Ollama: {endpoint}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"Erreur HTTP lors de la requête Ollama: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la requête Ollama: {e}")
            return None
    
    def generate_text(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """
        Génère du texte via Ollama.
        
        Args:
            prompt: Prompt à envoyer au modèle
            model: Modèle à utiliser (par défaut: self.model)
            
        Returns:
            Texte généré ou None en cas d'erreur
        """
        if not self.enabled:
            return None
        
        model_to_use = model or self.model
        
        data = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": False
        }
        
        response = self._make_request("/api/generate", data)
        
        if response and "response" in response:
            return response["response"]
        
        return None
    
    def generate_scenario_description(self, scenario_data: Dict[str, Any]) -> str:
        """
        Génère une description intelligente d'un scénario détecté.
        
        Args:
            scenario_data: Dict avec les métadonnées du scénario
                (heure, luminosité, présence, scénario, etc.)
            
        Returns:
            Description textuelle ou description par défaut si Ollama indisponible
        """
        if not self.enabled:
            # Description par défaut
            scenario_names = {0: "Journée", 1: "Nuit", 2: "Absence", 3: "Soirée"}
            scenario = scenario_data.get("scenario", 0)
            return f"Scénario {scenario_names.get(scenario, 'Inconnu')} détecté."
        
        # Construire le prompt
        hour = scenario_data.get("hour", 12)
        lux_value = scenario_data.get("lux_value", 0)
        presence = scenario_data.get("presence_detected", False)
        scenario = scenario_data.get("scenario", 0)
        scenario_names = {0: "Journée", 1: "Nuit", 2: "Absence", 3: "Soirée"}
        
        prompt = (
            f"Décris en français de manière naturelle et concise ce scénario domotique :\n"
            f"- Heure : {hour}h\n"
            f"- Luminosité ambiante : {lux_value:.0f} lux\n"
            f"- Présence détectée : {'Oui' if presence else 'Non'}\n"
            f"- Scénario : {scenario_names.get(scenario, 'Inconnu')}\n\n"
            f"Génère une description courte (2-3 phrases maximum) de ce contexte."
        )
        
        result = self.generate_text(prompt)
        
        if result:
            return result.strip()
        else:
            # Fallback
            return f"Scénario {scenario_names.get(scenario, 'Inconnu')} détecté à {hour}h."
    
    def parse_rule_from_text(self, user_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse une règle en langage naturel et retourne une structure JSON.
        
        Args:
            user_text: Texte de la règle en langage naturel
                (ex: "Allume la lumière du salon à 19h")
            
        Returns:
            Dict avec la structure de la règle ou None en cas d'erreur
        """
        if not self.enabled:
            logger.warning("Ollama non disponible pour parsing de règle")
            return None
        
        prompt = (
            f"Extrais les informations de cette règle domotique et retourne uniquement du JSON valide :\n"
            f"'{user_text}'\n\n"
            f"Retourne un JSON avec les champs suivants :\n"
            f"- conditions : liste des conditions (ex: [{{\"type\": \"time\", \"value\": \"19:00\"}}])\n"
            f"- actions : liste des actions (ex: [{{\"type\": \"device_state\", \"device\": \"salon\", \"state\": true}}])\n"
            f"Retourne uniquement le JSON, sans texte supplémentaire."
        )
        
        result = self.generate_text(prompt)
        
        if not result:
            return None
        
        # Essayer de parser le JSON depuis la réponse
        try:
            import json
            # Extraire le JSON de la réponse (peut contenir du texte autour)
            # Chercher le premier { et le dernier }
            start = result.find("{")
            end = result.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = result[start:end]
                parsed = json.loads(json_str)
                return parsed
        except Exception as e:
            logger.error(f"Erreur lors du parsing JSON de la réponse Ollama: {e}")
            logger.debug(f"Réponse Ollama: {result}")
        
        return None
    
    def generate_recommendations(self, user_history: Dict[str, Any]) -> List[str]:
        """
        Génère des recommandations personnalisées basées sur l'historique utilisateur.
        
        Args:
            user_history: Dict avec l'historique (habitudes, consommation, etc.)
            
        Returns:
            Liste de recommandations textuelles
        """
        if not self.enabled:
            return []
        
        # Construire le prompt avec l'historique
        prompt = (
            f"Analyse cet historique d'utilisation domotique et génère 3-5 recommandations "
            f"personnalisées pour optimiser l'utilisation et réduire la consommation énergétique :\n\n"
            f"Historique :\n"
        )
        
        # Ajouter des informations pertinentes de l'historique
        if "average_brightness" in user_history:
            prompt += f"- Intensité lumineuse moyenne : {user_history['average_brightness']:.0f}%\n"
        if "most_active_hours" in user_history:
            prompt += f"- Heures les plus actives : {', '.join(map(str, user_history['most_active_hours']))}\n"
        if "energy_consumption" in user_history:
            prompt += f"- Consommation énergétique : {user_history['energy_consumption']:.2f} kWh\n"
        
        prompt += "\nGénère des recommandations concises et actionnables (une par ligne)."
        
        result = self.generate_text(prompt)
        
        if not result:
            return []
        
        # Parser les recommandations (une par ligne)
        recommendations = [
            line.strip()
            for line in result.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        
        return recommendations[:5]  # Limiter à 5 recommandations
