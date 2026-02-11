"""
Dépendances FastAPI réutilisables pour l'injection de dépendances.

Ce module centralise toutes les dépendances communes utilisées dans les routes:
    - Gestion de la session base de données
    - Authentification JWT (utilisateur actuel)
    - Vérification des clés API (Raspberry Pi)
    - Extraction de paramètres communs

Architecture:
    Les dépendances FastAPI permettent d'éviter la duplication de code
    et de séparer clairement les préoccupations (authentification, BDD, etc.)
    
Utilisation:
    @app.get("/protected")
    def protected_route(current_user: User = Depends(get_current_user)):
        return {"user": current_user.username}
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.models.raspberry_pi import RaspberryPi
from app.utils.auth import decode_access_token, verify_api_key

# ========== Configuration du schéma de sécurité ==========
# HTTPBearer gère automatiquement l'extraction du token depuis l'en-tête Authorization
security = HTTPBearer()


# ============================================================================
# DÉPENDANCES DE BASE DE DONNÉES
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Fournit une session SQLAlchemy pour interagir avec la base de données.
    
    Cycle de vie:
        1. Création d'une nouvelle session
        2. Injection dans la fonction de route
        3. Fermeture automatique après traitement (même en cas d'erreur)
    
    Yields:
        Session: Session SQLAlchemy active
        
    Utilisation:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    
    Avantages:
        - Gestion automatique du cycle de vie des sessions
        - Pas de fuite de connexions
        - Rollback automatique en cas d'exception
    
    Note:
        Le mot-clé 'yield' permet à FastAPI de reprendre le contrôle
        après l'exécution de la route pour exécuter le code de nettoyage.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Fermeture garantie même en cas d'exception dans la route
        db.close()


# ============================================================================
# DÉPENDANCES D'AUTHENTIFICATION UTILISATEUR (JWT)
# ============================================================================

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extrait l'utilisateur actuel depuis le token JWT (optionnel).
    
    Cette version ne lève pas d'exception si le token est absent/invalide,
    elle retourne simplement None. Utile pour les endpoints publics qui
    peuvent avoir un comportement différent selon l'authentification.
    
    Args:
        credentials: Credentials HTTP Bearer extraits automatiquement
        db: Session de base de données
        
    Returns:
        User | None: Utilisateur authentifié ou None
        
    Utilisation:
        @app.get("/public")
        def public_route(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Bonjour {user.username}"}
            return {"message": "Bonjour visiteur"}
    """
    if not credentials:
        return None
    
    # Décodage du token JWT
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    
    # Extraction du nom d'utilisateur depuis le payload
    username: str = payload.get("sub")
    if not username:
        return None
    
    # Récupération de l'utilisateur depuis la base de données
    user = db.query(User).filter(User.username == username).first()
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extrait l'utilisateur actuel depuis le token JWT (obligatoire).
    
    Cette version lève une exception HTTP 401 si:
        - Le token est absent
        - Le token est invalide/expiré
        - L'utilisateur n'existe plus en base de données
    
    Args:
        credentials: Credentials HTTP Bearer extraits automatiquement
        db: Session de base de données
        
    Returns:
        User: Utilisateur authentifié
        
    Raises:
        HTTPException 401: Si l'authentification échoue
        
    Utilisation:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"username": current_user.username}
    
    Sécurité:
        - Validation stricte du token (signature + expiration)
        - Vérification de l'existence de l'utilisateur
        - Messages d'erreur génériques pour éviter l'énumération d'utilisateurs
    """
    # Décodage du token JWT
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extraction du nom d'utilisateur depuis le payload (champ "sub" = subject)
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide: identifiant utilisateur manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupération de l'utilisateur depuis la base de données
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Vérifie que l'utilisateur actuel est actif (non désactivé).
    
    Cette dépendance peut être utilisée à la place de get_current_user
    si vous implémentez un système de désactivation de comptes.
    
    Args:
        current_user: Utilisateur extrait par get_current_user
        
    Returns:
        User: Utilisateur actif
        
    Raises:
        HTTPException 403: Si le compte est désactivé
        
    Utilisation:
        @app.get("/admin")
        def admin_route(user: User = Depends(get_current_active_user)):
            return {"admin": user.username}
    
    Note:
        Dans la version actuelle, aucun champ "is_active" n'existe dans le modèle User.
        Cette fonction est préparée pour une évolution future.
    """
    # Vérification future: si un champ is_active est ajouté au modèle User
    # if not current_user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Compte utilisateur désactivé"
    #     )
    
    return current_user


