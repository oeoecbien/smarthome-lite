"""
Configuration centralisée de l'application SmartHome Lite.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List
import secrets


class Settings(BaseSettings):
    """Configuration de l'application."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Base de données
    database_url: str = Field(
        default="postgresql://postgres:smarthome2025@10.109.150.75:5432/smarthome"
    )
    database_host: str = Field(default="10.109.150.75")
    database_port: int = Field(default=5432)
    database_name: str = Field(default="smarthome")
    database_user: str = Field(default="postgres")
    database_password: str = Field(default="smarthome2025")
    database_echo: bool = Field(default=False)
    database_pool_size: int = Field(default=10)
    database_max_overflow: int = Field(default=20)
    database_pool_timeout: int = Field(default=30)
    database_pool_recycle: int = Field(default=3600)
    
    # JWT
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440)
    
    # Serveur
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    debug: bool = Field(default=True)
    environment: str = Field(default="development")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://10.109.150.75:3000"]
    )
    cors_allow_credentials: bool = Field(default=True)
    
    # Raspberry Pi
    raspberry_pi_protocol: str = Field(default="http")
    raspberry_pi_port: int = Field(default=5000)
    raspberry_pi_timeout: int = Field(default=5)
    raspberry_pi_heartbeat_interval: int = Field(default=60)
    raspberry_pi_offline_threshold: int = Field(default=180)
    
    # Machine Learning
    ml_model_path: str = Field(default="ml/models/scenario_classifier.pkl")
    ml_retrain_threshold: int = Field(default=100)
    
    # Ollama (IA générative)
    ollama_base_url: Optional[str] = Field(default=None, description="URL du serveur Ollama IUT")
    ollama_model: str = Field(default="llama2", description="Modèle LLM à utiliser")
    ollama_timeout: int = Field(default=30, description="Timeout en secondes pour les requêtes Ollama")
    
    # Smart Dimming
    smart_dimming_enabled: bool = Field(default=True, description="Activer/désactiver le Smart Dimming globalement")
    smart_dimming_threshold: int = Field(default=10, description="Seuil minimum de différence d'intensité pour déclencher un ajustement (%)")
    
    # Logs
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    @property
    def dimming_params(self) -> dict:
        """
        Paramètres de Smart Dimming par scénario.
        Scénarios: 0=Day, 1=Night, 2=Away, 3=Evening
        """
        return {
            0: {  # Day
                "enabled": True,
                "high_lux_threshold": 500,
                "low_lux_threshold": 200,
                "high_brightness": 20,
                "low_brightness": 70,
                "transition": "immediate"
            },
            1: {  # Night
                "enabled": True,
                "high_lux_threshold": 50,
                "low_lux_threshold": 0,
                "high_brightness": 20,
                "low_brightness": 30,
                "transition": "fade"
            },
            2: {  # Away
                "enabled": False,
                "fixed_brightness": 0
            },
            3: {  # Evening
                "enabled": True,
                "high_lux_threshold": 200,
                "low_lux_threshold": 50,
                "high_brightness": 30,
                "low_brightness": 75,
                "transition": "fade"
            }
        }
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @field_validator("database_url", mode="before")
    @classmethod
    def construct_database_url(cls, v, info):
        """Reconstruit l'URL si les composants individuels sont fournis."""
        if v and v != "postgresql://postgres:smarthome2025@10.109.150.75:5432/smarthome":
            return v
        
        data = info.data
        if all(k in data for k in ["database_user", "database_password", "database_host", "database_port", "database_name"]):
            return (
                f"postgresql://{data['database_user']}:{data['database_password']}"
                f"@{data['database_host']}:{data['database_port']}/{data['database_name']}"
            )
        return v


def validate_production_config():
    """Valide la configuration en environnement production."""
    if not settings.is_production:
        return
    
    if len(settings.secret_key) < 32:
        raise RuntimeError("SECRET_KEY doit faire au moins 32 caractères en production")
    
    if settings.debug:
        raise RuntimeError("DEBUG doit être désactivé en production")


settings = Settings()


def display_config():
    """Affiche la configuration (debug uniquement)."""
    print("\n" + "=" * 60)
    print("CONFIGURATION SMARTHOME LITE")
    print("=" * 60)
    print(f"Environnement: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print(f"Base de données: {settings.database_host}:{settings.database_port}/{settings.database_name}")
    print(f"API: {settings.api_host}:{settings.api_port}")
    print("=" * 60 + "\n")
