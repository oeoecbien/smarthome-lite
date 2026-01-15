"""
Module pour la gestion de la queue d'événements.
La queue est gérée par BackendClient, ce module est conservé pour compatibilité.
"""

# La queue d'événements est maintenant gérée directement dans BackendClient
# Ce module est conservé pour référence et éventuelles extensions futures

from services.backend_client import BackendClient

__all__ = ['BackendClient']