# ============================================================================
# DÉPENDANCES D'AUTHENTIFICATION RASPBERRY PI (API KEY)
# ============================================================================

async def verify_raspberry_pi(
    x_api_key: Optional[str] = Header(None, description="Clé API du Raspberry Pi"),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None, description="Token JWT Bearer")
) -> RaspberryPi:
    """
    Vérifie l'authentification d'un Raspberry Pi via sa clé API ou JWT.
    
    Cette dépendance est utilisée pour les endpoints appelés par les Raspberry Pi
    (envoi de mesures de capteurs, heartbeat, etc.)
    
    Processus d'authentification:
        Option 1 (API Key): 
            1. Extraction de la clé API depuis l'en-tête X-API-Key
            2. Recherche du Raspberry Pi correspondant en base de données
            3. Vérification de la clé avec comparaison sécurisée
        Option 2 (JWT):
            1. Extraction du token JWT depuis l'en-tête Authorization
            2. Décodage et validation du token
            3. Utilisation du premier Raspberry Pi disponible (ou création d'un RPi système)
    
    Args:
        x_api_key: Clé API extraite de l'en-tête HTTP X-API-Key (optionnel)
        credentials: Credentials JWT extraits automatiquement (optionnel)
        db: Session de base de données
        
    Returns:
        RaspberryPi: Instance du Raspberry Pi authentifié
        
    Raises:
        HTTPException 401: Si l'authentification échoue
        
    Utilisation:
        @app.post("/api/sensor/light")
        def record_light(
            data: LightReading,
            rpi: RaspberryPi = Depends(verify_raspberry_pi)
        ):
            # Enregistrer la mesure pour ce Raspberry Pi
            return {"status": "ok", "rpi": rpi.name}
    
    Sécurité:
        - Comparaison sécurisée des clés (protection timing attacks)
        - Validation stricte du token JWT
        - Messages d'erreur génériques
    """
    # Option 1: Authentification par API Key
    if x_api_key:
        all_rpis = db.query(RaspberryPi).all()
        rpi = None
        for candidate_rpi in all_rpis:
            if verify_api_key(x_api_key, candidate_rpi.api_key_hash):
                rpi = candidate_rpi
                break
        
        if rpi:
            if not rpi.is_online:
                rpi.is_online = True
                db.commit()
                db.refresh(rpi)
            return rpi
    
    # Option 2: Authentification par JWT
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        payload = decode_access_token(token)
        if payload:
            # Utilisateur authentifié via JWT
            # Utiliser le premier Raspberry Pi disponible ou créer un RPi système
            rpi = db.query(RaspberryPi).first()
            if not rpi:
                # Créer un Raspberry Pi système si aucun n'existe
                rpi = RaspberryPi(
                    name="System",
                    location="System",
                    ip_address="127.0.0.1",
                    is_online=True
                )
                db.add(rpi)
                db.commit()
                db.refresh(rpi)
            
            if not rpi.is_online:
                rpi.is_online = True
                db.commit()
                db.refresh(rpi)
            
            return rpi
    
    # Aucune méthode d'authentification valide
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise (API Key ou JWT)",
        headers={"WWW-Authenticate": "ApiKey, Bearer"},
    )


