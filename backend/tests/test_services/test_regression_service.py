"""
Tests unitaires pour le service de régression.
"""

import pytest
from app.services.regression_service import RegressionService


class TestRegressionService:
    """Tests pour RegressionService."""
    
    def test_service_initialization(self):
        """Test que le service s'initialise correctement."""
        service = RegressionService()
        assert service is not None
    
    def test_predict_intensity(self):
        """Test la prédiction d'intensité."""
        service = RegressionService()
        result = service.predict_intensity(
            hour=12,
            day_of_week=1,
            lux_value=300.0,
            presence_detected=True,
            scenario=0
        )
        
        assert "intensity" in result
        assert "confidence" in result
        assert "method" in result
        assert 0 <= result["intensity"] <= 100
    
    def test_predict_intensity_fallback(self):
        """Test que le fallback fonctionne si le modèle n'est pas disponible."""
        service = RegressionService()
        # Même si le modèle n'est pas chargé, le fallback doit fonctionner
        result = service.predict_intensity(
            hour=20,
            day_of_week=3,
            lux_value=100.0,
            presence_detected=True,
            scenario=3
        )
        
        assert result["intensity"] >= 0
        assert result["intensity"] <= 100
        assert result["method"] in ["ml", "fallback"]
