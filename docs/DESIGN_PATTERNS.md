# MCP Discord Server - Design Patterns Guide

**Last Updated:** January 2025  
**Status:** Production-Ready Patterns  
**Purpose:** Document reusable design patterns discovered during MCP server development

---

## Table of Contents

1. [Pattern 1: Helper Pattern (Singleton Service Access)](#pattern-1-helper-pattern-singleton-service-access)
2. [Pattern 2: Upsert Pattern (Create or Update)](#pattern-2-upsert-pattern-create-or-update)
3. [Pattern 3: Timestamp Tracking (Test Validation)](#pattern-3-timestamp-tracking-test-validation)
4. [Pattern 4: Cache Decorator Pattern](#pattern-4-cache-decorator-pattern)
5. [Pattern 5: URL Extraction Utility](#pattern-5-url-extraction-utility)
6. [Pattern Selection Guide](#pattern-selection-guide)

---

## Pattern 1: Helper Pattern (Singleton Service Access)

### Problem

Tools need access to external service clients (Discord bot, Notion API, GitHub client) without:
- Creating global state in tool files (makes testing hard)
- Passing client as parameter to every tool (violates MCP tool signature)
- Initializing client multiple times (inefficient, may cause auth issues)

### Solution

Create a helper module (`_bot_helper.py` or `_client_helper.py`) that manages singleton access to the service client.

### Implementation

**File: `src/mcp_ce/tools/discord/_bot_helper.py`**

```python
"""Helper for accessing Discord bot instance."""

from typing import Optional
from discord.ext import commands

_bot_instance: Optional[commands.Bot] = None


def get_bot() -> commands.Bot:
    """
    Get the Discord bot instance.
    
    Returns:
        The Discord bot instance
        
    Raises:
        RuntimeError: If bot not initialized (call set_bot first)
    """
    if _bot_instance is None:
        raise RuntimeError("Discord bot not initialized. Call set_bot() first.")
    return _bot_instance


def set_bot(bot: commands.Bot) -> None:
    """
    Set the Discord bot instance.
    
    Args:
        bot: Discord bot instance to register
    """
    global _bot_instance
    _bot_instance = bot


def is_bot_ready() -> bool:
    """
    Check if bot is initialized and ready.
    
    Returns:
        True if bot is ready, False otherwise
    """
    return _bot_instance is not None and _bot_instance.is_ready()
```

### Usage in Tools

```python
"""Send a message to a Discord channel."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.discord.models import MessageResult
from ._bot_helper import get_bot


@register_command("discord", "send_message")
async def send_message(channel_id: str, content: str) -> ToolResponse:
    """Send a message to a Discord channel."""
    try:
        bot = get_bot()  # ✅ No global state in tool file
        channel = bot.get_channel(int(channel_id))
        
        if not channel:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"Channel {channel_id} not found"
            )
        
        message = await channel.send(content)
        
        result = MessageResult(
            message_id=str(message.id),
            channel_id=str(message.channel.id),
            content=content,
            timestamp=message.created_at.isoformat(),
        )
        
        return ToolResponse(is_success=True, result=result)
    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
```

### When to Use

✅ **Use when:**
- Tools need access to authenticated service clients
- Service initialization is expensive (API connections, auth)
- Multiple tools share the same client
- Testing requires mock clients

❌ **Don't use when:**
- Tool creates its own client (e.g., one-off HTTP request)
- Service doesn't maintain state
- Each tool needs different auth credentials

### Benefits

- ✅ **Testability** - Easy to mock with `set_bot(mock_bot)` in tests
- ✅ **No global state** - Tools remain pure functions
- ✅ **Clear error messages** - RuntimeError explains missing initialization
- ✅ **Single source of truth** - One place to manage client lifecycle
- ✅ **Reusable** - Same pattern works for any service (Discord, Notion, GitHub)

### Applied In

- **Discord:** `_bot_helper.py` (21 tools)
- **Notion:** `_client_helper.py` (6 tools)

### Example: Notion Client Helper

```python
"""Helper for accessing Notion API client."""

import os
from typing import Optional
from notion_client import AsyncClient

_client: Optional[AsyncClient] = None


def get_client() -> AsyncClient:
    """Get Notion API client (singleton)."""
    global _client
    if _client is None:
        token = os.getenv("NOTION_TOKEN")
        if not token:
            raise RuntimeError("NOTION_TOKEN environment variable not set")
        _client = AsyncClient(auth=token)
    return _client
```

---

## Pattern 2: Upsert Pattern (Create or Update)

### Problem

During testing and automation:
- Running tests multiple times creates duplicate resources (events, pages, channels)
- Need to clean up after each test run (complex, error-prone)
- Want permanent test fixtures that persist across runs

### Solution

Implement "upsert" tools that search for existing resources by unique identifier (name, title) and update if found, create if not.

### Implementation

**File: `src/mcp_ce/tools/discord/upsert_scheduled_event.py`**

```python
"""Upsert (create or update) a scheduled event in a Discord server."""

from datetime import datetime, timezone
from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.discord.models import EventResult
from ._bot_helper import get_bot
import discord


@register_command("discord", "upsert_scheduled_event")
async def upsert_scheduled_event(
    server_id: str,
    name: str,
    description: Optional[str] = None,
    start_time: Optional[str] = None,
    location: Optional[str] = None,
) -> ToolResponse:
    """
    Create or update a scheduled event (upsert pattern).
    
    Searches for existing event by name. If found, updates it.
    If not found, creates new event. This prevents duplicate events
    during testing and automation.
    
    Args:
        server_id: Discord server/guild ID
        name: Event name (used as unique identifier for search)
        description: Event description
        start_time: ISO 8601 timestamp (defaults to 1 week from now)
        location: Event location (for external events)
        
    Returns:
        ToolResponse with EventResult containing:
        - operation: "created" or "updated"
        - event_id: Discord event ID
        - event_name: Event name
        - start_time: Event start time
        - url: Event URL
    """
    try:
        bot = get_bot()
        guild = bot.get_guild(int(server_id))
        
        if not guild:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"Server {server_id} not found"
            )
        
        # Step 1: Search for existing event by name
        existing_event = None
        for event in guild.scheduled_events:
            if event.name == name:
                existing_event = event
                break
        
        # Parse start time
        if start_time:
            event_start = datetime.fromisoformat(start_time)
        else:
            event_start = datetime.now(timezone.utc).replace(
                hour=19, minute=0, second=0, microsecond=0
            )
        
        # Step 2: Update or create
        if existing_event:
            # Update existing event
            await existing_event.edit(
                name=name,
                description=description,
                start_time=event_start,
                location=location,
            )
            operation = "updated"
            event = existing_event
        else:
            # Create new event
            event = await guild.create_scheduled_event(
                name=name,
                description=description,
                start_time=event_start,
                location=location,
                entity_type=discord.EntityType.external,
            )
            operation = "created"
        
        result = EventResult(
            operation=operation,  # ✅ Track whether created or updated
            event_id=str(event.id),
            event_name=event.name,
            start_time=event.start_time.isoformat(),
            url=event.url,
        )
        
        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
```

### When to Use

✅ **Use when:**
- Creating test fixtures that should persist across runs
- Automating resource creation (idempotent operations)
- Preventing duplicate resources (events, pages, channels)
- Building CI/CD pipelines (safe to run multiple times)

❌ **Don't use when:**
- Every invocation should create a new resource (messages, logs)
- Resource uniqueness isn't required
- Performance is critical (search adds overhead)

### Benefits

- ✅ **Idempotency** - Safe to run multiple times, same result
- ✅ **No test pollution** - Avoids creating 100s of "Test Event" duplicates
- ✅ **Simplified testing** - No need for complex cleanup logic
- ✅ **Clear semantics** - Returns "created" or "updated" operation
- ✅ **Permanent fixtures** - Test resources persist for debugging

### Applied In

- **Discord:** `upsert_scheduled_event.py` (permanent "Test Event - Discord")

### Usage Example (Testing)

```python
# First run: Creates "Test Event - Discord"
result = await upsert_scheduled_event(
    server_id="123456789",
    name="Test Event - Discord",
    description="Permanent test fixture"
)
assert result.result.operation == "created"

# Second run: Updates existing event (no duplicate)
result = await upsert_scheduled_event(
    server_id="123456789",
    name="Test Event - Discord",  # ✅ Same name
    description="Updated description"
)
assert result.result.operation == "updated"  # ✅ Updated, not created
```

### Extension Ideas

- **Notion:** `upsert_notion_page` - Search by title, update if exists
- **GitHub:** `upsert_github_issue` - Search by title, update if open
- **Slack:** `upsert_slack_channel` - Search by name, use existing if found

---

## Pattern 3: Timestamp Tracking (Test Validation)

### Problem

When running tests repeatedly:
- Hard to verify test actually executed (vs. cached/stale result)
- Difficult to see when fixture was last updated
- No visual confirmation in UI (Discord, Notion, etc.)

### Solution

Append "Last test run: [timestamp]" to resource descriptions. Automatically remove old timestamp and add new one on each run.

### Implementation

```python
"""Update event description with execution timestamp."""

from datetime import datetime, timezone


def add_timestamp_to_description(description: Optional[str]) -> str:
    """
    Add execution timestamp to description.
    
    Removes any existing "Last test run:" line and appends new one.
    
    Args:
        description: Existing description (may contain old timestamp)
        
    Returns:
        Description with current timestamp appended
    """
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    if description:
        # Remove old "Last test run:" line if exists
        lines = description.split("\n")
        lines = [line for line in lines if not line.startswith("Last test run:")]
        base_description = "\n".join(lines).strip()
        
        # Append new timestamp
        return f"{base_description}\n\nLast test run: {current_time}"
    else:
        # No existing description
        return f"Last test run: {current_time}"
```

### Usage in Tools

```python
@register_command("discord", "upsert_scheduled_event")
async def upsert_scheduled_event(
    server_id: str,
    name: str,
    description: Optional[str] = None,
    # ... other params
) -> ToolResponse:
    # Add timestamp to description
    final_description = add_timestamp_to_description(description)
    
    if existing_event:
        await existing_event.edit(
            name=name,
            description=final_description,  # ✅ Always fresh timestamp
            # ... other fields
        )
    else:
        event = await guild.create_scheduled_event(
            name=name,
            description=final_description,  # ✅ Timestamp on creation
            # ... other fields
        )
```

### When to Use

✅ **Use when:**
- Creating permanent test fixtures
- Running integration tests repeatedly
- Need visual confirmation in UI
- Debugging test execution timing

❌ **Don't use when:**
- Production resources (user-facing)
- Timestamp would confuse end users
- Description field is critical data

### Benefits

- ✅ **Visual validation** - See "Last test run: 2025-01-17 14:32:00 UTC" in UI
- ✅ **Test debugging** - Know exactly when fixture was last updated
- ✅ **Automatic cleanup** - Old timestamps removed automatically
- ✅ **Timezone clarity** - Always UTC (no ambiguity)

### Applied In

- **Discord:** `upsert_scheduled_event.py` (adds to event descriptions)

### Example Output

```
Event Description (First Run):
"""
Permanent test fixture for Discord tools validation.

Last test run: 2025-01-17 14:30:15 UTC
"""

Event Description (Second Run, 5 minutes later):
"""
Permanent test fixture for Discord tools validation.

Last test run: 2025-01-17 14:35:22 UTC
"""
```

---

## Pattern 4: Cache Decorator Pattern

### Problem

- External API calls are slow (200-500ms per request)
- APIs have rate limits (YouTube: 10k/day, Notion: 3 req/sec)
- Same data requested repeatedly during development/testing
- Need consistent cache behavior across all tools

### Solution

Decorator pattern for file-based caching with TTL expiration and standardized `override_cache` parameter.

### Implementation

**File: `src/mcp_ce/cache/cache.py`**

```python
"""Cache decorator for expensive tool operations."""

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Optional, Any


CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def cache_tool(ttl: int = 3600, id_param: str = None) -> Callable:
    """
    Cache tool results with TTL expiration.
    
    Args:
        ttl: Time-to-live in seconds (default: 1 hour)
        id_param: Parameter name to use in cache key (default: all params)
        
    Returns:
        Decorator function
        
    Example:
        @cache_tool(ttl=7200, id_param="video_id")
        async def get_transcript(video_id: str, override_cache: bool = False):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract override_cache parameter
            override_cache = kwargs.get("override_cache", False)
            
            # Generate cache key
            if id_param and id_param in kwargs:
                cache_key = f"{func.__name__}_{kwargs[id_param]}"
            else:
                # Use all parameters
                cache_key = f"{func.__name__}_{hashlib.md5(str(kwargs).encode()).hexdigest()}"
            
            cache_file = CACHE_DIR / f"{cache_key}.json"
            
            # Check cache (unless override_cache=True)
            if not override_cache and cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                    
                    # Check TTL
                    cached_time = datetime.fromisoformat(cached_data["timestamp"])
                    age = (datetime.now() - cached_time).total_seconds()
                    
                    if age < ttl:
                        # Cache hit
                        return cached_data["result"]
                except Exception:
                    pass  # Cache read failed, fetch fresh
            
            # Cache miss or override - call function
            result = await func(*args, **kwargs)
            
            # Save to cache
            try:
                cache_data = {
                    "timestamp": datetime.now().isoformat(),
                    "result": result,
                }
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2)
            except Exception:
                pass  # Cache write failed, return result anyway
            
            return result
        
        return wrapper
    return decorator
```

### Usage in Tools

```python
"""Get YouTube video transcript (cached)."""

from typing import Optional, List
from registry import register_command
from mcp_ce.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.youtube.models import Transcript


@register_command("youtube", "get_transcript")
@cache_tool(ttl=7200, id_param="video_id")  # ✅ Cache for 2 hours
async def get_transcript(
    video_id: str,
    languages: Optional[List[str]] = None,
    override_cache: bool = False  # ✅ Standard parameter
) -> ToolResponse:
    """
    Get transcript for a YouTube video.
    
    Args:
        video_id: YouTube video ID or URL
        languages: Preferred languages (default: ["en"])
        override_cache: Bypass cache and fetch fresh (default: False)
        
    Returns:
        ToolResponse with Transcript dataclass
    """
    # Tool implementation (cache decorator handles caching)
    # ...
```

### Cache TTL Guidelines

| Data Type | TTL | Rationale | Examples |
|-----------|-----|-----------|----------|
| **Immutable content** | 7200s (2hr) | Never changes | YouTube transcripts |
| **Slow-changing metadata** | 3600s (1hr) | Changes rarely | YouTube metadata, web content |
| **User profiles** | 1800s (30min) | Changes occasionally | Discord user info |
| **Lists/collections** | 300s (5min) | Changes moderately | Discord channels, Notion search |
| **Search results** | 180s (3min) | Changes frequently | Notion database queries |

### When to Use

✅ **Use when:**
- External API calls with rate limits
- Data changes infrequently (transcripts, metadata)
- Same data requested repeatedly (testing, development)
- Performance improvement needed (200ms → 5ms)

❌ **Don't use when:**
- Data must always be fresh (real-time messages, live data)
- Side effects (send_message, create_page, delete_channel)
- User expects immediate updates

### Benefits

- ✅ **Performance** - 40-100x speedup on cache hits (200ms → 2-5ms)
- ✅ **Rate limit protection** - Avoids hitting API quotas
- ✅ **Consistent behavior** - `override_cache` parameter standardized across tools
- ✅ **Chainable** - Stacks with `@register_command` decorator
- ✅ **Transparent** - Tool code doesn't need cache logic

### Applied In

- **Discord:** 5 tools (get_server_info, get_channels, list_members, get_user_info, read_messages)
- **YouTube:** 3 tools (all tools cached: 300s-7200s TTL)
- **Notion:** 3 tools (search_notion, query_database, get_page: 180s-300s TTL)
- **Crawl4AI:** 2 tools (crawl_website, deep_crawl: 3600s TTL)

### Cache Performance Metrics

From Discord test suite:
```
[2.1] Testing get_server_info (cached)
✅ Cache MISS: 245ms

[2.2] Testing get_server_info (cache hit)
✅ Cache HIT: 3ms (82x faster)

[2.3] Testing get_server_info (override_cache=True)
✅ Cache BYPASSED: 238ms (fresh fetch)
```

---

## Pattern 5: URL Extraction Utility

### Problem

Users provide both IDs and full URLs:
- YouTube: `"dQw4w9WgXcQ"` vs `"https://www.youtube.com/watch?v=dQw4w9WgXcQ"`
- GitHub: `"12345"` vs `"https://github.com/user/repo/issues/12345"`
- Notion: `"abc123"` vs `"https://www.notion.so/Page-Title-abc123"`

Tools should accept both formats without requiring users to manually extract IDs.

### Solution

Create utility functions that extract IDs from both formats (ID strings and full URLs).

### Implementation

**File: `src/mcp_ce/tools/youtube/_utils.py`**

```python
"""Utility functions for YouTube tools."""

from typing import Optional
import re


def extract_video_id(video_id_or_url: str) -> Optional[str]:
    """
    Extract YouTube video ID from either ID string or full URL.
    
    Supports formats:
    - Video ID: "dQw4w9WgXcQ"
    - youtube.com: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    - youtu.be: "https://youtu.be/dQw4w9WgXcQ"
    - Embedded: "https://www.youtube.com/embed/dQw4w9WgXcQ"
    
    Args:
        video_id_or_url: YouTube video ID or URL
        
    Returns:
        Extracted video ID, or None if invalid
    """
    # Already a video ID (11 characters, no special chars)
    if len(video_id_or_url) == 11 and video_id_or_url.isalnum():
        return video_id_or_url
    
    # youtube.com/watch?v=VIDEO_ID
    if "youtube.com/watch" in video_id_or_url:
        match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", video_id_or_url)
        if match:
            return match.group(1)
    
    # youtu.be/VIDEO_ID
    if "youtu.be/" in video_id_or_url:
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", video_id_or_url)
        if match:
            return match.group(1)
    
    # youtube.com/embed/VIDEO_ID
    if "youtube.com/embed/" in video_id_or_url:
        match = re.search(r"embed/([a-zA-Z0-9_-]{11})", video_id_or_url)
        if match:
            return match.group(1)
    
    return None  # Invalid format
```

### Usage in Tools

```python
"""Get YouTube video metadata."""

from registry import register_command
from mcp_ce.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.youtube.models import VideoMetadata
from ._utils import extract_video_id  # ✅ Reusable utility


@register_command("youtube", "get_video_metadata")
@cache_tool(ttl=3600, id_param="video_id")
async def get_video_metadata(
    video_id: str,
    override_cache: bool = False
) -> ToolResponse:
    """
    Get metadata for a YouTube video.
    
    Args:
        video_id: YouTube video ID or full URL
        override_cache: Bypass cache and fetch fresh
        
    Returns:
        ToolResponse with VideoMetadata
    """
    # Extract ID from URL (if provided)
    extracted_id = extract_video_id(video_id)
    
    if not extracted_id:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Could not extract valid video ID from: {video_id}"
        )
    
    # Use extracted ID for API call
    # ...
```

### When to Use

✅ **Use when:**
- Users might provide URLs or IDs
- Multiple URL formats exist (youtube.com, youtu.be, embed)
- Extracting IDs is non-trivial (regex required)
- Multiple tools need same extraction logic

❌ **Don't use when:**
- Only one format accepted (API design decision)
- Extraction is trivial (simple string split)
- Tool-specific format (not reusable)

### Benefits

- ✅ **User-friendly** - Accept both formats (no manual extraction)
- ✅ **Centralized** - One implementation, multiple tools
- ✅ **Reusable** - Same utility works for all YouTube tools
- ✅ **Robust** - Handles edge cases (query params, embedded URLs)
- ✅ **Clear errors** - Returns None for invalid format

### Applied In

- **YouTube:** `_utils.py` (used by all 3 tools)

### Extension Ideas

- **GitHub:** `extract_issue_number(url)` - Parse GitHub issue URLs
- **Notion:** `extract_page_id(url)` - Parse Notion page URLs
- **Slack:** `extract_channel_id(url)` - Parse Slack channel links

### Example Test Cases

```python
# Test URL extraction
assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
assert extract_video_id("invalid") is None
```

---

## Pattern Selection Guide

### Decision Tree: Which Pattern Should I Use?

```
START: Creating a new tool category (GitHub, Slack, etc.)

1. Does tool need authenticated client?
   ├─ YES → Use Helper Pattern (_client_helper.py)
   └─ NO → Skip to step 2

2. Does tool create resources that might duplicate during testing?
   ├─ YES → Implement Upsert Pattern (search + create/update)
   └─ NO → Skip to step 3

3. Are you creating permanent test fixtures?
   ├─ YES → Add Timestamp Tracking (append "Last test run:")
   └─ NO → Skip to step 4

4. Does tool make expensive API calls or have rate limits?
   ├─ YES → Apply Cache Decorator (@cache_tool)
   └─ NO → Skip to step 5

5. Does tool accept both IDs and URLs?
   ├─ YES → Create URL Extraction Utility (_utils.py)
   └─ NO → Done! Tool complete.
```

### Pattern Combinations

Most tools use **multiple patterns** together:

**Example: YouTube `get_transcript` tool**
- ✅ Cache Decorator (expensive API call, 7200s TTL)
- ✅ URL Extraction (accepts both ID and URL)
- ❌ Helper Pattern (not needed - uses youtube-transcript-api directly)
- ❌ Upsert Pattern (read-only operation)
- ❌ Timestamp Tracking (not a test fixture)

**Example: Discord `upsert_scheduled_event` tool**
- ✅ Helper Pattern (requires Discord bot client)
- ✅ Upsert Pattern (prevents duplicate events)
- ✅ Timestamp Tracking (permanent test fixture)
- ❌ Cache Decorator (write operation, shouldn't cache)
- ❌ URL Extraction (not needed)

**Example: Notion `get_page` tool**
- ✅ Helper Pattern (requires Notion API client)
- ✅ Cache Decorator (expensive API call, 300s TTL)
- ❌ Upsert Pattern (read-only operation)
- ❌ Timestamp Tracking (not a test fixture)
- ❌ URL Extraction (could be added if needed)

### Pattern Priority Matrix

| Pattern | Priority | Apply When | Examples |
|---------|----------|------------|----------|
| **Helper** | 🔴 High | Tool category needs auth | Discord (21 tools), Notion (6 tools) |
| **Cache** | 🟡 Medium | Read-only + rate limits | YouTube (3/3), Discord (5/21), Notion (3/6) |
| **Upsert** | 🟢 Low | Testing creates duplicates | Discord events, Notion pages |
| **Timestamp** | 🟢 Low | Permanent test fixtures | Discord events |
| **URL Extract** | 🟢 Low | Multiple URL formats | YouTube (3 tools) |

---

## Best Practices

### 1. Start with Helper Pattern

If your tool category needs authentication, create `_helper.py` first:

```python
# src/mcp_ce/tools/github/_client_helper.py
import os
from github import Github

_client = None

def get_client() -> Github:
    global _client
    if _client is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN not set")
        _client = Github(token)
    return _client
```

### 2. Cache Read-Only Operations

Add `@cache_tool` to any tool that:
- Makes external API calls
- Has rate limits
- Returns data that changes slowly

```python
@register_command("github", "get_issue")
@cache_tool(ttl=300, id_param="issue_number")  # 5 min cache
async def get_issue(issue_number: str, override_cache: bool = False):
    pass
```

### 3. Document TTL Rationale

Add comment explaining cache TTL choice:

```python
@cache_tool(ttl=7200)  # 2hr - transcripts never change
async def get_transcript(...):
    pass

@cache_tool(ttl=300)  # 5min - issues update frequently
async def get_issue(...):
    pass
```

### 4. Test Upsert Behavior

When implementing upsert, test both code paths:

```python
# First call - creates resource
result1 = await upsert_page(title="Test Page")
assert result1.result.operation == "created"

# Second call - updates resource
result2 = await upsert_page(title="Test Page")
assert result2.result.operation == "updated"
assert result2.result.page_id == result1.result.page_id  # Same page
```

### 5. Handle URL Extraction Errors

Always validate extracted IDs:

```python
extracted_id = extract_video_id(video_id)

if not extracted_id:
    return ToolResponse(
        is_success=False,
        result=None,
        error=f"Invalid video ID or URL: {video_id}"
    )
```

---

## Future Patterns to Consider

### Pattern 6: Pagination Helper

**Problem:** Many APIs return paginated results (100 items at a time)

**Solution:**
```python
async def paginate_all(fetch_func, max_pages=10):
    """Fetch all pages of results."""
    results = []
    page = 1
    while page <= max_pages:
        batch = await fetch_func(page=page)
        if not batch:
            break
        results.extend(batch)
        page += 1
    return results
```

### Pattern 7: Retry with Exponential Backoff

**Problem:** APIs occasionally fail with transient errors (network, rate limits)

**Solution:**
```python
async def retry_with_backoff(func, max_attempts=3):
    """Retry function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

### Pattern 8: Batch Operations

**Problem:** Creating 100 resources one-by-one is slow

**Solution:**
```python
@register_command("github", "create_issues_batch")
async def create_issues_batch(issues: List[dict]):
    """Create multiple issues efficiently."""
    tasks = [create_issue(**issue) for issue in issues]
    return await asyncio.gather(*tasks)
```

---

## References

- [CODE_REVIEW_FINDINGS.md](CODE_REVIEW_FINDINGS.md) - Comprehensive code review
- [.github/copilot-instructions.md](../.github/copilot-instructions.md) - Repository patterns
- Discord test suite: `TESTS/mcp_ce/tools/discord/test_discord_tools.py` (495 lines)
- YouTube test suite: `TESTS/mcp_ce/tools/youtube/test_youtube_tools.py` (292 lines)

---

**End of Design Patterns Guide**
