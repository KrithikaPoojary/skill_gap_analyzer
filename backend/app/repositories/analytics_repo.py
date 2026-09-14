"""Analytical aggregation query caching repository.

Provides in-memory TTL caching for computationally heavy aggregations
across thousands of job postings, with manual invalidation hooks.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable


@dataclass
class CacheEntry:
    """Cached computation entry with expiry timestamp."""

    value: Any
    expires_at: float

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class AnalyticsCacheRepository:
    """In-memory cache for market intelligence queries with TTL expiration."""

    def __init__(self, default_ttl: int = 60) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl

    def get_or_set(
        self,
        cache_key: str,
        compute_fn: Callable[[], Any],
        ttl_seconds: int | None = None,
    ) -> Any:
        """Retrieve value from cache or execute compute_fn and cache result."""
        now = time.time()
        entry = self._cache.get(cache_key)

        if entry and not entry.is_expired():
            return entry.value

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        result = compute_fn()
        self._cache[cache_key] = CacheEntry(value=result, expires_at=now + ttl)
        return result

    def invalidate(self, cache_key: str) -> bool:
        """Evict a specific key from cache."""
        if cache_key in self._cache:
            del self._cache[cache_key]
            return True
        return False

    def invalidate_all(self) -> int:
        """Flush the entire cache."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def size(self) -> int:
        """Number of currently stored entries (active and expired)."""
        return len(self._cache)


analytics_cache_repo = AnalyticsCacheRepository()
