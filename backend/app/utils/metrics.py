"""
Collecte de métriques de performance pour monitoring.
"""

import time
from typing import Dict, Any
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collecteur de métriques pour monitoring.
    """
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.endpoint_stats = defaultdict(lambda: {"count": 0, "errors": 0, "total_time": 0.0})
        self.max_response_times = 100  # Garder les 100 derniers temps de réponse
    
    def record_request(self, endpoint: str, method: str, status_code: int, process_time: float):
        """
        Enregistre une requête.
        
        Args:
            endpoint: Chemin de l'endpoint
            method: Méthode HTTP
            status_code: Code de statut HTTP
            process_time: Temps de traitement en secondes
        """
        self.request_count += 1
        
        # Enregistrer les erreurs (4xx, 5xx)
        if status_code >= 400:
            self.error_count += 1
        
        # Statistiques par endpoint
        key = f"{method} {endpoint}"
        self.endpoint_stats[key]["count"] += 1
        self.endpoint_stats[key]["total_time"] += process_time
        
        if status_code >= 400:
            self.endpoint_stats[key]["errors"] += 1
        
        # Garder les temps de réponse (limité)
        self.response_times.append(process_time)
        if len(self.response_times) > self.max_response_times:
            self.response_times.pop(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques actuelles.
        
        Returns:
            Dict avec les métriques
        """
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0.0
        )
        
        error_rate = (
            (self.error_count / self.request_count * 100)
            if self.request_count > 0 else 0.0
        )
        
        # Statistiques par endpoint (top 10)
        top_endpoints = sorted(
            self.endpoint_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]
        
        endpoint_stats = {}
        for endpoint, stats in top_endpoints:
            endpoint_stats[endpoint] = {
                "count": stats["count"],
                "errors": stats["errors"],
                "avg_time": stats["total_time"] / stats["count"] if stats["count"] > 0 else 0.0
            }
        
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": round(error_rate, 2),
            "avg_response_time": round(avg_response_time, 3),
            "endpoints": endpoint_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset(self):
        """Réinitialise les métriques."""
        self.request_count = 0
        self.error_count = 0
        self.response_times.clear()
        self.endpoint_stats.clear()


# Instance globale
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Obtient l'instance globale du collecteur de métriques."""
    return _metrics_collector
