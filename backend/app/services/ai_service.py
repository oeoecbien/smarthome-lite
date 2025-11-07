"""
Service d'Intelligence Artificielle pour classification de scénarios.

Ce service utilise un Decision Tree Classifier (scikit-learn) pour classer
automatiquement le contexte d'utilisation en quatre scénarios :
- Day (0) : Journée normale
- Night (1) : Période nocturne
- Away (2) : Absence prolongée
- Evening (3) : Soirée détente
"""

import logging
import os
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import joblib
import numpy as np

from app.config import settings
from app.models import Device, Presence, TrainingData

logger = logging.getLogger(__name__)

# Modèle global chargé au démarrage
_model = None
_model_loaded = False


class AIService:
    """
    Service de classification de scénarios utilisant un Decision Tree.
    """
    
    def __init__(self):
        """Initialise le service et charge le modèle si disponible."""
        self.model = None
        self.load_model()
    
    def load_model(self) -> bool:
        """
        Charge le modèle Decision Tree depuis le fichier pickle.
        
        Returns:
            bool: True si le modèle a été chargé, False sinon
        """
        global _model, _model_loaded
        
        if _model_loaded and _model is not None:
            self.model = _model
            return True
        
        model_path = settings.ml_model_path
        
        # Créer le répertoire s'il n'existe pas
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        if not os.path.exists(model_path):
            logger.warning(f"Modèle IA non trouvé: {model_path}")
            logger.info("Utilisation d'un scénario par défaut basé sur l'heure")
            _model_loaded = True
            return False
        
        try:
            _model = joblib.load(model_path)
            self.model = _model
            _model_loaded = True
            logger.info(f"Modèle IA chargé depuis {model_path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle IA: {e}")
            _model_loaded = True
            return False
    
    def classify(
        self,
        hour: int,
        day_of_week: int,
        presence_detected: bool,
        light_on: bool
    ) -> Dict[str, any]:
        """
        Classe le contexte actuel en un scénario.
        
        Args:
            hour: Heure actuelle (0-23)
            day_of_week: Jour de la semaine (0=Lundi, 6=Dimanche)
            presence_detected: Présence détectée dans les 5 dernières minutes
            light_on: Au moins une lampe est allumée
        
        Returns:
            Dict avec:
                - scenario: Numéro du scénario (0-3)
                - scenario_name: Nom du scénario
                - confidence: Confiance (si modèle disponible)
                - method: "ml" ou "fallback"
        """
        scenario_names = {
            0: "Day",
            1: "Night",
            2: "Away",
            3: "Evening"
        }
        
        # Si le modèle est disponible, l'utiliser
        if self.model is not None:
            try:
                # Préparer les features
                features = np.array([[
                    hour,
                    day_of_week,
                    1 if presence_detected else 0,
                    1 if light_on else 0
                ]])
                
                # Prédiction
                scenario = int(self.model.predict(features)[0])
                
                # Probabilités (si disponibles)
                if hasattr(self.model, 'predict_proba'):
                    probabilities = self.model.predict_proba(features)[0]
                    confidence = float(max(probabilities))
                else:
                    confidence = 1.0
                
                return {
                    "scenario": scenario,
                    "scenario_name": scenario_names.get(scenario, "Unknown"),
                    "confidence": confidence,
                    "method": "ml"
                }
            except Exception as e:
                logger.error(f"Erreur lors de la classification ML: {e}")
                # Fallback sur la méthode par défaut
        
        # Méthode fallback basée sur l'heure
        return self._classify_fallback(hour, presence_detected, light_on)
    
    def _classify_fallback(
        self,
        hour: int,
        presence_detected: bool,
        light_on: bool
    ) -> Dict[str, any]:
        """
        Classification par défaut basée sur des règles simples.
        
        Args:
            hour: Heure actuelle (0-23)
            presence_detected: Présence détectée
            light_on: Lumière allumée
        
        Returns:
            Dict avec scenario, scenario_name, confidence, method
        """
        scenario_names = {
            0: "Day",
            1: "Night",
            2: "Away",
            3: "Evening"
        }
        
        # Règles simples
        if 6 <= hour < 18:
            # Journée
            if not presence_detected and not light_on:
                scenario = 2  # Away
            else:
                scenario = 0  # Day
        elif 18 <= hour < 23:
            # Soirée
            scenario = 3  # Evening
        else:
            # Nuit
            scenario = 1  # Night
        
        return {
            "scenario": scenario,
            "scenario_name": scenario_names.get(scenario, "Unknown"),
            "confidence": 0.7,  # Confiance moyenne pour fallback
            "method": "fallback"
        }
    
    def get_current_scenario(
        self,
        db: Session,
        raspberry_pi_id: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Obtient le scénario actuel en analysant le contexte.
        
        Args:
            db: Session de base de données
            raspberry_pi_id: ID du Raspberry Pi (optionnel, pour filtrer)
        
        Returns:
            Dict avec scenario, scenario_name, confidence, method, context
        """
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()  # 0=Lundi, 6=Dimanche
        
        # Vérifier la présence dans les 5 dernières minutes
        from datetime import timedelta
        five_minutes_ago = now - timedelta(minutes=5)
        
        presence_query = db.query(Presence).filter(
            Presence.detected_at >= five_minutes_ago
        )
        if raspberry_pi_id:
            presence_query = presence_query.filter(
                Presence.raspberry_pi_id == raspberry_pi_id
            )
        
        presence_detected = presence_query.first() is not None
        
        # Vérifier si au moins une lampe est allumée
        device_query = db.query(Device).filter(
            Device.type.in_(["light", "dimmer"]),
            Device.state == True
        )
        if raspberry_pi_id:
            device_query = device_query.filter(
                Device.raspberry_pi_id == raspberry_pi_id
            )
        
        light_on = device_query.first() is not None
        
        # Classification
        result = self.classify(hour, day_of_week, presence_detected, light_on)
        
        # Ajouter le contexte
        result["context"] = {
            "hour": hour,
            "day_of_week": day_of_week,
            "presence_detected": presence_detected,
            "light_on": light_on,
            "raspberry_pi_id": raspberry_pi_id
        }
        
        return result


# Instance globale du service
_ai_service_instance = None


def get_ai_service() -> AIService:
    """
    Obtient l'instance globale du service IA (singleton).
    
    Returns:
        AIService: Instance du service
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance

