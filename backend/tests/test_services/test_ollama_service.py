"""
Tests unitaires pour le service Ollama.
"""

import pytest
from app.services.ollama_service import OllamaService


class TestOllamaService:
    """Tests pour OllamaService."""
    
    def test_service_initialization_disabled(self):
        """Test que le service s'initialise correctement quand Ollama n'est pas configuré."""
        service = OllamaService()
        assert service is not None
        # Si OLLAMA_BASE_URL n'est pas défini, le service doit être désactivé
        # mais ne doit pas planter
    
    def test_generate_text_disabled(self):
        """Test que generate_text retourne None si Ollama n'est pas configuré."""
        service = OllamaService()
        if not service.enabled:
            result = service.generate_text("Test prompt")
            assert result is None
    
    def test_generate_scenario_description_fallback(self):
        """Test que generate_scenario_description retourne une description par défaut."""
        service = OllamaService()
        scenario_data = {
            "hour": 12,
            "lux_value": 300.0,
            "presence_detected": True,
            "scenario": 0
        }
        description = service.generate_scenario_description(scenario_data)
        assert description is not None
        assert len(description) > 0
