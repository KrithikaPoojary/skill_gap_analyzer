"""Unit tests for the AnalyticsCacheRepository."""

import time
import pytest

from app.repositories.analytics_repo import AnalyticsCacheRepository


@pytest.fixture
def cache():
    return AnalyticsCacheRepository(default_ttl=1)


class TestAnalyticsCacheRepo:
    """Test suite for analytical query caching, expiration, and invalidation."""

    def test_get_or_set_caches_computation(self, cache) -> None:
        call_count = 0

        def expensive_computation():
            nonlocal call_count
            call_count += 1
            return {"metric": 42}

        # First call executes function
        res1 = cache.get_or_set("test_key", expensive_computation, ttl_seconds=5)
        assert res1 == {"metric": 42}
        assert call_count == 1

        # Second call returns cached value without executing function
        res2 = cache.get_or_set("test_key", expensive_computation, ttl_seconds=5)
        assert res2 == {"metric": 42}
        assert call_count == 1

    def test_ttl_expiration(self, cache) -> None:
        call_count = 0

        def compute():
            nonlocal call_count
            call_count += 1
            return call_count

        res1 = cache.get_or_set("exp_key", compute, ttl_seconds=0.01)
        assert res1 == 1

        time.sleep(0.02)

        # After expiry, function is re-executed
        res2 = cache.get_or_set("exp_key", compute, ttl_seconds=0.01)
        assert res2 == 2

    def test_invalidate_and_invalidate_all(self, cache) -> None:
        cache.get_or_set("k1", lambda: 1)
        cache.get_or_set("k2", lambda: 2)
        assert cache.size() == 2

        assert cache.invalidate("k1") is True
        assert cache.size() == 1

        count = cache.invalidate_all()
        assert count == 1
        assert cache.size() == 0