async def verify_raspberry_pi_online(
    rpi: RaspberryPi = Depends(verify_raspberry_pi)
) -> RaspberryPi:
    """
    Vérifie que le Raspberry Pi est en ligne.
    
    Cette dépendance compose verify_raspberry_pi en ajoutant une vérification
    de l'état de connexion (utile pour certaines opérations critiques).
    
    Args:
        rpi: Raspberry Pi authentifié
        
    Returns:
        RaspberryPi: Instance du Raspberry Pi en ligne
        
    Raises:
        HTTPException 503: Si le Raspberry Pi est hors ligne
        
    Utilisation:
        @app.post("/api/device/control")
        def control_device(
            command: DeviceCommand,
            rpi: RaspberryPi = Depends(verify_raspberry_pi_online)
        ):
            # Exécuter la commande sur le Raspberry Pi en ligne
            return {"status": "command_sent"}
    """
    if not rpi.is_online:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Raspberry Pi '{rpi.name}' est actuellement hors ligne"
        )
    
    return rpi


# ============================================================================
# DÉPENDANCES DE PAGINATION
# ============================================================================

class PaginationParams:
    """
    Classe de dépendance pour gérer la pagination des listes.
    
    Attributs:
        skip (int): Nombre d'éléments à sauter (offset)
        limit (int): Nombre maximum d'éléments à retourner
    
    Utilisation:
        @app.get("/items")
        def get_items(
            pagination: PaginationParams = Depends(),
            db: Session = Depends(get_db)
        ):
            items = db.query(Item).offset(pagination.skip).limit(pagination.limit).all()
            return items
    
    Exemple de requête:
        GET /items?skip=20&limit=10
        # Retourne les éléments 21 à 30
    """
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100
    ):
        """
        Initialise les paramètres de pagination.
        
        Args:
            skip: Nombre d'éléments à sauter (défaut: 0)
            limit: Nombre maximum d'éléments (défaut: 100, max: 1000)
        
        Validation:
            - skip doit être >= 0
            - limit doit être entre 1 et 1000
        """
        # Validation du paramètre skip
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le paramètre 'skip' doit être >= 0"
            )
        
        # Validation du paramètre limit
        if limit < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le paramètre 'limit' doit être >= 1"
            )
        
        if limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le paramètre 'limit' ne peut pas dépasser 1000"
            )
        
        self.skip = skip
        self.limit = limit


# ============================================================================
# DÉPENDANCES DE FILTRAGE
# ============================================================================

class DeviceFilterParams:
    """
    Classe de dépendance pour filtrer les appareils.
    
    Permet de filtrer par:
        - Type d'appareil (light, socket, dimmer)
        - État (ON/OFF)
        - Raspberry Pi
        - Localisation
    
    Utilisation:
        @app.get("/devices")
        def get_devices(
            filters: DeviceFilterParams = Depends(),
            db: Session = Depends(get_db)
        ):
            query = db.query(Device)
            if filters.device_type:
                query = query.filter(Device.type == filters.device_type)
            # ... autres filtres
            return query.all()
    """
    def __init__(
        self,
        device_type: Optional[str] = None,
        state: Optional[bool] = None,
        raspberry_pi_id: Optional[int] = None,
        location: Optional[str] = None
    ):
        """
        Initialise les paramètres de filtrage.
        
        Args:
            device_type: Type d'appareil ('light', 'socket', 'dimmer')
            state: État de l'appareil (True=ON, False=OFF)
            raspberry_pi_id: ID du Raspberry Pi
            location: Localisation (ex: "Salon", "Chambre")
        """
        # Validation du type d'appareil
        if device_type and device_type not in ["light", "socket", "dimmer"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Type d'appareil invalide: {device_type}. Types autorisés: light, socket, dimmer"
            )
        
        self.device_type = device_type
        self.state = state
        self.raspberry_pi_id = raspberry_pi_id
        self.location = location


