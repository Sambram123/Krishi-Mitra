"""
Krishi Mitra — Backend Idempotency Store
Provides idempotency key support for /api/chat and /api/voice-turn endpoints.
Prevents duplicate processing and re-execution during retries or network reconnections.
"""

import time
import threading
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple


class IdempotencyStore(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        """Retrieves cached (status_code, response_data) for the idempotency key, or None."""
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        status_code: int,
        response_data: Dict[str, Any],
        ttl_seconds: int = 300,
    ) -> None:
        """Stores status code and response payload with TTL."""
        pass

    @abstractmethod
    def is_in_flight(self, key: str) -> bool:
        """Returns True if this key is currently being processed by another request."""
        pass

    @abstractmethod
    def start_in_flight(self, key: str, ttl_seconds: int = 60) -> bool:
        """
        Marks key as currently in-flight.
        Returns True if acquired, False if already in-flight or already cached.
        """
        pass

    @abstractmethod
    def finish_in_flight(self, key: str) -> None:
        """Removes in-flight flag after processing finishes."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clears all stored entries (primarily for testing)."""
        pass


class InMemoryIdempotencyStore(IdempotencyStore):
    """
    Thread-safe in-memory idempotency cache with TTL expiration.
    Easily pluggable with Redis for distributed production deployments.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # key -> {"status_code": int, "response_data": dict, "expires_at": float}
        self._cache: Dict[str, Dict[str, Any]] = {}
        # key -> float (expires_at)
        self._in_flight: Dict[str, float] = {}

    def _purge_expired(self, now: float) -> None:
        expired_cache = [k for k, v in self._cache.items() if v["expires_at"] <= now]
        for k in expired_cache:
            del self._cache[k]
        expired_in_flight = [k for k, exp in self._in_flight.items() if exp <= now]
        for k in expired_in_flight:
            del self._in_flight[k]

    def get(self, key: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        if not key:
            return None
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            entry = self._cache.get(key)
            if entry and entry["expires_at"] > now:
                return entry["status_code"], entry["response_data"]
            return None

    def set(
        self,
        key: str,
        status_code: int,
        response_data: Dict[str, Any],
        ttl_seconds: int = 300,
    ) -> None:
        if not key:
            return
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            self._cache[key] = {
                "status_code": status_code,
                "response_data": response_data,
                "expires_at": now + ttl_seconds,
            }
            if key in self._in_flight:
                del self._in_flight[key]

    def is_in_flight(self, key: str) -> bool:
        if not key:
            return False
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            return key in self._in_flight

    def start_in_flight(self, key: str, ttl_seconds: int = 60) -> bool:
        if not key:
            return True
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            if key in self._cache and self._cache[key]["expires_at"] > now:
                return False
            if key in self._in_flight and self._in_flight[key] > now:
                return False
            self._in_flight[key] = now + ttl_seconds
            return True

    def finish_in_flight(self, key: str) -> None:
        if not key:
            return
        with self._lock:
            if key in self._in_flight:
                del self._in_flight[key]

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._in_flight.clear()


_default_store = InMemoryIdempotencyStore()


def get_idempotency_store() -> IdempotencyStore:
    return _default_store
