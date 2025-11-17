"""
Cache management utilities.

Provides functions to inspect, clear, and manage the cache.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from .cache import CACHE_DIR


def clear_cache(pattern: Optional[str] = None) -> int:
    """
    Clear cache entries.

    Args:
        pattern: Optional glob pattern to match cache files
                 If None, clears all cache

    Returns:
        Number of cache entries cleared
    """
    if not CACHE_DIR.exists():
        return 0

    if pattern:
        cache_files = list(CACHE_DIR.glob(pattern))
    else:
        cache_files = list(CACHE_DIR.glob("*.json"))

    count = 0
    for cache_file in cache_files:
        try:
            cache_file.unlink()
            count += 1
        except OSError:
            pass

    return count


def cache_stats() -> Dict[str, any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache statistics:
        - total_entries: Total number of cache entries
        - total_size_bytes: Total size of cache in bytes
        - expired_entries: Number of expired entries
    """
    if not CACHE_DIR.exists():
        return {
            "total_entries": 0,
            "total_size_bytes": 0,
            "expired_entries": 0,
        }

    cache_files = list(CACHE_DIR.glob("*.json"))
    total_entries = len(cache_files)
    total_size = sum(f.stat().st_size for f in cache_files)

    # Count expired entries (need to check each file)
    expired_count = 0
    current_time = time.time()

    for cache_file in cache_files:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            # Check if expired (we don't know TTL, so assume any entry older than 24h is expired)
            if current_time - cached_data.get("timestamp", 0) > 86400:
                expired_count += 1
        except (json.JSONDecodeError, KeyError, OSError):
            expired_count += 1

    return {
        "total_entries": total_entries,
        "total_size_bytes": total_size,
        "expired_entries": expired_count,
    }


def cleanup_expired_cache(ttl: int = 86400) -> int:
    """
    Remove expired cache entries.

    Args:
        ttl: Time-to-live in seconds (default: 86400 = 24 hours)
             Entries older than this are considered expired

    Returns:
        Number of expired entries removed
    """
    if not CACHE_DIR.exists():
        return 0

    cache_files = list(CACHE_DIR.glob("*.json"))
    current_time = time.time()
    removed_count = 0

    for cache_file in cache_files:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            # Check if expired
            if current_time - cached_data.get("timestamp", 0) > ttl:
                cache_file.unlink()
                removed_count += 1
        except (json.JSONDecodeError, KeyError, OSError):
            # Corrupted cache - delete it
            try:
                cache_file.unlink()
                removed_count += 1
            except OSError:
                pass

    return removed_count


def list_cache_entries(limit: Optional[int] = None) -> List[Dict[str, any]]:
    """
    List cache entries with metadata.

    Args:
        limit: Optional limit on number of entries to return

    Returns:
        List of dictionaries with cache entry metadata:
        - cache_key: Cache key (filename without .json)
        - timestamp: Cache creation timestamp
        - age_seconds: Age in seconds
        - size_bytes: File size in bytes
    """
    if not CACHE_DIR.exists():
        return []

    cache_files = list(CACHE_DIR.glob("*.json"))
    current_time = time.time()
    entries = []

    for cache_file in cache_files:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            entry = {
                "cache_key": cache_file.stem,
                "timestamp": cached_data.get("timestamp", 0),
                "age_seconds": int(current_time - cached_data.get("timestamp", 0)),
                "size_bytes": cache_file.stat().st_size,
            }
            entries.append(entry)
        except (json.JSONDecodeError, KeyError, OSError):
            # Skip corrupted entries
            pass

    # Sort by age (newest first)
    entries.sort(key=lambda e: e["age_seconds"])

    if limit:
        entries = entries[:limit]

    return entries
