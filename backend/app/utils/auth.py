"""
Utilitaires pour authentification JWT et gestion des mots de passe.

Ce module fournit:
    - Hachage sécurisé des mots de passe avec bcrypt
    - Génération et validation de tokens JWT
    - Extraction des informations utilisateur depuis le token

Sécurité:
    - Algorithme bcrypt avec 12 rounds (compromis sécurité/performance)
    - JWT signé avec HS256 (HMAC-SHA256)
    - Expiration configurable des tokens
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
import secrets

from app.config import settings

# ========== Configuration du hachage de mot de passe ==========
# Facteur de coût pour bcrypt (12 rounds = compromis sécurité/performance)
BCRYPT_ROUNDS = 12


# ========== Fonctions de gestion des mots de passe ==========

def _truncate_password_to_72_bytes(password: str) -> bytes:
    """
    Tronque un mot de passe à 72 bytes maximum (limitation bcrypt).
    
    Cette fonction garantit que le mot de passe tronqué en bytes
    ne dépassera jamais 72 bytes, ce qui est la limite de bcrypt.
    
    Args:
        password (str): Mot de passe à tronquer
        
    Returns:
        bytes: Mot de passe tronqué en bytes (maximum 72 bytes)
    """
    # Encoder le mot de passe en bytes
    password_bytes = password.encode('utf-8')
    
    # Tronquer à exactement 72 bytes si nécessaire
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    return password_bytes


def get_password_hash(password: str) -> str:
    """
    Hache un mot de passe en clair avec bcrypt.
    
    Processus:
        1. Troncature du mot de passe à 72 bytes (limitation bcrypt)
        2. Génération automatique d'un sel aléatoire
        3. Application de l'algorithme bcrypt avec 12 rounds
        4. Retour du hash complet (sel + hash)
    
    Args:
        password (str): Mot de passe en clair
        
    Returns:
        str: Hash bcrypt (60 caractères, format $2b$12$...)
        
    Exemple:
        >>> hash_pwd = get_password_hash("SecurePass123")
        >>> print(hash_pwd)
        $2b$12$vKGZ7J8T9X.../...
    
    Note:
        Le hash généré est différent à chaque appel même pour le même mot de passe
        (grâce au sel aléatoire), ce qui est un comportement souhaité.
        Les mots de passe de plus de 72 bytes sont automatiquement tronqués.
    """
    # Tronquer le mot de passe à 72 bytes (limitation bcrypt)
    password_bytes = _truncate_password_to_72_bytes(password)
    # Générer le sel et hasher le mot de passe
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Retourner le hash en string (bcrypt retourne des bytes)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond au hash stocké.
    
    Processus:
        1. Troncature du mot de passe à 72 bytes (limitation bcrypt)
        2. Extraction du sel depuis le hash stocké
        3. Hachage du mot de passe fourni avec le même sel
        4. Comparaison constante en temps (protection timing attacks)
    
    Args:
        plain_password (str): Mot de passe fourni par l'utilisateur
        hashed_password (str): Hash bcrypt stocké en base de données
        
    Returns:
        bool: True si le mot de passe correspond, False sinon
        
    Exemple:
        >>> stored_hash = "$2b$12$vKGZ7J8T9X..."
        >>> verify_password("SecurePass123", stored_hash)
        True
        >>> verify_password("WrongPassword", stored_hash)
        False
    
    Sécurité:
        La comparaison est effectuée en temps constant pour éviter les
        attaques par analyse temporelle (timing attacks).
        Les mots de passe de plus de 72 bytes sont automatiquement tronqués.
    """
    # Tronquer le mot de passe à 72 bytes (limitation bcrypt)
    password_bytes = _truncate_password_to_72_bytes(plain_password)
    # Convertir le hash en bytes si nécessaire
    hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
    # Vérifier le mot de passe (bcrypt.compare_digest est utilisé en interne)
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ========== Fonctions de gestion des JWT ==========

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT signé avec les données fournies.
    
    Structure du token:
        Header: {"alg": "HS256", "typ": "JWT"}
        Payload: {
            "sub": "username",
            "exp": timestamp_expiration,
            ... autres données
        }
        Signature: HMAC-SHA256(header + payload, SECRET_KEY)
    
    Args:
        data (dict): Données à encoder dans le token (ex: {"sub": "username"})
        expires_delta (timedelta, optional): Durée de validité personnalisée.
            Si None, utilise ACCESS_TOKEN_EXPIRE_MINUTES du config.
            
    Returns:
        str: Token JWT encodé (format xxxxx.yyyyy.zzzzz)
        
    Exemple:
        >>> token = create_access_token({"sub": "john_doe"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huX2RvZSIsImV4cCI6MTY...
        
        >>> # Token avec expiration personnalisée (1 heure)
        >>> short_token = create_access_token(
        ...     {"sub": "admin"},
        ...     expires_delta=timedelta(hours=1)
        ... )
    
    Note:
        Le champ "sub" (subject) est une convention JWT pour identifier l'utilisateur.
        Le champ "exp" (expiration) est automatiquement ajouté.
    """
    # Copie des données pour éviter modification de l'original
    to_encode = data.copy()
    
    # Calcul de la date d'expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    # Ajout du timestamp d'expiration au payload
    to_encode.update({"exp": expire})
    
    # Encodage et signature du token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Décode et valide un token JWT.
    
    Validations effectuées:
        1. Signature valide (vérification avec SECRET_KEY)
        2. Token non expiré (vérification du champ "exp")
        3. Structure valide (header + payload + signature)
    
    Args:
        token (str): Token JWT à décoder
        
    Returns:
        dict | None: Payload du token si valide, None si invalide/expiré
        
    Exemple:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> payload = decode_access_token(token)
        >>> if payload:
        ...     print(f"Utilisateur: {payload['sub']}")
        ... else:
        ...     print("Token invalide")
        Utilisateur: john_doe
    
    Gestion des erreurs:
        - JWTError: Token malformé, signature invalide
        - ExpiredSignatureError: Token expiré
        - Toute autre exception: considéré comme invalide
    
    Sécurité:
        Ne jamais faire confiance au contenu d'un token sans validation.
        Cette fonction DOIT être appelée avant d'utiliser les données du token.
    """
    try:
        # Décodage avec vérification de signature et expiration
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    
    except JWTError as e:
        # Token invalide (signature incorrecte, format invalide, expiré)
        # En production, logger l'erreur pour détecter les tentatives d'attaque
        return None
    
    except Exception as e:
        # Erreur inattendue (ne devrait jamais arriver)
        return None


def generate_api_key() -> str:
    """
    Génère une clé API aléatoire sécurisée pour les Raspberry Pi.
    
    Format:
        64 caractères hexadécimaux (256 bits d'entropie)
        
    Returns:
        str: Clé API unique (en clair, à hasher avant stockage)
        
    Exemple:
        >>> api_key = generate_api_key()
        >>> print(api_key)
        a7f3b9c1e5d8... (64 caractères)
        >>> len(api_key)
        64
    
    Sécurité:
        Utilise secrets.token_hex() qui fait appel au générateur
        cryptographiquement sécurisé du système d'exploitation.
        Ne JAMAIS utiliser random.randint() pour générer des clés.
        IMPORTANT: Hasher cette clé avec hash_api_key() avant stockage.
    """
    return secrets.token_hex(32)  # 32 bytes = 64 caractères hex


def hash_api_key(api_key: str) -> str:
    """
    Hache une clé API avec bcrypt (comme les mots de passe).
    
    Args:
        api_key (str): Clé API en clair
        
    Returns:
        str: Hash bcrypt de la clé API
        
    Sécurité:
        Utilise bcrypt avec 12 rounds pour hasher les API keys.
        Les API keys ne doivent JAMAIS être stockées en clair.
    """
    api_key_bytes = api_key.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(api_key_bytes, salt)
    return hashed.decode('utf-8')


def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """
    Vérifie une clé API en comparant avec le hash stocké.
    
    Args:
        provided_key (str): Clé API fournie dans la requête (en clair)
        stored_hash (str): Hash bcrypt stocké en base de données
        
    Returns:
        bool: True si la clé correspond au hash
        
    Sécurité:
        Utilise bcrypt.checkpw() qui effectue une comparaison constante en temps.
        Ne JAMAIS comparer avec == ou != directement.
    """
    provided_bytes = provided_key.encode('utf-8')
    stored_bytes = stored_hash.encode('utf-8')
    return bcrypt.checkpw(provided_bytes, stored_bytes)


# ========== Fonctions utilitaires pour extraction de données ==========

def get_username_from_token(token: str) -> Optional[str]:
    """
    Extrait le nom d'utilisateur depuis un token JWT.
    
    Args:
        token (str): Token JWT
        
    Returns:
        str | None: Nom d'utilisateur si token valide, None sinon
        
    Exemple:
        >>> token = create_access_token({"sub": "john_doe"})
        >>> username = get_username_from_token(token)
        >>> print(username)
        john_doe
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("sub")
    return None


def is_token_expired(token: str) -> bool:
    """
    Vérifie si un token JWT est expiré sans lever d'exception.
    
    Args:
        token (str): Token JWT
        
    Returns:
        bool: True si expiré ou invalide, False si encore valide
        
    Exemple:
        >>> token = create_access_token({"sub": "test"})
        >>> is_token_expired(token)
        False
        
        >>> # Après expiration
        >>> is_token_expired(old_token)
        True
    """
    payload = decode_access_token(token)
    return payload is None
