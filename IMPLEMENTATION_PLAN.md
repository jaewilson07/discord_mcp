# MCP Discord Server - Implementation Plan

**Version:** 1.0  
**Date:** November 16, 2025  
**Status:** Ready for Implementation

## Overview

This plan outlines the implementation of the updated MCP CE architecture based on:
1. **Atomic tool design** - Tools as single-purpose, standalone functions
2. **Decorator-based registration** - Using `@register_command` pattern
3. **Cache wrapper** - Optional `@cache_tool` decorator for performance
4. **Agent composition** - Agents orchestrate atomic tools for complex workflows

**Key Principle:** We are NOT concerned with backward compatibility. This is a clean break to achieve optimal architecture.

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

**Goal:** Implement decorator pattern and cache wrapper without breaking existing functionality.

#### 1.1 Implement Cache Decorator

**Files to Create:**
- `src/mcp_ce/cache.py` - Cache decorator implementation
- `src/mcp_ce/cache_manager.py` - Cache management utilities
- `tests/test_cache.py` - Cache tests

**Tasks:**
1. ✅ Copy implementation from `CACHE_WRAPPER_DESIGN.md`
2. ✅ Add `.cache/` to `.gitignore`
3. ✅ Write unit tests for:
   - Cache hit/miss
   - TTL expiration
   - Custom cache keys
   - Failure non-caching
4. ✅ Validate all tests pass

**Validation:**
```bash
# Run cache tests
pytest tests/test_cache.py -v

# Verify .gitignore updated
git check-ignore .cache/
```

**Success Criteria:**
- ✅ All cache tests pass
- ✅ Cache decorator creates files in `.cache/` directory
- ✅ TTL expiration works correctly
- ✅ `.cache/` is gitignored

#### 1.2 Update Registry Pattern

**Files to Modify:**
- `src/registry.py` - Ensure decorator works with async functions

**Tasks:**
1. ✅ Review current `registry.py` implementation
2. ✅ Test with async functions
3. ✅ Add registry tests

**Current Registry Code:**
```python
# src/registry.py
from typing import Callable

_registry: list[tuple[str, str, Callable]] = []

def register_command(group: str, name: str):
    """Register a command."""
    def decorator(func: Callable) -> Callable:
        _registry.append((group, name, func))
        return func
    return decorator

def get_registry() -> list[tuple[str, str, Callable]]:
    """Get all registered commands."""
    return _registry.copy()
```

**Validation:**
```python
# Test registry with async function
from registry import register_command, get_registry

@register_command("test", "test_tool")
async def test_tool(param: str) -> dict:
    return {"success": True, "data": param}

# Verify registration
registry = get_registry()
assert len(registry) == 1
assert registry[0] == ("test", "test_tool", test_tool)

# Verify function still works
import asyncio
result = asyncio.run(test_tool("hello"))
assert result["success"]
```

**Success Criteria:**
- ✅ Registry works with async functions
- ✅ Decorator doesn't break function execution
- ✅ `get_registry()` returns correct tuples

#### 1.3 Update Runtime to Use Registry

**Files to Modify:**
- `src/mcp_ce/runtime.py` - Modify to read from registry

**Current Approach:**
```python
# Hardcoded registry
_SERVERS_REGISTRY = {
    "url_ping": {
        "name": "url_ping",
        "description": "...",
        "tools": ["ping_url"],
    },
}
```

**Target Approach:**
```python
# Dynamic registry from decorators
from registry import get_registry

def _build_servers_registry() -> Dict[str, Dict[str, Any]]:
    """Build servers registry from decorated functions."""
    registry = get_registry()
    servers = {}
    
    for server, tool, func in registry:
        if server not in servers:
            servers[server] = {
                "name": server,
                "description": f"{server.title()} server",  # Can be enhanced
                "tools": []
            }
        servers[server]["tools"].append(tool)
    
    return servers

# Build once at module load
_SERVERS_REGISTRY = _build_servers_registry()
```

