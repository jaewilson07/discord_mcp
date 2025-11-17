"""
MCP Cache utilities.

Provides general tool result caching, Notion-specific cache checking,
and cache management utilities.
"""

from mcp_ce.cache.cache import cache_tool
from mcp_ce.cache.notion_cache import (
    check_url_in_notion,
    check_multiple_urls_in_notion,
)
from mcp_ce.cache.cache_manager import (
    clear_cache,
    cache_stats,
    cleanup_expired_cache,
    list_cache_entries,
)

__all__ = [
    # Tool caching
    "cache_tool",
    # Notion cache checking
    "check_url_in_notion",
    "check_multiple_urls_in_notion",
    # Cache management
    "clear_cache",
    "cache_stats",
    "cleanup_expired_cache",
    "list_cache_entries",
]
