"""
Unit tests for cache decorator.
"""

import asyncio
import json
import time
from pathlib import Path

import pytest

from mcp_ce.cache.cache import CACHE_DIR, cache_tool
from mcp_ce.cache.cache_manager import (
    cache_stats,
    cleanup_expired_cache,
    clear_cache,
    list_cache_entries,
)


@pytest.fixture
def clean_cache():
    """Clear cache before and after each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.mark.asyncio
async def test_cache_hit(clean_cache):
    """Test cache hit on second call."""
    call_count = 0

    @cache_tool(ttl=60)
    async def test_func(param: str) -> dict:
        nonlocal call_count
        call_count += 1
        return {"success": True, "data": f"result_{param}", "call_count": call_count}

    # First call - cache miss
    result1 = await test_func("test")
    assert result1["success"] is True
    assert result1["call_count"] == 1

    # Second call - cache hit (should not increment call_count)
    result2 = await test_func("test")
    assert result2["success"] is True
    assert result2["call_count"] == 1  # Same as first call

    # Total function calls should be 1
    assert call_count == 1


@pytest.mark.asyncio
async def test_cache_miss_different_args(clean_cache):
    """Test cache miss with different arguments."""
    call_count = 0

    @cache_tool(ttl=60)
    async def test_func(param: str) -> dict:
        nonlocal call_count
        call_count += 1
        return {"success": True, "data": f"result_{param}"}

    # First call
    result1 = await test_func("test1")
    assert result1["data"] == "result_test1"

    # Second call with different arg - cache miss
    result2 = await test_func("test2")
    assert result2["data"] == "result_test2"

    # Both calls should execute
    assert call_count == 2


@pytest.mark.asyncio
async def test_cache_expiration(clean_cache):
    """Test cache expiration after TTL."""
    call_count = 0

    @cache_tool(ttl=1)  # 1 second TTL
    async def test_func(param: str) -> dict:
        nonlocal call_count
        call_count += 1
        return {"success": True, "data": f"result_{param}"}

    # First call
    result1 = await test_func("test")
    assert call_count == 1

    # Wait for cache to expire
    time.sleep(1.5)

    # Second call - cache expired, should execute again
    result2 = await test_func("test")
    assert call_count == 2


@pytest.mark.asyncio
async def test_cache_only_successful_results(clean_cache):
    """Test that only successful results are cached."""
    call_count = 0

    @cache_tool(ttl=60)
    async def test_func(should_succeed: bool) -> dict:
        nonlocal call_count
        call_count += 1
        if should_succeed:
            return {"success": True, "data": "success"}
        else:
            return {"success": False, "error": "failed"}

    # First call - failure (should not cache)
    result1 = await test_func(False)
    assert result1["success"] is False
    assert call_count == 1

    # Second call - failure (should execute again, not cached)
    result2 = await test_func(False)
    assert result2["success"] is False
    assert call_count == 2

    # Third call - success (should cache)
    result3 = await test_func(True)
    assert result3["success"] is True
    assert call_count == 3

    # Fourth call - success (should use cache)
    result4 = await test_func(True)
    assert result4["success"] is True
    assert call_count == 3  # No new call


@pytest.mark.asyncio
async def test_custom_cache_key(clean_cache):
    """Test custom cache key function."""
    call_count = 0

    def custom_key(user_id: str, include_metadata: bool = False) -> str:
        # Ignore include_metadata in cache key
        return f"user_{user_id}"

    @cache_tool(ttl=60, key_func=custom_key)
    async def test_func(user_id: str, include_metadata: bool = False) -> dict:
        nonlocal call_count
        call_count += 1
        return {
            "success": True,
            "data": f"user_{user_id}",
            "metadata": include_metadata,
        }

    # First call
    result1 = await test_func("123", include_metadata=False)
    assert call_count == 1

    # Second call with different include_metadata (should use cache due to custom key)
    result2 = await test_func("123", include_metadata=True)
    assert call_count == 1  # Cache hit
    assert result2["metadata"] is False  # Cached value


def test_clear_cache(clean_cache):
    """Test cache clearing."""
    # Create some cache files
    (CACHE_DIR / "test1.json").write_text('{"timestamp": 0, "result": {}}')
    (CACHE_DIR / "test2.json").write_text('{"timestamp": 0, "result": {}}')

    # Clear all
    count = clear_cache()
    assert count == 2
    assert len(list(CACHE_DIR.glob("*.json"))) == 0


def test_cache_stats(clean_cache):
    """Test cache statistics."""
    # Empty cache
    stats = cache_stats()
    assert stats["total_entries"] == 0

    # Create cache files
    (CACHE_DIR / "test1.json").write_text('{"timestamp": 0, "result": {}}')
    (CACHE_DIR / "test2.json").write_text('{"timestamp": 0, "result": {}}')

    stats = cache_stats()
    assert stats["total_entries"] == 2
    assert stats["total_size_bytes"] > 0


def test_cleanup_expired_cache(clean_cache):
    """Test expired cache cleanup."""
    current_time = time.time()

    # Create fresh and expired cache entries
    fresh_data = {"timestamp": current_time, "result": {"success": True}}
    expired_data = {"timestamp": current_time - 90000, "result": {"success": True}}

    (CACHE_DIR / "fresh.json").write_text(json.dumps(fresh_data))
    (CACHE_DIR / "expired.json").write_text(json.dumps(expired_data))

    # Cleanup expired (TTL = 1 hour)
    removed = cleanup_expired_cache(ttl=3600)
    assert removed == 1

    # Fresh entry should remain
    assert (CACHE_DIR / "fresh.json").exists()
    assert not (CACHE_DIR / "expired.json").exists()


def test_list_cache_entries(clean_cache):
    """Test listing cache entries."""
    current_time = time.time()

    # Create cache entries
    entry1 = {"timestamp": current_time - 100, "result": {"success": True}}
    entry2 = {"timestamp": current_time - 50, "result": {"success": True}}

    (CACHE_DIR / "entry1.json").write_text(json.dumps(entry1))
    (CACHE_DIR / "entry2.json").write_text(json.dumps(entry2))

    # List all entries
    entries = list_cache_entries()
    assert len(entries) == 2

    # Should be sorted by age (newest first)
    assert entries[0]["age_seconds"] < entries[1]["age_seconds"]

    # Test limit
    entries_limited = list_cache_entries(limit=1)
    assert len(entries_limited) == 1