**Tasks:**
1. ✅ Add `_build_servers_registry()` function
2. ✅ Keep `_SERVERS_REGISTRY` variable for compatibility
3. ✅ Test discovery functions still work
4. ✅ Ensure empty registry doesn't break server

**Validation:**
```python
# After adding decorators to tools
from src.mcp_ce.runtime import discovered_servers

servers = discovered_servers()
print(f"Discovered {len(servers)} servers")
for server in servers:
    print(f"- {server['name']}: {len(server.get('tools', []))} tools")
```

**Success Criteria:**
- ✅ `discovered_servers()` returns servers from registry
- ✅ Empty registry returns empty list (doesn't crash)
- ✅ Existing hardcoded registry still works during transition

---

### Phase 2: Tool Migration (Week 2-3)

**Goal:** Add decorators to all existing tools and migrate execution logic.

#### 2.1 Add Decorators to URL Ping Tools

**Files to Modify:**
- `src/mcp_ce/tools/url_ping/ping_url.py`

**Before:**
```python
async def ping_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Ping a URL..."""
    pass
```

**After:**
```python
from registry import register_command
from mcp_ce.cache import cache_tool

@register_command("url_ping", "ping_url")
@cache_tool(ttl=60)  # Cache for 1 minute
async def ping_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Ping a URL..."""
    pass
```

**Validation:**
```python
# Test registration
from registry import get_registry
registry = get_registry()
assert ("url_ping", "ping_url") in [(s, t) for s, t, f in registry]

# Test caching
from src.mcp_ce.tools.url_ping.ping_url import ping_url
import asyncio

result1 = asyncio.run(ping_url("https://example.com"))
result2 = asyncio.run(ping_url("https://example.com"))
# Second call should hit cache (verify via .cache/ directory)
```

**Success Criteria:**
- ✅ Tool registered in registry
- ✅ Tool execution still works
- ✅ Cache files created in `.cache/url_ping/ping_url/`

#### 2.2 Add Decorators to Discord Tools (21 tools)

**Files to Modify:**
- `src/mcp_ce/tools/discord/send_message.py`
- `src/mcp_ce/tools/discord/read_messages.py`
- `src/mcp_ce/tools/discord/get_channel.py`
- ... (all 21 Discord tools)

**Pattern:**
```python
from registry import register_command
from mcp_ce.cache import cache_tool
from ._bot_helper import get_bot

@register_command("discord", "send_message")
async def send_message(channel_id: str, content: str) -> Dict[str, Any]:
    """Send a message to a Discord channel."""
    try:
        bot = get_bot()
        # ... implementation
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Caching Guidelines:**

| Tool | Cache? | TTL | Reason |
|------|--------|-----|--------|
| `send_message` | ❌ No | N/A | Side effect (sends message) |
| `read_messages` | ❌ No | N/A | Real-time data |
| `get_channel` | ✅ Yes | 300s | Channel info rarely changes |
| `get_server_info` | ✅ Yes | 600s | Server info rarely changes |
| `get_user_info` | ✅ Yes | 1800s | User profiles relatively stable |
| `list_servers` | ✅ Yes | 300s | Server list doesn't change often |
| `list_members` | ✅ Yes | 600s | Member list somewhat stable |
| `get_channels` | ✅ Yes | 300s | Channel list relatively stable |
| `add_reaction` | ❌ No | N/A | Side effect |
| `remove_reaction` | ❌ No | N/A | Side effect |
| `create_*` | ❌ No | N/A | Side effects (create channel, etc.) |
| `delete_*` | ❌ No | N/A | Side effects |
| `add_role` | ❌ No | N/A | Side effect |
| `remove_role` | ❌ No | N/A | Side effect |

**Validation:**
```bash
# Test all Discord tools registered
python -c "
from registry import get_registry
discord_tools = [tool for server, tool, func in get_registry() if server == 'discord']
print(f'Discord tools: {len(discord_tools)}')
assert len(discord_tools) == 21, f'Expected 21, got {len(discord_tools)}'
"
```

**Success Criteria:**
- ✅ All 21 Discord tools registered
- ✅ Read-only tools have appropriate cache TTLs
- ✅ Side-effect tools NOT cached
- ✅ All tools still work via MCP and Python

#### 2.3 Add Decorators to YouTube Tools

**Files to Modify:**
- `src/mcp_ce/tools/youtube/get_video_metadata.py`
- `src/mcp_ce/tools/youtube/get_transcript.py`
- `src/mcp_ce/tools/youtube/search_videos.py`

**Pattern:**
```python
from registry import register_command
from mcp_ce.cache import cache_tool
from ._client_helper import get_client

@register_command("youtube", "get_video_metadata")
@cache_tool(ttl=3600)  # Cache for 1 hour
async def get_video_metadata(video_id: str) -> Dict[str, Any]:
    """Get video metadata (cached)."""
    try:
        client = get_client()
        # ... implementation
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Caching Guidelines:**

| Tool | TTL | Reason |
|------|-----|--------|
| `get_video_metadata` | 3600s (1 hour) | Metadata rarely changes |
| `get_transcript` | 7200s (2 hours) | Transcripts don't change |
| `search_videos` | 300s (5 minutes) | Search results change frequently |

**Success Criteria:**
- ✅ All YouTube tools registered and cached
- ✅ Cache files created in `.cache/youtube/`
- ✅ Tools work standalone and via MCP

#### 2.4 Add Decorators to Notion Tools

**Files to Modify:**
- `src/mcp_ce/tools/notion/get_notion_page.py`
- `src/mcp_ce/tools/notion/create_notion_page.py`
- `src/mcp_ce/tools/notion/update_notion_page.py`
- `src/mcp_ce/tools/notion/query_notion_database.py`
- `src/mcp_ce/tools/notion/search_notion.py`

**Caching Guidelines:**

| Tool | Cache? | TTL | Reason |
|------|--------|-----|--------|
| `get_notion_page` | ✅ Yes | 300s | Page content somewhat stable |
| `create_notion_page` | ❌ No | N/A | Side effect |
| `update_notion_page` | ❌ No | N/A | Side effect |
| `query_notion_database` | ✅ Yes | 180s | Database queries cacheable |
| `search_notion` | ✅ Yes | 180s | Search results cacheable |

**Success Criteria:**
- ✅ All Notion tools registered
- ✅ Read-only tools cached appropriately
- ✅ Side-effect tools NOT cached

#### 2.5 Add Decorators to Remaining Tools

**Files to Modify:**
- `src/mcp_ce/tools/crawl4ai/*` - Web scraping tools
- `src/mcp_ce/tools/summarizer/*` - Summarization tools
- `src/mcp_ce/tools/research/*` - Research tools

**Pattern for Each Server:**
1. Add `@register_command(server, tool)` to each tool
2. Add `@cache_tool(ttl=X)` if appropriate (read-only, expensive)
3. Test registration and caching

**Success Criteria:**
- ✅ All tools in all servers registered
- ✅ Appropriate caching added
- ✅ Registry complete

---

### Phase 3: Runtime Refactoring (Week 3)

**Goal:** Simplify `_execute_tool()` to use registry lookup instead of if/elif chains.

#### 3.1 Refactor _execute_tool()

**Current Implementation (~200 lines):**
```python
async def _execute_tool(server: str, tool: str, **kwargs) -> Dict[str, Any]:
    if server == "url_ping" and tool == "ping_url":
        from mcp_ce.tools.url_ping.ping_url import ping_url
        return await ping_url(**kwargs)
    elif server == "discord" and tool == "send_message":
        from mcp_ce.tools.discord.send_message import send_message
        return await send_message(**kwargs)
    # ... 50+ more elif blocks
    else:
        return {"success": False, "error": f"Tool {server}.{tool} not found"}
```

**Target Implementation (~10 lines):**
```python
from registry import get_registry

async def _execute_tool(server: str, tool: str, **kwargs) -> Dict[str, Any]:
    """
    Execute tool by looking up function from registry.
    
    Args:
        server: Server name
        tool: Tool name
        **kwargs: Tool parameters
        
    Returns:
        Tool execution result
    """
    # Look up function in registry
    registry = get_registry()
    func = next(
        (f for s, t, f in registry if s == server and t == tool),
        None
    )
    
    if func is None:
        return {
            "success": False,
            "error": f"Tool '{tool}' not found in server '{server}'"
        }
    
    # Execute function
    try:
        return await func(**kwargs)
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }
```

**Tasks:**
1. ✅ Replace entire `_execute_tool()` implementation
2. ✅ Remove all if/elif blocks
3. ✅ Test all tools still work

**Validation:**
```python
# Test execution via runtime
from src.mcp_ce.runtime import _execute_tool
import asyncio

# Test URL ping
result = asyncio.run(_execute_tool("url_ping", "ping_url", url="https://example.com"))
assert result["success"]

# Test Discord (if bot available)
result = asyncio.run(_execute_tool("discord", "get_server_info", server_id="123"))
# Should work if bot is connected

# Test non-existent tool
result = asyncio.run(_execute_tool("fake", "fake_tool"))
assert not result["success"]
assert "not found" in result["error"]
```

**Success Criteria:**
- ✅ All tools executable via `_execute_tool()`
- ✅ ~200 lines of if/elif code removed
- ✅ Error handling for missing tools
- ✅ No regression in functionality

#### 3.2 Update query_tool_docs()

**Goal:** Generate tool schemas from function docstrings instead of hardcoded dicts.

**Current Approach:**
```python
def query_tool_docs(server: str, tool: Optional[str] = None, detail: str = "summary") -> str:
    if server == "url_ping":
        schemas = {
            "ping_url": {
                "name": "ping_url",
                "description": "...",
                "parameters": {...}
            }
        }
    # ... more hardcoded schemas
```

**Target Approach:**
```python
from registry import get_registry
import inspect
from typing import get_type_hints

def query_tool_docs(server: str, tool: Optional[str] = None, detail: str = "summary") -> str:
    """
    Generate tool documentation from function introspection.
    
    Uses:
    - Function docstring for description
    - Type hints for parameter types
    - Default values for optional parameters
    """
    registry = get_registry()
    server_tools = [(t, f) for s, t, f in registry if s == server]
    
    if not server_tools:
        return f"Server '{server}' not found"
    
    if tool:
        # Get specific tool
        func = next((f for t, f in server_tools if t == tool), None)
        if not func:
            return f"Tool '{tool}' not found in server '{server}'"
        
        return _generate_tool_schema(tool, func, detail)
    else:
        # Get all tools in server
        schemas = []
        for tool_name, func in server_tools:
            schemas.append(_generate_tool_schema(tool_name, func, detail))
        return "\n\n".join(schemas)


def _generate_tool_schema(tool_name: str, func: Callable, detail: str) -> str:
    """Generate JSON schema from function signature."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    schema = {
        "name": tool_name,
        "description": func.__doc__ or "No description available",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
    
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        
        param_type = type_hints.get(param_name, "any")
        param_schema = _type_to_json_schema(param_type)
        
        schema["parameters"]["properties"][param_name] = param_schema
        
        if param.default == inspect.Parameter.empty:
            schema["parameters"]["required"].append(param_name)
    
    if detail == "summary":
        # Return just name and description
        return f"{tool_name}: {schema['description']}"
    else:
        # Return full schema
        import json
        return json.dumps(schema, indent=2)


def _type_to_json_schema(py_type) -> dict:
    """Convert Python type hint to JSON schema type."""
    type_map = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }
    
    # Handle Optional types
    if hasattr(py_type, "__origin__"):
        if py_type.__origin__ is Union:
            # Optional[X] is Union[X, None]
            non_none_types = [t for t in py_type.__args__ if t != type(None)]
            if non_none_types:
                return _type_to_json_schema(non_none_types[0])
    
    return type_map.get(py_type, {"type": "string"})
```

**Tasks:**
1. ✅ Implement `_generate_tool_schema()`
2. ✅ Implement `_type_to_json_schema()`
3. ✅ Update `query_tool_docs()` to use introspection
4. ✅ Test schema generation for all tools

**Validation:**
```python
# Test schema generation
from src.mcp_ce.runtime import query_tool_docs

# Get summary
summary = query_tool_docs("url_ping", detail="summary")
print(summary)

# Get full schema
schema = query_tool_docs("url_ping", tool="ping_url", detail="full")
print(schema)
```

**Success Criteria:**
- ✅ Schemas generated from docstrings
- ✅ Type hints converted to JSON schema types
- ✅ Required vs optional parameters detected
- ✅ No hardcoded schemas remain

#### 3.3 Remove Hardcoded Registry

**Files to Modify:**
- `src/mcp_ce/runtime.py` - Remove `_SERVERS_REGISTRY` dict

**Tasks:**
1. ✅ Delete hardcoded `_SERVERS_REGISTRY` dict
2. ✅ Ensure `_build_servers_registry()` is only source
3. ✅ Test discovery still works

**Before:**
```python
# Hardcoded
_SERVERS_REGISTRY = {
    "url_ping": {...},
    "discord": {...},
    # ...
}
```

**After:**
```python
# Dynamic from registry
from registry import get_registry

_SERVERS_REGISTRY = _build_servers_registry()
```

**Success Criteria:**
- ✅ No hardcoded server/tool lists
- ✅ All servers discovered from decorators
- ✅ Discovery functions work correctly

---

### Phase 4: Agent Implementation (Week 4)

**Goal:** Create example agents that compose atomic tools.

#### 4.1 Create Video Research Agent

**File to Create:**
- `src/mcp_ce/tools/research/video_research_agent.py`

**Implementation:**
```python
"""Video research agent that composes multiple atomic tools."""

from typing import Dict, Any
from registry import register_command
import os


@register_command("research", "video_research_agent")
async def video_research_agent(
    video_url: str,
    notion_database_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Orchestrate video analysis and topic research.
    
    Workflow:
    1. Get video metadata (title, description, published date)
    2. Get transcript
    3. Summarize transcript
    4. Create research plan from summary
    5. Search web for topics
    6. Crawl URLs from video description
    7. Compile research document
    8. Save to Notion
    
    Args:
        video_url: YouTube video URL
        notion_database_id: Notion database ID (optional, uses env var if not provided)
        
    Returns:
        Dictionary with:
        - success: Whether workflow completed
        - data: Results including summary, research topics, Notion page ID
        - error: Error message if failed
    """
    try:
        # Extract video ID
        video_id = _extract_video_id(video_url)
        
        # Step 1: Get video metadata
        from mcp_ce.tools.youtube.get_video_metadata import get_video_metadata
        metadata_result = await get_video_metadata(video_id=video_id)
        if not metadata_result["success"]:
            return metadata_result
        metadata = metadata_result["data"]
        
        # Step 2: Get transcript
        from mcp_ce.tools.youtube.get_transcript import get_transcript
        transcript_result = await get_transcript(video_id=video_id)
        if not transcript_result["success"]:
            return transcript_result
        transcript = transcript_result["data"]["text"]
        
        # Step 3: Summarize transcript
        from mcp_ce.tools.summarizer.summarize_transcript import summarize_transcript
        summary_result = await summarize_transcript(transcript=transcript)
        if not summary_result["success"]:
            return summary_result
        summary = summary_result["data"]["summary"]
        
        # Step 4: Create research plan
        from mcp_ce.tools.research.create_research_plan import create_research_plan
        plan_result = await create_research_plan(context=summary)
        if not plan_result["success"]:
            return plan_result
        topics = plan_result["data"]["topics"]
        
        # Step 5: Search web for topics
        from mcp_ce.tools.research.search_web import search_web
        search_results = []
        for topic in topics[:5]:  # Limit to top 5 topics
            result = await search_web(query=topic)
            if result["success"]:
                search_results.append({
                    "topic": topic,
                    "results": result["data"]
                })
        
        # Step 6: Crawl URLs from description
        from mcp_ce.tools.crawl4ai.crawl_url import crawl_url
        description_urls = _extract_urls_from_description(metadata.get("description", ""))
        url_content = []
        for url in description_urls[:3]:  # Limit to first 3 URLs
            result = await crawl_url(url=url)
            if result["success"]:
                url_content.append({
                    "url": url,
                    "content": result["data"]
                })
        
        # Step 7: Compile research document
        research_doc = _compile_research_document(
            metadata=metadata,
            summary=summary,
            topics=topics,
            search_results=search_results,
            url_content=url_content
        )
        
        # Step 8: Save to Notion (if database_id provided)
        notion_page_id = None
        if notion_database_id or os.getenv("NOTION_RESEARCH_DB"):
            from mcp_ce.tools.notion.create_notion_page import create_notion_page
            db_id = notion_database_id or os.getenv("NOTION_RESEARCH_DB")
            notion_result = await create_notion_page(
                database_id=db_id,
                title=f"Research: {metadata['title']}",
                content=research_doc
            )
            if notion_result["success"]:
                notion_page_id = notion_result["data"]["page_id"]
        
        return {
            "success": True,
            "data": {
                "video_id": video_id,
                "video_title": metadata["title"],
                "summary": summary,
                "research_topics": topics,
                "search_results_count": len(search_results),
                "urls_crawled": len(url_content),
                "notion_page_id": notion_page_id,
                "research_document": research_doc
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Video research agent failed: {str(e)}"
        }


def _extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    import re
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def _extract_urls_from_description(description: str) -> list[str]:
    """Extract URLs from video description."""
    import re
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, description)
    return urls


def _compile_research_document(
    metadata: dict,
    summary: str,
    topics: list[str],
    search_results: list[dict],
    url_content: list[dict]
) -> str:
    """Compile research findings into formatted document."""
    doc = f"""# Video Research: {metadata['title']}

## Video Information
- **Published:** {metadata.get('published_at', 'Unknown')}
- **Duration:** {metadata.get('duration', 'Unknown')}
- **Views:** {metadata.get('view_count', 'Unknown')}

## Summary
{summary}

## Research Topics
{chr(10).join(f'- {topic}' for topic in topics)}

## Web Search Results
"""
    
    for result in search_results:
        doc += f"\n### {result['topic']}\n"
        for item in result['results'][:3]:  # Top 3 results per topic
            doc += f"- [{item.get('title', 'Untitled')}]({item.get('url', '#')})\n"
    
    if url_content:
        doc += "\n## Links from Video Description\n"
        for item in url_content:
            doc += f"\n### {item['url']}\n"
            doc += f"{item['content'][:500]}...\n"  # First 500 chars
    
    return doc
```

**Tasks:**
1. ✅ Implement video research agent
2. ✅ Add all helper functions
3. ✅ Test full workflow with real video
4. ✅ Validate Notion integration

**Validation:**
```python
# Test video research agent
from src.mcp_ce.tools.research.video_research_agent import video_research_agent
import asyncio

result = asyncio.run(video_research_agent(
    video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    notion_database_id="your-database-id"
))

assert result["success"]
assert "summary" in result["data"]
assert "research_topics" in result["data"]
print(f"Research complete: {result['data']['notion_page_id']}")
```

**Success Criteria:**
- ✅ Agent executes full workflow
- ✅ All atomic tools called correctly
- ✅ Research document compiled
- ✅ Notion page created (if configured)

#### 4.2 Create Additional Agents

**Agents to Create:**
- `summarizer/video_summarizer_agent.py` - Simpler agent just for summarization
- `crawl4ai/web_research_agent.py` - Web scraping and research
- `discord/discord_admin_agent.py` - Discord server management tasks

**Pattern:** Each agent follows same structure:
1. Import atomic tools
2. Orchestrate workflow
3. Return compiled results

**Success Criteria:**
- ✅ 3-4 example agents implemented
- ✅ All agents registered with `@register_command`
- ✅ All agents work via MCP and Python

---

### Phase 5: Documentation & Cleanup (Week 5)

**Goal:** Update all documentation and remove deprecated code.

#### 5.1 Update Copilot Instructions

**File to Update:**
- `.github/copilot-instructions.md`

**Tasks:**
1. ✅ Add "Architectural Principles" section
2. ✅ Update "Tool Development Patterns" with decorator pattern
3. ✅ Add "Tool Caching Pattern" section
4. ✅ Add "Documentation Hierarchy" section
5. ✅ Update "Search and Exploration Tips"
6. ✅ Remove all references to manual three-location registration

**Success Criteria:**
- ✅ Documentation reflects current architecture
- ✅ No outdated patterns remain
- ✅ Clear examples for all patterns

#### 5.2 Update Tool Instructions

**File to Update:**
- `.github/instructions/mcp-ce-tools.instructions.md`

**Tasks:**
1. ✅ Remove three-step registration process
2. ✅ Add decorator pattern examples
3. ✅ Add caching guidelines
4. ✅ Update validation checklist

**Success Criteria:**
- ✅ Instructions match new architecture
- ✅ No conflicting guidance

#### 5.3 Create Architecture Decision Record

**File to Create:**
- `ARCHITECTURE.md`

**Content:**
```markdown
# Architecture Decision Records

## ADR-001: Decorator-Based Tool Registration

**Date:** November 16, 2025
**Status:** Accepted

**Context:**
Previous architecture required manual registration in three locations:
1. _SERVERS_REGISTRY dict
2. query_tool_docs() function
3. _execute_tool() function

This was error-prone and didn't scale.

**Decision:**
Use `@register_command(server, tool)` decorator pattern for automatic registration.

**Consequences:**
- Positive: One location to register tools
- Positive: Auto-discovery from decorators
- Positive: Scales to 1000+ tools
- Negative: Breaking change (no backward compatibility)

**Implementation:**
See `IMPLEMENTATION_PLAN.md` Phase 1-3.

---

## ADR-002: Atomic Tool Design

**Date:** November 16, 2025
**Status:** Accepted

**Context:**
Need tools to work both as MCP tools (called by LLMs) and as standalone functions (called by agents).

**Decision:**
All tools must be atomic:
- One task per tool
- No cross-tool dependencies
- Work as MCP tools AND Python functions
- Agents orchestrate tools for complex workflows

**Consequences:**
- Positive: Testable in isolation
- Positive: Reusable across contexts
- Positive: Composable into complex workflows
- Negative: More tools needed (can't bundle functionality)

**Implementation:**
See `IMPLEMENTATION_PLAN.md` Phase 4 for agent composition patterns.

---

## ADR-003: Cache Wrapper Design

**Date:** November 16, 2025
**Status:** Accepted

**Context:**
Many tools make expensive API calls (YouTube, Notion, Discord) with rate limits.

**Decision:**
Implement `@cache_tool(ttl=X)` decorator for optional file-based caching.

**Consequences:**
- Positive: Reduces API calls and improves performance
- Positive: Respects rate limits
- Positive: Optional per tool (not enforced)
- Negative: Adds complexity (cache invalidation, storage)

**Implementation:**
See `CACHE_WRAPPER_DESIGN.md` for complete specification.
```

**Success Criteria:**
- ✅ All major architectural decisions documented
- ✅ Rationale and consequences explained
- ✅ Implementation references provided

#### 5.4 Update README Files

**Files to Update:**
- `README.md` (root) - Update feature list
- `src/mcp_ce/README.md` - Update usage examples
- `src/mcp_ce/tools/*/README.md` - Update tool examples

**Tasks:**
1. ✅ Update tool examples to show decorators
2. ✅ Add caching examples
3. ✅ Update discovery workflow examples
4. ✅ Add agent composition examples

**Success Criteria:**
- ✅ All README files current
- ✅ Examples use new patterns
- ✅ No deprecated patterns shown

#### 5.5 Remove Deprecated Code

**Files to Clean:**
- `.github/instructions/mcp-ce-tools.instructions.md` - Remove old patterns
- Any test files using old patterns

**Tasks:**
1. ✅ Search for references to old patterns
2. ✅ Remove or update deprecated code
3. ✅ Ensure all tests pass

**Validation:**
```bash
# Search for deprecated patterns
grep -r "_SERVERS_REGISTRY" src/
grep -r "three locations" .github/

# Should return no results after cleanup
```

**Success Criteria:**
- ✅ No references to old patterns
- ✅ All tests pass
- ✅ Clean codebase

---

## Testing Strategy

### Unit Tests

**Coverage Requirements:**
- ✅ Cache decorator: 100% coverage
- ✅ Registry decorator: 100% coverage
- ✅ Runtime functions: 90%+ coverage
- ✅ Individual tools: 80%+ coverage

**Test Files:**
- `tests/test_cache.py` - Cache decorator tests
- `tests/test_registry.py` - Registry decorator tests
- `tests/test_runtime.py` - Runtime discovery tests
- `tests/test_tools_*.py` - Per-server tool tests

### Integration Tests

**Scenarios:**
1. ✅ Full discovery workflow (discover → query → execute)
2. ✅ Tool execution via MCP protocol
3. ✅ Tool execution via Python code
4. ✅ Agent composition (multi-tool workflows)
5. ✅ Cache hit/miss behavior
6. ✅ Error handling and recovery

### Manual Testing

**Checklist:**
- [ ] Install fresh on new machine
- [ ] Run all tools via Claude Desktop
- [ ] Execute video research agent end-to-end
- [ ] Verify cache files created
- [ ] Check Notion integration
- [ ] Test Discord bot integration

---

## Deployment Checklist

### Pre-Deployment

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Performance validated (no regressions)

### Deployment Steps

1. [ ] Merge to main branch
2. [ ] Tag release: `v2.0.0` (major version for breaking changes)
3. [ ] Update PyPI package
4. [ ] Update Smithery deployment
5. [ ] Notify users of breaking changes

### Post-Deployment

- [ ] Monitor error logs
- [ ] Check cache hit rates
- [ ] Validate tool execution metrics
- [ ] Gather user feedback

---

## Success Metrics

### Performance

- **Cache hit rate:** Target 60%+ for cacheable tools
- **Tool execution time:** No regression vs. current
- **Discovery overhead:** < 200 tokens (current: ~200 tokens, maintain)

### Code Quality

- **Lines of code:** Reduce by ~200 lines (remove if/elif chains)
- **Test coverage:** Increase to 85%+
- **Documentation coverage:** 100% (all patterns documented)

### Developer Experience

- **Time to add new tool:** < 5 minutes (vs ~15 minutes previously)
- **Registration locations:** 1 (vs 3 previously)
- **Onboarding time:** < 30 minutes to understand architecture

---

## Risks & Mitigation

### Risk 1: Breaking Changes

**Risk:** Users relying on old patterns will break.
**Mitigation:** 
- Document migration in `MIGRATION.md`
- Version bump to 2.0.0 (signals breaking change)
- No backward compatibility burden

### Risk 2: Cache Storage Growth

**Risk:** `.cache/` directory grows unbounded.
**Mitigation:**
- Implement `cleanup_expired_cache()` function
- Document cache management
- Add cache size monitoring

### Risk 3: Schema Generation Complexity

**Risk:** Auto-generating schemas from type hints may fail for complex types.
**Mitigation:**
- Start with simple types (str, int, bool, list, dict)
- Add special handling for complex types as needed
- Fallback to manual schema definition if needed

---

## Timeline Summary

| Phase | Week | Status |
|-------|------|--------|
| Phase 1: Core Infrastructure | Week 1 | Ready |
| Phase 2: Tool Migration | Week 2-3 | Ready |
| Phase 3: Runtime Refactoring | Week 3 | Ready |
| Phase 4: Agent Implementation | Week 4 | Ready |
| Phase 5: Documentation & Cleanup | Week 5 | Ready |

**Total Duration:** 5 weeks  
**Start Date:** [To be filled]  
**Target Completion:** [To be filled]

---

## Approval

**Architecture Approved By:** [To be filled]  
**Implementation Start:** [To be filled]  
**Target Release:** v2.0.0
