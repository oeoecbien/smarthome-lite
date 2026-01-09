"""
Tests unitaires pour le service IA (classification).
"""

import pytest
from app.services.ai_service import AIService


class TestAIService:
    """Tests pour AIService."""
    
    def test_service_initialization(self):
        """Test que le service s'initialise correctement."""
        service = AIService()
        assert service is not None
    
    def test_classify_day_scenario(self):
        """Test la classification d'un scénario Day."""
        service = AIService()
        result = service.classify(
            hour=12,
            day_of_week=1,  # Mardi
            presence_detected=True,
            light_on=True
        )
        
        assert "scenario" in result
        assert "scenario_name" in result
        assert "confidence" in result
        assert "method" in result
        assert result["scenario"] in [0, 1, 2, 3]
    
    def test_classify_night_scenario(self):
        """Test la classification d'un scénario Night."""
        service = AIService()
        result = service.classify(
            hour=2,
            day_of_week=1,
            presence_detected=False,
            light_on=False
        )
        
        assert result["scenario"] in [0, 1, 2, 3]
    
    def test_classify_validation(self):
        """Test la validation des paramètres."""
        service = AIService()
        
        # Test avec valeurs limites
        result = service.classify(0, 0, False, False)
        assert result is not None
        
        result = service.classify(23, 6, True, True)
        assert result is not None
