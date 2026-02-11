"""
Cache simple avec TTL. Centralise la logique d'expiration pour que le client Z-Wave
ne gère pas les timestamps à la main.
"""

import time
from typing import Dict, Generic, Iterator, Optional, Tuple, TypeVar

K = TypeVar("K")
V = TypeVar("V")

class SimpleCache(Generic[K, V]):
    """Cache clé → valeur avec TTL (time-to-live) en secondes."""

    def __init__(self, ttl_sec: float = 90.0):
        self._ttl_sec = ttl_sec
        self._data: Dict[K, Tuple[V, float]] = {}  # key -> (value, timestamp)

    def get(self, key: K) -> Optional[V]:
        """Retourne la valeur si présente et non expirée, sinon None et supprime l'entrée."""
        entry = self._data.get(key)
        if not entry:
            return None
        value, ts = entry
        if time.monotonic() - ts > self._ttl_sec:
            del self._data[key]
            return None
        return value

    def set(self, key: K, value: V) -> None:
        """Enregistre la valeur avec le timestamp actuel."""
        self._data[key] = (value, time.monotonic())

    def pop(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Retire l'entrée et retourne la valeur (sans vérifier le TTL)."""
        entry = self._data.pop(key, None)
        if entry is None:
            return default
        return entry[0]

    def items(self) -> Iterator[Tuple[K, V]]:
        """Itère sur les entrées non expirées (key, value). Supprime les expirées au passage."""
        now = time.monotonic()
        to_del = []
        for k, (v, ts) in list(self._data.items()):
            if now - ts > self._ttl_sec:
                to_del.append(k)
                continue
            yield k, v
        for k in to_del:
            del self._data[k]