class EventFilterParams:
    """
    Classe de dépendance pour filtrer les événements.
    
    Permet de filtrer par:
        - Type d'événement (state_changed, brightness_changed, etc.)
        - Source (manual, automatic, ai, smart_dimming)
        - ID d'appareil
        - Plage de dates
    
    Utilisation:
        @app.get("/events")
        def get_events(
            filters: EventFilterParams = Depends(),
            db: Session = Depends(get_db)
        ):
            query = db.query(Event)
            if filters.event_type:
                query = query.filter(Event.event_type == filters.event_type)
            # ... autres filtres
            return query.all()
    """
    def __init__(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        device_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Initialise les paramètres de filtrage des événements.
        
        Args:
            event_type: Type d'événement
            source: Source de l'événement
            device_id: ID de l'appareil concerné
            start_date: Date de début (format ISO 8601)
            end_date: Date de fin (format ISO 8601)
        """
        # Validation des types d'événements (aligné avec le modèle Event et le frontend)
        valid_event_types = [
            "state_changed", "brightness_changed", "presence_detected",
            "rule_triggered", "scenario_changed", "smart_dimming_applied", "system"
        ]
        if event_type and event_type not in valid_event_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Type d'événement invalide. Types autorisés: {', '.join(valid_event_types)}"
            )
        
        # Validation des sources
        valid_sources = ["manual", "automatic", "ai", "smart_dimming", "rule"]
        if source and source not in valid_sources:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Source invalide. Sources autorisées: {', '.join(valid_sources)}"
            )
        
        self.event_type = event_type
        self.source = source
        self.device_id = device_id
        self.start_date = start_date
        self.end_date = end_date


# ============================================================================
# DÉPENDANCES DE VALIDATION PERSONNALISÉES
# ============================================================================

async def validate_device_exists(
    device_id: int,
    db: Session = Depends(get_db)
) -> int:
    """
    Vérifie qu'un appareil existe.
    
    Args:
        device_id: ID de l'appareil
        db: Session de base de données
        
    Returns:
        int: ID de l'appareil validé
        
    Raises:
        HTTPException 404: Si l'appareil n'existe pas
        
    Utilisation:
        @app.get("/devices/{device_id}")
        def get_device(
            device_id: int = Depends(validate_device_exists),
            db: Session = Depends(get_db)
        ):
            device = db.query(Device).get(device_id)
            return device
    """
    from app.models.device import Device
    
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appareil avec ID {device_id} introuvable"
        )
    
    return device_id


async def validate_raspberry_pi_exists(
    raspberry_pi_id: int,
    db: Session = Depends(get_db)
) -> int:
    """
    Vérifie qu'un Raspberry Pi existe.
    
    Args:
        raspberry_pi_id: ID du Raspberry Pi
        db: Session de base de données
        
    Returns:
        int: ID du Raspberry Pi validé
        
    Raises:
        HTTPException 404: Si le Raspberry Pi n'existe pas
    """
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == raspberry_pi_id).first()
    if not rpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raspberry Pi avec ID {raspberry_pi_id} introuvable"
        )
    
    return raspberry_pi_id


# ============================================================================
# DÉPENDANCES DE PERMISSION (FUTURE EXTENSION)
# ============================================================================

async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Vérifie que l'utilisateur actuel a les permissions administrateur.
    
    Cette dépendance vérifie que l'utilisateur authentifié a le rôle "admin".
    Utilisez cette dépendance pour protéger les endpoints réservés aux administrateurs.
    
    Args:
        current_user: Utilisateur authentifié
        
    Returns:
        User: Utilisateur avec permissions admin
        
    Raises:
        HTTPException 403: Si l'utilisateur n'est pas administrateur
        
    Utilisation:
        @app.get("/admin/users")
        def list_users(admin_user: User = Depends(require_admin)):
            # Seuls les administrateurs peuvent accéder à cet endpoint
            return {"users": [...]}
    """
    # Vérifier que l'utilisateur a le rôle admin
    if not hasattr(current_user, 'role') or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions administrateur requises"
        )
    
    return current_user


# ============================================================================
# EXPORT DES DÉPENDANCES PRINCIPALES
# ============================================================================

__all__ = [
    # Base de données
    "get_db",
    
    # Authentification utilisateur
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    
    # Authentification Raspberry Pi
    "verify_raspberry_pi",
    "verify_raspberry_pi_online",
    
    # Pagination et filtrage
    "PaginationParams",
    "DeviceFilterParams",
    "EventFilterParams",
    
    # Validation
    "validate_device_exists",
    "validate_raspberry_pi_exists",
    
    # Permissions (future)
    "require_admin",
]
