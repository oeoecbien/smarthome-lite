"""
Middleware de rate limiting pour protéger les endpoints sensibles.
"""

import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour limiter le nombre de requêtes par IP.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.cleanup_interval = 60  # Nettoyer toutes les 60 secondes
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next):
        # Nettoyer les anciennes entrées périodiquement
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        # Obtenir l'IP du client
        client_ip = request.client.host if request.client else "unknown"
        
        # Vérifier le rate limit
        if not self._check_rate_limit(client_ip, current_time):
            logger.warning(f"Rate limit dépassé pour {client_ip} sur {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Trop de requêtes. Limite: {self.requests_per_minute} requêtes/minute"
            )
        
        # Continuer avec la requête
        response = await call_next(request)
        return response
    
    def _check_rate_limit(self, client_ip: str, current_time: float) -> bool:
        """
        Vérifie si l'IP a dépassé la limite de requêtes.
        
        Returns:
            True si la requête est autorisée, False sinon
        """
        # Nettoyer les requêtes de plus d'une minute
        minute_ago = current_time - 60
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]
        
        # Vérifier la limite
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        # Ajouter la requête actuelle
        self.requests[client_ip].append(current_time)
        return True
    
    def _cleanup_old_entries(self, current_time: float):
        """Nettoie les entrées de plus d'une minute."""
        minute_ago = current_time - 60
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                req_time for req_time in self.requests[ip]
                if req_time > minute_ago
            ]
            # Supprimer les IPs sans requêtes récentes
            if not self.requests[ip]:
                del self.requests[ip]
