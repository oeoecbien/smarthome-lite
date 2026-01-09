"""
Service de régression pour prédiction d'intensité lumineuse optimale.
"""

import logging
import os
from typing import Dict, Optional
from datetime import datetime
import joblib
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# Modèle global chargé au démarrage
_regression_model = None
_regression_model_loaded = False


class RegressionService:
    """
    Service de régression pour prédire l'intensité lumineuse optimale.
    Utilise un Random Forest Regressor entraîné.
    """
    
    def __init__(self):
        """Initialise le service et charge le modèle si disponible."""
        self.model = None
        self.load_model()
    
    def load_model(self) -> bool:
        """
        Charge le modèle Random Forest Regressor depuis le fichier joblib.
        
        Returns:
            bool: True si le modèle a été chargé, False sinon
        """
        global _regression_model, _regression_model_loaded
        
        if _regression_model_loaded and _regression_model is not None:
            self.model = _regression_model
            return True
        
        # Chemin par défaut du modèle
        model_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "ml",
            "models",
            "regression_model.joblib"
        )
        model_path = os.path.abspath(model_path)
        
        # Créer le répertoire s'il n'existe pas
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        if not os.path.exists(model_path):
            logger.warning(f"Modèle de régression non trouvé: {model_path}")
            logger.info("Utilisation d'une prédiction par défaut basée sur des règles")
            _regression_model_loaded = True
            return False
        
        try:
            _regression_model = joblib.load(model_path)
            self.model = _regression_model
            _regression_model_loaded = True
            logger.info(f"Modèle de régression chargé depuis {model_path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle de régression: {e}")
            _regression_model_loaded = True
            return False
    
    def predict_intensity(
        self,
        hour: int,
        day_of_week: int,
        lux_value: float,
        presence_detected: bool,
        scenario: int
    ) -> Dict[str, any]:
        """
        Prédit l'intensité lumineuse optimale selon le contexte.
        
        Args:
            hour: Heure actuelle (0-23)
            day_of_week: Jour de la semaine (0=Lundi, 6=Dimanche)
            lux_value: Valeur de luminosité ambiante en lux
            presence_detected: Présence détectée
            scenario: Scénario actuel (0-3)
        
        Returns:
            Dict avec:
                - intensity: Intensité prédite (0-100)
                - confidence: Confiance de la prédiction (si disponible)
                - method: "ml" ou "fallback"
        """
        # Si le modèle est disponible, l'utiliser
        if self.model is not None:
            try:
                # Préparer les features
                features = np.array([[
                    hour,
                    day_of_week,
                    lux_value,
                    1 if presence_detected else 0,
                    scenario
                ]])
                
                # Prédiction
                intensity = float(self.model.predict(features)[0])
                
                # Clamp entre 0 et 100
                intensity = max(0, min(100, int(intensity)))
                
                # Pour un Random Forest, on peut estimer la confiance via la variance
                # des prédictions des arbres individuels
                if hasattr(self.model, 'estimators_'):
                    tree_predictions = [tree.predict(features)[0] for tree in self.model.estimators_]
                    std_dev = np.std(tree_predictions)
                    # Confiance inverse de l'écart-type (normalisé)
                    confidence = max(0, min(1, 1 - (std_dev / 50)))  # Normalisation approximative
                else:
                    confidence = 0.8  # Confiance par défaut
                
                logger.debug(
                    f"Prédiction ML: {intensity}% (confiance: {confidence:.2f}) "
                    f"pour hour={hour}, lux={lux_value:.1f}, scenario={scenario}"
                )
                
                return {
                    "intensity": intensity,
                    "confidence": confidence,
                    "method": "ml"
                }
            except Exception as e:
                logger.error(f"Erreur lors de la prédiction ML: {e}")
                # Fallback sur la méthode par défaut
        else:
            logger.debug("Modèle de régression non disponible, utilisation du fallback")
        
        # Méthode fallback basée sur des règles simples
        return self._predict_fallback(hour, lux_value, presence_detected, scenario)
    
    def _predict_fallback(
        self,
        hour: int,
        lux_value: float,
        presence_detected: bool,
        scenario: int
    ) -> Dict[str, any]:
        """
        Prédiction par défaut basée sur des règles simples.
        
        Args:
            hour: Heure actuelle (0-23)
            lux_value: Valeur de luminosité ambiante en lux
            presence_detected: Présence détectée
            scenario: Scénario actuel (0-3)
        
        Returns:
            Dict avec intensity, confidence, method
        """
        # Règles simples selon le scénario
        if scenario == 0:  # Day
            base_intensity = 40
            lux_factor = -0.1
        elif scenario == 1:  # Night
            base_intensity = 25
            lux_factor = -0.15
        elif scenario == 2:  # Away
            intensity = 0
            return {
                "intensity": intensity,
                "confidence": 0.9,
                "method": "fallback"
            }
        else:  # Evening
            base_intensity = 60
            lux_factor = -0.12
        
        # Calculer l'intensité
        intensity = base_intensity + (lux_value * lux_factor)
        
        # Bonus si présence
        if presence_detected:
            intensity += 10 if scenario == 0 else (5 if scenario == 1 else 15)
        
        # Clamp entre 0 et 100
        intensity = max(0, min(100, int(intensity)))
        
        logger.debug(
            f"Prédiction fallback: {intensity}% "
            f"pour hour={hour}, lux={lux_value:.1f}, scenario={scenario}"
        )
        
        return {
            "intensity": intensity,
            "confidence": 0.7,  # Confiance moyenne pour fallback
            "method": "fallback"
        }


# Instance globale du service
_regression_service_instance = None


def get_regression_service() -> RegressionService:
    """
    Obtient l'instance globale du service de régression (singleton).
    
    Returns:
        RegressionService: Instance du service
    """
    global _regression_service_instance
    if _regression_service_instance is None:
        _regression_service_instance = RegressionService()
    return _regression_service_instance
