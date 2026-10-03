# backend/app/services/cache.py
"""
Caché en memoria con TTL para optimización de consultas
Fase 5.1.2 - Evitar consultas repetitivas a la BD

Responsable: Ramírez Cruz Nazario
"""

import os
import time
import threading
import logging
from typing import Optional, Any, Dict, Tuple

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Caché thread-safe en memoria con TTL (time-to-live).

    Uso:
        cache = EmbeddingCache(ttl_seconds=60)
        value = cache.get_or_load('clave', lambda: query_db())
        cache.invalidate('clave')
    """

    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché si no ha expirado."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None

            value, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                self._misses += 1
                return None

            self._hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        """Guarda un valor con TTL."""
        with self._lock:
            self._store[key] = (value, time.time() + self.ttl)

    def get_or_load(self, key: str, loader) -> Any:
        """Obtiene del caché o ejecuta el loader si no está."""
        cached = self.get(key)
        if cached is not None:
            logger.debug(f"Cache HIT: {key}")
            return cached

        logger.debug(f"Cache MISS: {key}, ejecutando loader")
        value = loader()
        self.set(key, value)
        return value

    def invalidate(self, key: str = None) -> None:
        """Invalida una clave específica o todo el caché."""
        with self._lock:
            if key is None:
                self._store.clear()
                logger.info("Caché invalidado completo")
            else:
                self._store.pop(key, None)
                logger.info(f"Caché invalidado: {key}")

    def stats(self) -> Dict[str, Any]:
        """Estadísticas del caché."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            return {
                'size': len(self._store),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 4),
                'ttl_seconds': self.ttl,
            }


# ============================================
# Singleton global
# ============================================
_embedding_cache: Optional[EmbeddingCache] = None


def get_embedding_cache() -> EmbeddingCache:
    """Obtiene la instancia singleton del caché."""
    global _embedding_cache
    if _embedding_cache is None:
        ttl = int(os.getenv('EMBEDDING_CACHE_TTL', '60'))
        _embedding_cache = EmbeddingCache(ttl_seconds=ttl)
        logger.info(f"EmbeddingCache inicializado con TTL={ttl}s")
    return _embedding_cache