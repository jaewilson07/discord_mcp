"""
Cache decorator for MCP tools.

Provides file-based caching with TTL expiration for expensive operations.
"""

import asyncio
import functools
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from dataclasses import asdict, is_dataclass


# Cache directory
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)


def cache_tool(
    ttl: int = 3600,
    id_param: Optional[str] = None,
) -> Callable:
    """
    Decorator to cache tool results with TTL expiration using human-readable keys.

    Args:
        ttl: Time-to-live in seconds (default: 3600 = 1 hour)
        id_param: Parameter name to use for cache key (e.g., "video_id", "page_id", "url")
                  If not provided, uses hash of all arguments (not recommended)

    Returns:
        Decorated function with caching behavior

    Example:
        @register_command("youtube", "get_video_metadata")
        @cache_tool(ttl=3600, id_param="video_id")
        async def get_video_metadata(video_id: str) -> Dict[str, Any]:
            # Cache key will be: youtube/get_video_metadata_<video_id>.json
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Dict[str, Any]:
            # Check if cache should be overridden (don't pop, let function receive it too)
            override_cache = kwargs.get("override_cache", False)

            # Generate cache key
            if id_param:
                # Special case: if id_param is "_static", use a fixed key for parameterless functions
                if id_param == "_static":
                    safe_value = "static"
                else:
                    # Human-readable cache key using specified parameter
                    # Get the parameter value from either args or kwargs
                    param_value = None

                    # Try to get from kwargs first
                    if id_param in kwargs:
                        param_value = kwargs[id_param]
                    else:
                        # Try to get from args by parameter position
                        import inspect

                        sig = inspect.signature(func)
                        param_names = list(sig.parameters.keys())
                        if id_param in param_names:
                            param_index = param_names.index(id_param)
                            if param_index < len(args):
                                param_value = args[param_index]

                    if param_value is None:
                        raise ValueError(
                            f"Cache id_param '{id_param}' not found in function arguments"
                        )

                    # Sanitize the parameter value for use in filename
                    safe_value = (
                        str(param_value)
                        .replace("/", "_")
                        .replace("\\", "_")
                        .replace(":", "_")
                    )

                cache_key = f"{func.__name__}_{safe_value}"
            else:
                # Fallback to hash-based key (legacy, not recommended)
                key_data = {
                    "function": func.__name__,
                    "args": args,
                    "kwargs": kwargs,
                }
                key_str = json.dumps(key_data, sort_keys=True, default=str)
                cache_key = hashlib.sha256(key_str.encode()).hexdigest()

            # Organize cache by function name
            func_cache_dir = CACHE_DIR / func.__name__
            func_cache_dir.mkdir(exist_ok=True)

            cache_file = func_cache_dir / f"{cache_key}.json"

            # Check if cache exists and is valid (skip if override_cache=True)
            if not override_cache and cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)

                    # Check if cache is still valid
                    if time.time() - cached_data["timestamp"] < ttl:
                        # Cache hit - reconstruct result in proper format
                        cached_result = cached_data["result"]

                        # If cached result has ToolResponse structure, reconstruct it
                        if (
                            isinstance(cached_result, dict)
                            and "is_success" in cached_result
                        ):
                            from mcp_ce.tools.model import ToolResponse

                            # Reconstruct the nested result object if it was a dataclass
                            result_data = cached_result["result"]
                            result_type = cached_data.get("result_type")

                            if result_type:
                                # Reconstruct dataclass from cached dict
                                if result_type == "CrawlResult":
                                    from mcp_ce.tools.crawl4ai.models import CrawlResult

                                    result_data = CrawlResult(**result_data)
                                elif result_type == "DeepCrawlResult":
                                    from mcp_ce.tools.crawl4ai.models import (
                                        CrawlResult,
                                        DeepCrawlResult,
                                    )

                                    # Reconstruct nested CrawlResult objects in pages list
                                    pages = [
                                        CrawlResult(**page)
                                        for page in result_data.get("pages", [])
                                    ]
                                    result_data = DeepCrawlResult(
                                        seed_url=result_data["seed_url"],
                                        pages_crawled=result_data["pages_crawled"],
                                        pages=pages,
                                        max_depth=result_data["max_depth"],
                                        domain=result_data["domain"],
                                    )
                                elif result_type == "Transcript":
                                    from mcp_ce.tools.youtube.models import Transcript

                                    result_data = Transcript(**result_data)
                                elif result_type == "VideoMetadata":
                                    from mcp_ce.tools.youtube.models import (
                                        VideoMetadata,
                                    )

                                    result_data = VideoMetadata(**result_data)
                                elif result_type == "SearchResults":
                                    from mcp_ce.tools.youtube.models import (
                                        SearchResults,
                                        VideoInfo,
                                    )

                                    # Reconstruct nested VideoInfo objects in videos list
                                    videos = [
                                        VideoInfo(**video)
                                        for video in result_data.get("videos", [])
                                    ]
                                    result_data = SearchResults(
                                        query=result_data["query"],
                                        videos=videos,
                                        count=result_data["count"],
                                        message=result_data.get("message", ""),
                                    )
                                elif result_type == "PingResult":
                                    from mcp_ce.tools.url_ping.models import PingResult

                                    result_data = PingResult(**result_data)
                                elif result_type == "NotionPage":
                                    from mcp_ce.tools.notion.models import NotionPage

                                    result_data = NotionPage(**result_data)
                                elif result_type == "NotionPageContent":
                                    from mcp_ce.tools.notion.models import (
                                        NotionPageContent,
                                    )

                                    result_data = NotionPageContent(**result_data)
                                elif result_type == "NotionPageUpdateResult":
                                    from mcp_ce.tools.notion.models import (
                                        NotionPageUpdateResult,
                                    )

                                    result_data = NotionPageUpdateResult(**result_data)
                                elif result_type == "DatabaseQueryResult":
                                    from mcp_ce.tools.notion.models import (
                                        DatabaseQueryResult,
                                    )

                                    result_data = DatabaseQueryResult(**result_data)
                                elif result_type == "NotionSearchResult":
                                    from mcp_ce.tools.notion.models import (
                                        NotionSearchResult,
                                    )

                                    result_data = NotionSearchResult(**result_data)
                                elif result_type == "NotionCommentResult":
                                    from mcp_ce.tools.notion.models import (
                                        NotionCommentResult,
                                    )

                                    result_data = NotionCommentResult(**result_data)
                                elif result_type == "ServerInfo":
                                    from mcp_ce.tools.discord.models import ServerInfo

                                    result_data = ServerInfo(**result_data)
                                elif result_type == "UserInfo":
                                    from mcp_ce.tools.discord.models import UserInfo

                                    result_data = UserInfo(**result_data)
                                elif result_type == "ChannelListResult":
                                    from mcp_ce.tools.discord.models import (
                                        ChannelListResult,
                                    )

                                    result_data = ChannelListResult(**result_data)
                                elif result_type == "MemberListResult":
                                    from mcp_ce.tools.discord.models import (
                                        MemberListResult,
                                    )

                                    result_data = MemberListResult(**result_data)
                                elif result_type == "ServerListResult":
                                    from mcp_ce.tools.discord.models import (
                                        ServerListResult,
                                    )

                                    result_data = ServerListResult(**result_data)
                                elif result_type == "MessageListResult":
                                    from mcp_ce.tools.discord.models import (
                                        MessageListResult,
                                    )

                                    result_data = MessageListResult(**result_data)
                                elif result_type == "MessageResult":
                                    from mcp_ce.tools.discord.models import (
                                        MessageResult,
                                    )

                                    result_data = MessageResult(**result_data)
                                elif result_type == "ReactionResult":
                                    from mcp_ce.tools.discord.models import (
                                        ReactionResult,
                                    )

                                    result_data = ReactionResult(**result_data)
                                elif result_type == "RoleResult":
                                    from mcp_ce.tools.discord.models import RoleResult

                                    result_data = RoleResult(**result_data)
                                elif result_type == "ChannelResult":
                                    from mcp_ce.tools.discord.models import (
                                        ChannelResult,
                                    )

                                    result_data = ChannelResult(**result_data)
                                elif result_type == "CategoryResult":
                                    from mcp_ce.tools.discord.models import (
                                        CategoryResult,
                                    )

                                    result_data = CategoryResult(**result_data)
                                elif result_type == "ChannelMoveResult":
                                    from mcp_ce.tools.discord.models import (
                                        ChannelMoveResult,
                                    )

                                    result_data = ChannelMoveResult(**result_data)
                                elif result_type == "ModerationResult":
                                    from mcp_ce.tools.discord.models import (
                                        ModerationResult,
                                    )

                                    result_data = ModerationResult(**result_data)
                                elif result_type == "EventResult":
                                    from mcp_ce.tools.discord.models import EventResult

                                    result_data = EventResult(**result_data)

                            return ToolResponse(
                                is_success=cached_result["is_success"],
                                result=result_data,
                                error=cached_result.get("error"),
                            )
                        else:
                            # Legacy dict format
                            return cached_result
                    else:
                        # Cache expired - delete it
                        cache_file.unlink()
                except (json.JSONDecodeError, KeyError, OSError):
                    # Corrupted cache - delete it
                    cache_file.unlink(missing_ok=True)

            # Cache miss - execute function
            result = await func(*args, **kwargs)

            # Only cache successful results
            # Support both dict format (legacy) and ToolResponse format
            is_success = False
            if hasattr(result, "is_success"):
                # ToolResponse format
                is_success = result.is_success
            elif isinstance(result, dict):
                # Legacy dict format
                is_success = result.get("success", False)

            if is_success:
                try:
                    # Convert ToolResponse to dict for caching
                    if hasattr(result, "is_success"):
                        # Serialize dataclass result to dict if needed
                        result_data = result.result
                        result_type = None

                        if is_dataclass(result_data):
                            result_type = type(result_data).__name__
                            # For DeepCrawlResult, also convert nested CrawlResult objects
                            if result_type == "DeepCrawlResult":
                                result_dict = asdict(result_data)
                            else:
                                result_dict = asdict(result_data)
                            result_data = result_dict

                        cache_result = {
                            "is_success": result.is_success,
                            "result": result_data,
                            "error": result.error,
                        }
                    else:
                        cache_result = result
                        result_type = None

                    cache_data = {
                        "timestamp": time.time(),
                        "result": cache_result,
                    }

                    # Store result type for reconstruction
                    if result_type:
                        cache_data["result_type"] = result_type

                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(cache_data, f, indent=2, default=str)
                except (OSError, TypeError) as e:
                    # Failed to write cache - log but don't fail
                    print(f"Warning: Failed to cache result for {func.__name__}: {e}")

            return result

        return wrapper

    return decorator
