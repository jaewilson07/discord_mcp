# MCP Discord Server - Repository Instructions

This repository implements a Model Context Protocol (MCP) server providing Discord bot integration with a unified zero-context discovery architecture (MCP CE).

## Repository Overview

**Type:** Python MCP Server with Multi-Server Architecture  
**Primary Languages:** Python 3.11+  
**Key Frameworks:** discord.py 2.4.0, mcp 1.21.1, fastmcp 2.13.0.2, mcp-agent 0.2.5  
**Architecture:** Unified MCP CE (Code Execution) runtime with 7 integrated servers

## Architectural Principles

### Atomic Tool Design

**Core Principle:** Tools must be **atomic** - performing a single, well-defined task that can work independently.

**Key Requirements:**

1. **Dual Functionality:**
   - Tools MUST work as MCP tools (called by LLMs via MCP protocol)
   - Tools MUST work as standalone functions (called by agents/other Python code)

2. **No Cross-Tool Dependencies:**
   - Tools should NOT call other tools directly
   - Shared functionality belongs in helpers (`_bot_helper.py`, `_client_helper.py`)
   - Cross-cutting concerns (cache, registry, auth) are allowed via decorators/helpers

3. **Single Responsibility:**
   - Each tool performs ONE task well
   - Complex workflows are handled by agents composing multiple tools
   - Tools return data, not side effects from other tools

**Why This Matters:**

This architecture enables:
- **Composability:** Agents can orchestrate tools to create complex workflows
- **Testability:** Each tool can be tested in isolation
- **Reusability:** Same tool works in MCP context or Python code
- **Maintainability:** Changes to one tool don't cascade to others

### Agent Composition Pattern

Agents orchestrate atomic tools to accomplish complex tasks. Tools remain simple; agents handle the workflow.

**Example: Video Research Workflow**

User request: *"Summarize a video and research topics mentioned in the video and explore links from the description"*

**Required Atomic Tools:**
1. `get_video_metadata` - Retrieve video title, description, published date
2. `get_transcript` - Retrieve video transcript/captions
3. `summarize_transcript` - Summarize transcript text
4. `create_research_plan` - Generate research plan from topics
5. `search_web` - Search the web for topics
6. `crawl_url` - Scrape/extract content from URLs
7. `create_notion_page` - Save research document to Notion

**Agent Implementation Pattern:**
```python
from registry import register_command

@register_command("research", "video_research_agent")
async def video_research_agent(video_url: str) -> Dict[str, Any]:
    """
    Orchestrates video analysis and topic research.
    
    Composes atomic tools without calling them directly as tools.
    """
    # Import and call atomic tools as Python functions
    from mcp_ce.tools.youtube.get_video_metadata import get_video_metadata
    metadata = await get_video_metadata(video_id=extract_id(video_url))
    
    from mcp_ce.tools.youtube.get_transcript import get_transcript
    transcript = await get_transcript(video_id=extract_id(video_url))
    
    from mcp_ce.tools.summarizer.summarize_transcript import summarize_transcript
    summary = await summarize_transcript(transcript=transcript["data"]["text"])
    
    # ... orchestrate remaining tools
    
    return {"success": True, "data": compiled_research}
```

**Key Observations:**
- ✅ Each tool is atomic: `get_video_metadata` only gets metadata
- ✅ Agent orchestrates: Workflow logic in agent, not tools
- ✅ Tools work standalone: Each callable independently or via MCP
- ✅ Shared helpers OK: Tools use `get_client()` for auth
- ✅ Cross-cutting OK: Decorators for cache/registry don't violate atomicity

### Backward Compatibility Policy

**We are NOT concerned with backward compatibility during this architecture transition.**

- Legacy patterns (hardcoded registry, manual registration) will be **deprecated and removed**
- Tools will be refactored to use decorator pattern without maintaining old registration
- Breaking changes are acceptable to achieve clean architecture
- Migration will be documented but not backwards-compatible

**Rationale:** Clean architecture now is more valuable than maintaining technical debt.

### Current Refactoring Status (November 2025)

**Overview:** Tools are being migrated to use `ToolResponse` with structured dataclasses instead of raw dictionaries.

**Compliance Status:**

| Tool Category | Status | Dataclass Models | Test Coverage | Notes |
|---------------|--------|------------------|---------------|-------|
| **Discord** (21) | ✅ Complete | 16 models | ✅ 100% (495 lines) | All tools return ToolResponse, live testing validated |
| **YouTube** (3) | ✅ Complete | 4 models | ✅ 100% (292 lines) | All tools cached, production test suite |
| **Notion** (6) | ✅ Complete | 6 models | ✅ 100% (430 lines) | All tools return ToolResponse, UPSERT pattern implemented |
| **Crawl4AI** (3) | ✅ Complete | 2 models | ✅ 100% (230 lines) | All tools return ToolResponse, cache integration |
| **URL Ping** (1) | ✅ Complete | 1 model | ✅ 100% (175 lines) | All tools return ToolResponse, cache integration |
| **Overall** (34) | ✅ Excellent | 29+ models | ✅ 100% (34/34) | Production-ready, full test coverage achieved! |

**What's Complete:**
- ✅ **All 34 tools return ToolResponse** with structured dataclasses (100% compliance)
- ✅ **Discord tools** (21 tools, 16 dataclasses, live server testing - 9 bugs fixed)
- ✅ **YouTube tools** (3 tools, 4 dataclasses, production test suite)
- ✅ **Notion tools** (6 tools, 6 dataclasses, production test suite with UPSERT pattern)
- ✅ **Crawl4AI tools** (3 tools, 2 dataclasses, production test suite, DeepCrawlResult inheritance fixed)
- ✅ **URL Ping tool** (1 tool, 1 dataclass, production test suite)
- ✅ **100% test coverage achieved** (34/34 tools with production test suites)
- ✅ Cache system with `override_cache` parameter (14 tools cached)
- ✅ Helper pattern (`_bot_helper.py`, `_client_helper.py`)
- ✅ Decorator pattern (`@register_command`, `@cache_tool`)
- ✅ Cache deserialization for all dataclasses
- ✅ Design patterns documented (`docs/DESIGN_PATTERNS.md`)

**Discovered Patterns (Reusable):**
- ✅ **Helper Pattern** - Singleton bot/client access (Discord, Notion)
- ✅ **Upsert Pattern** - Create or update to prevent duplicates (`upsert_scheduled_event`)
- ✅ **Timestamp Tracking** - Validate test execution with automatic timestamps
- ✅ **Cache Decorator** - Standardized caching with `override_cache` parameter
- ✅ **URL Extraction** - Handle both IDs and full URLs (`_utils.py` in YouTube)

**What's Pending:**
- 🎉 **All code review action items completed!**
- 🚀 **Project is production-ready with 100% test coverage**

**Design Pattern (Target State):**
```python
# Tool with dataclass result
from dataclasses import dataclass
from mcp_ce.tools.model import ToolResponse, ToolResult

@dataclass
class ToolNameResult(ToolResult):
    field1: str
    field2: int

@register_command("server", "tool_name")
@cache_tool(ttl=3600, id_param="param_name")
async def tool_name(param_name: str, override_cache: bool = False) -> ToolResponse:
    result = ToolNameResult(field1="value", field2=123)
    return ToolResponse(is_success=True, result=result)
```

**Migration Guide:** See `COMPREHENSIVE_CODE_REVIEW.md` for detailed action plan.

## Project Structure

### Core Components
- `src/mcp_ce/` - Unified MCP Code Execution runtime (7 servers)
  - `runtime.py` - Zero-context discovery engine, tool registry, and execution dispatcher
  - `server.py` - Main MCP server implementation (base FastMCP server with run_python tool)
  - `sandbox.py` - Python code execution sandbox with injected runtime helpers
  - `cache/` - Cache utilities (infrastructure, not user-facing tools)
    - `cache.py` - General tool result caching with TTL
    - `notion_cache.py` - Notion-specific URL caching to avoid re-scraping
    - `cache_manager.py` - Cache management utilities (clear, stats, cleanup, list)
    - `__init__.py` - Unified cache exports
  - `tools/` - Tool implementations organized by server:
    - `discord/` (19 tools) - Discord bot operations
    - `url_ping/` (1 tool) - URL ping utility
    - `youtube/` (3 tools) - YouTube API integration
    - `notion/` (6 tools) - Notion API integration
    - `crawl4ai/` (3 tools) - Web scraping
    - `events/` - Event extraction workflow helpers (not MCP tools, used by agents)
  - `models/` - Pydantic data models (EventDetails, NotionExport, YouTube)

- `src/agency/` - AI Agent orchestration system (separate from MCP CE)
- `src/registry.py` - Tool registration system with ToolResponse enforcement

### Cache Architecture

**Location:** `src/mcp_ce/cache/` (infrastructure utilities, NOT tools)

**Purpose:** Centralized caching infrastructure for expensive operations.

**Key Principle:** Cache utilities belong in infrastructure, not scattered in tool directories.

**Available Utilities:**
1. **`cache_tool` decorator** - General tool result caching
   - File-based caching with TTL expiration
   - Supports both dict and ToolResponse formats
   - Use for expensive API calls, computations

2. **`check_url_in_notion`** - Query Notion for cached scraped URLs
   - Checks if URL already scraped and stored in Notion database
   - Avoids re-scraping recently processed content
   - Returns cached page data if fresh

3. **`check_multiple_urls_in_notion`** - Batch URL checking
   - Efficiently check multiple URLs at once
   - Returns dict mapping URL → cached data

4. **Cache Management** - Administrative utilities
   - `clear_cache(pattern)` - Clear cache entries (optionally by pattern)
   - `cache_stats()` - Get cache statistics (total entries, size, expired count)
   - `cleanup_expired_cache(ttl)` - Remove expired entries
   - `list_cache_entries(limit)` - List cache entries with metadata

**Import Pattern:**
```python
from mcp_ce.cache import (
    cache_tool,
    check_url_in_notion,
    check_multiple_urls_in_notion,
    clear_cache,
    cache_stats,
)
```

**Why NOT in tools/?**
- Tools are user-facing operations (called by LLMs/users)
- Cache utilities are infrastructure (called by tools internally)
- Separation of concerns improves discoverability and maintainability

### Configuration Files
- `pyproject.toml` - Project dependencies and build configuration
- `requirements.txt` - Python package requirements
- `run.py` - Main entry point for Discord MCP server
- `Dockerfile` - Container configuration
- `.github/copilot-instructions.md` - This file

### Temporary Files
- `TEMP/` - **All temporary test files, scripts, and scratch work must go here**
  - Test scripts (e.g., `test_*.py`, `run_*.py`)
  - Temporary data files
  - Debug scripts
  - Scratch files
  - **Never create test/temp files in the root directory**

## Tool Development Patterns

### Tool Registration Pattern (Decorator-Based)

**REQUIRED:** All tools use the `@register_command` decorator for automatic registration.

**File Location:** `src/mcp_ce/tools/{server_name}/{tool_name}.py`

**Complete Tool Pattern:**
```python
"""Brief tool description."""

from dataclasses import dataclass, field
from typing import Optional, List
from registry import register_command
from mcp_ce.cache import cache_tool  # Optional: for caching
from mcp_ce.tools.model import ToolResponse, ToolResult

# 1. Define result dataclass (extends ToolResult)
@dataclass
class ToolNameResult(ToolResult):
    """
    Structured result from tool_name.
    
    Attributes:
        field1: Description of field1
        field2: Description of field2
    """
    field1: str
    field2: int
    field3: List[str] = field(default_factory=list)

# 2. Implement tool returning ToolResponse with dataclass result
@register_command("server_name", "tool_name")
@cache_tool(ttl=3600, id_param="required_param")  # Optional: cache for 1 hour
async def tool_name(
    required_param: str,
    optional_param: Optional[int] = None,
    override_cache: bool = False
) -> ToolResponse:
    """
    Detailed tool description.
    
    Args:
        required_param: Parameter description
        optional_param: Optional parameter (default: None)
        override_cache: Bypass cache and force fresh fetch (default: False)
        
    Returns:
        ToolResponse with ToolNameResult dataclass containing:
        - field1: Description
        - field2: Description
        - field3: Description
    """
    try:
        # Tool implementation
        data = await some_operation(required_param, optional_param)
        
        result = ToolNameResult(
            field1=data["field1"],
            field2=data["field2"],
            field3=data.get("field3", []),
        )
        
        return ToolResponse(
            is_success=True,
            result=result,
        )
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=str(e),
        )
```

**Testing Pattern:**

Production test suites belong in `TESTS/mcp_ce/tools/{category}/test_{category}_tools.py` mirroring the `src/` structure. For quick validation or temporary testing, use `TEMP/test_{tool_name}.py`.

**Production Test Example** (in `TESTS/mcp_ce/tools/youtube/test_youtube_tools.py`):

```python
"""Production test suite for YouTube tools."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Import tools
from src.mcp_ce.tools.youtube.get_transcript import get_transcript
from src.mcp_ce.tools.youtube.get_video_metadata import get_video_metadata
from src.mcp_ce.tools.youtube.search_youtube import search_youtube

async def test_youtube_tools():
    """Comprehensive test suite for YouTube tools."""
    
    # Test 1: Get video metadata
    print("=" * 50)
    print("Test 1: Get Video Metadata")
    print("=" * 50)
    result = await get_video_metadata(video_id="SJi469BuU6g")
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Title: {result.result.title}")
        print(f"   Channel: {result.result.channel_title}")
    
    # Test 2: Get transcript
    print("\n" + "=" * 50)
    print("Test 2: Get Transcript")
    print("=" * 50)
    result = await get_transcript(video_id="SJi469BuU6g")
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Language: {result.result.language}")
        print(f"   Length: {result.result.length} characters")
    
    # Test 3: Search YouTube
    print("\n" + "=" * 50)
    print("Test 3: Search YouTube")
    print("=" * 50)
    result = await search_youtube(query="python tutorials", max_results=5)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Found {len(result.result['videos'])} videos")
    
    # Test 4: Error handling
    print("\n" + "=" * 50)
    print("Test 4: Error Handling")
    print("=" * 50)
    result = await get_video_metadata(video_id="invalid_id_format")
    print(f"❌ Error handled: {not result.is_success}")
    if not result.is_success:
        print(f"   Error message: {result.error}")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_youtube_tools())
```

**Quick Validation Test** (temporary in `TEMP/test_tool_name.py`):

```python
"""Quick validation test for tool_name."""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from src.mcp_ce.tools.server_name.tool_name import tool_name

async def test_tool_name():
    """Quick test for tool_name."""
    result = await tool_name(required_param="test_value")
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Result: {result.result}")
    else:
        print(f"   Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_tool_name())
```

**Benefits:**
- ✅ Single location to register tools (DRY principle)
- ✅ Auto-discovery by runtime (no manual runtime.py updates)
- ✅ Chainable with cache decorator
- ✅ Works as MCP tool AND standalone Python function
- ✅ Aligns with Anthropic code execution model

### Tool Requirements

1. **Always async functions** - All tools must be async (even if not doing async operations)
2. **Return ToolResponse** - All tools must return `ToolResponse(is_success, result, error)` instance from `src/mcp_ce/tools/model.py`
3. **Structured result with dataclasses** - Tool results must be modeled as dataclasses extending `ToolResult` for deterministic, type-safe responses
4. **Comprehensive docstrings** - Used for auto-generated tool schemas
5. **Error handling** - Always wrap in try/except, return ToolResponse with error
6. **Atomic design** - One task per tool, no cross-tool calls
7. **Standalone capable** - Must work when called directly from Python code
8. **Production test suite** - Each tool category must have a test suite in `TESTS/mcp_ce/tools/{category}/test_{category}_tools.py`

### Tools vs Agents: Data Models

**Tools return deterministic, structured data:**
- Use **dataclasses** extending `ToolResult` for tool response models
- Tools produce predictable, well-defined outputs (API responses, database queries, file operations)
- Dataclasses provide type safety, IDE autocomplete, and clean serialization
- Examples: `CrawlResult`, `Transcript`, `VideoMetadata`

**Agents return LLM-generated, validated data:**
- Use **Pydantic `BaseModel`** for agent response models
- Agents orchestrate tools and use LLMs to process/transform data
- Pydantic provides runtime validation, coercion, and LLM output formatting
- Examples: Research plans, summaries, extracted insights, structured analysis

**Why this distinction matters:**
```python
# TOOL: Deterministic API call → dataclass
@dataclass
class Transcript(ToolResult):
    video_id: str
    transcript: str
    language: str
    # Predictable structure from YouTube API

# AGENT: LLM-generated analysis → Pydantic
class TranscriptAnalysis(BaseModel):
    key_topics: List[str]
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str
    # Validated/coerced from LLM output
```

### Creating Discord Tools

Discord tools require bot client access via the singleton helper:

```python
from registry import register_command
from mcp_ce.cache import cache_tool
from ._bot_helper import get_bot

@register_command("discord", "send_message")
async def send_message(channel_id: str, content: str) -> Dict[str, Any]:
    """Send a message to a Discord channel."""
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channel_id))
        
        if not channel:
            return {"success": False, "error": f"Channel {channel_id} not found"}
        
        message = await channel.send(content)
        
        return {
            "success": True,
            "data": {
                "message_id": str(message.id),
                "channel_id": str(message.channel.id),
                "content": content,
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@register_command("discord", "get_user_info")
@cache_tool(ttl=1800)  # Cache for 30 minutes
async def get_user_info(user_id: str) -> Dict[str, Any]:
    """Get user profile information (cached)."""
    try:
        bot = get_bot()
        user = await bot.fetch_user(int(user_id))
        
        return {
            "success": True,
            "data": {
                "id": str(user.id),
                "name": user.name,
                "discriminator": user.discriminator,
                "avatar_url": str(user.avatar.url) if user.avatar else None,
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Bot Management:** 
- Bot instance managed by `src/mcp_ce/tools/discord/_bot_helper.py`
- Use `get_bot()` to retrieve bot instance
- Use `set_bot(bot)` during server initialization
- Use `is_bot_ready()` to check bot status

**Caching Guidelines:**
- ❌ Don't cache side effects (send_message, add_reaction, create_channel)
- ✅ Cache read-only operations (get_user_info: 30min, get_channel: 5min, get_server_info: 10min)

### Creating YouTube Tools

YouTube tools use the client helper pattern with structured dataclass results:

```python
from dataclasses import dataclass, field
from typing import List, Optional
from registry import register_command
from mcp_ce.cache import cache_tool
from mcp_ce.tools.model import ToolResponse, ToolResult
from ._client_helper import get_client

# Define result model in tools/youtube/models.py
@dataclass
class Transcript(ToolResult):
    """YouTube video transcript with metadata."""
    video_id: str
    transcript: str
    language: str
    length: int
    is_auto_generated: bool = False
    entries: List[dict] = field(default_factory=list)

@register_command("youtube", "get_transcript")
@cache_tool(ttl=7200, id_param="video_id")  # Cache for 2 hours
async def get_transcript(
    video_id: str, 
    languages: Optional[List[str]] = None,
    override_cache: bool = False
) -> ToolResponse:
    """Extract transcript from YouTube video (cached)."""
    try:
        # Tool implementation
        transcript_data = await fetch_transcript(video_id, languages)
        
        result = Transcript(
            video_id=video_id,
            transcript=transcript_data["text"],
            language=transcript_data["language"],
            length=len(transcript_data["text"]),
            is_auto_generated=transcript_data["is_generated"],
            entries=transcript_data["entries"],
        )
        
        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
```

**Caching Guidelines:**
- `get_video_metadata`: 1 hour (metadata rarely changes)
- `get_transcript`: 2 hours (transcripts don't change)
- `search_videos`: 5 minutes (search results change frequently)

### Creating Notion Tools

Notion tools use the official notion-sdk-py (https://github.com/ramnes/notion-sdk-py) via the client helper pattern.

**IMPORTANT:** Notion API version 2025-09-03 introduced breaking changes for multi-source databases:
- `database_id` and `data_source_id` are now distinct
- Database operations (query, create page) require `data_source_id`
- Use `get_data_source_id_from_database()` helper to retrieve data_source_id
- See: https://developers.notion.com/docs/upgrade-guide-2025-09-03

```python
from typing import Optional
from registry import register_command
from mcp_ce.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from ._client_helper import get_client, get_data_source_id_from_database

@register_command("notion", "query_notion_database")
@cache_tool(ttl=180)  # Cache for 3 minutes
async def query_notion_database(database_id: str, filter_json: Optional[str] = None) -> ToolResponse:
    """Query a Notion database using data sources API (2025-09-03)."""
    try:
        client = get_client()  # Returns notion_client.AsyncClient
        
        # Step 1: Get data_source_id from database_id (required for 2025-09-03 API)
        data_source_id = await get_data_source_id_from_database(database_id)
        
        # Step 2: Query using data_sources endpoint
        response = await client.request(
            path=f'data_sources/{data_source_id}/query',
            method='POST',
            body={"filter": filter_json} if filter_json else {}
        )
        
        return ToolResponse(
            is_success=True,
            result=response.get("results", [])
        )
    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Failed to query database: {str(e)}"
        )


@register_command("notion", "create_notion_page")
async def create_notion_page(database_id: str, properties: dict) -> ToolResponse:
    """Create a page in a Notion database."""
    try:
        client = get_client()  # Returns notion_client.AsyncClient
        
        # Create page using database_id (SDK handles data_source_id internally)
        page = await client.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        
        return ToolResponse(
            is_success=True,
            result={"page_id": page["id"], "url": page["url"]}
        )
    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Failed to create page: {str(e)}"
        )
```

**Client Helper Pattern:**
- Helper location: `src/mcp_ce/tools/notion/_client_helper.py`
- Returns: `notion_client.AsyncClient` (singleton pattern)
- Environment: Requires `NOTION_TOKEN` environment variable
- Error handling: Raises `RuntimeError` if token missing
- **Key Helper:** `get_data_source_id_from_database(database_id)` - Required for database queries

**API Version 2025-09-03 Key Changes:**
1. **Database Query:** Use `data_sources/{data_source_id}/query` instead of `databases/{database_id}/query`
2. **Get Data Source ID:** Always call `get_data_source_id_from_database()` before querying
3. **Create Page:** Can still use `database_id` as parent (SDK translates internally)
4. **Search:** Returns `data_source` objects instead of `database` objects

**Caching Guidelines:**
- ❌ Don't cache write operations (create_notion_page, update_notion_page, add_notion_comment)
- ✅ Cache read operations (get_notion_page: 5min, query_database: 3min, search_notion: 3min)

### Creating Agent Tools

Agents orchestrate multiple atomic tools to accomplish complex workflows. Use **Pydantic BaseModel** for agent results to validate LLM-generated outputs:

```python
from pydantic import BaseModel, Field
from typing import List
from registry import register_command
from mcp_ce.tools.model import ToolResponse

# Agent result model uses Pydantic for LLM output validation
class VideoResearchResult(BaseModel):
    """LLM-generated research analysis (validated by Pydantic)."""
    video_title: str
    key_topics: List[str] = Field(description="Main topics discussed")
    summary: str = Field(min_length=100)
    sentiment: str = Field(pattern="^(positive|neutral|negative)$")
    notion_page_id: str
    notion_page_url: str

@register_command("research", "video_research_agent")
async def video_research_agent(video_url: str, notion_database_id: str) -> ToolResponse:
    """
    Orchestrates video analysis and topic research workflow.
    
    This is an AGENT that composes atomic tools and uses LLM for analysis.
    Returns Pydantic-validated result.
    """
    try:
        # Import atomic tools as Python functions (tools return ToolResponse with dataclasses)
        from mcp_ce.tools.youtube.get_video_metadata import get_video_metadata
        from mcp_ce.tools.youtube.get_transcript import get_transcript
        from mcp_ce.agents.analyze_content import analyze_with_llm
        from mcp_ce.tools.notion.create_notion_page import create_notion_page
        
        video_id = extract_video_id(video_url)
        
        # Step 1: Get metadata (tool returns ToolResponse with VideoMetadata dataclass)
        metadata_response = await get_video_metadata(video_id=video_id)
        if not metadata_response.is_success:
            return metadata_response
        metadata = metadata_response.result  # VideoMetadata dataclass
        
        # Step 2: Get transcript (tool returns ToolResponse with Transcript dataclass)
        transcript_response = await get_transcript(video_id=video_id)
        if not transcript_response.is_success:
            return transcript_response
        transcript = transcript_response.result  # Transcript dataclass
        
        # Step 3: LLM analysis (agent uses Pydantic for validation)
        analysis = await analyze_with_llm(
            title=metadata.title,
            transcript=transcript.transcript
        )  # Returns Pydantic model
        
        # Step 4: Save to Notion
        notion_response = await create_notion_page(
            database_id=notion_database_id,
            title=f"Research: {metadata.title}",
            content=analysis.summary
        )
        
        # Return Pydantic-validated agent result
        result = VideoResearchResult(
            video_title=metadata.title,
            key_topics=analysis.key_topics,
            summary=analysis.summary,
            sentiment=analysis.sentiment,
            notion_page_id=notion_response.result.page_id,
            notion_page_url=notion_response.result.url,
        )
        
        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
```

**Key Difference: Tools vs Agents:**

| Aspect | Tool | Agent |
|--------|------|-------|
| Purpose | Single atomic operation | Complex workflow |
| Dependencies | Only helpers (auth, cache) | Calls multiple tools |
| Result Model | **Dataclass** (ToolResult) | **Pydantic BaseModel** |
| Data Source | API/DB (deterministic) | LLM-generated (validated) |
| Example | `get_video_metadata` → `VideoMetadata` | `video_research_agent` → `VideoResearchResult` |
| Registered | Yes (`@register_command`) | Yes (`@register_command`) |
| MCP Callable | Yes | Yes |
| Standalone Callable | Yes | Yes |
| Validation | Type hints only | Pydantic runtime validation |

### Tool Caching Pattern

For tools that make expensive API calls or fetch rarely-changing data, use the `@cache_tool` decorator.

**Basic Usage:**
```python
from registry import register_command
from mcp_ce.cache import cache_tool

@register_command("youtube", "get_video_metadata")
@cache_tool(ttl=3600)  # Cache for 1 hour
async def get_video_metadata(video_id: str) -> Dict[str, Any]:
    # Expensive YouTube API call
    pass
```

**Cache Configuration:**
- `ttl` (int): Time-to-live in seconds (default: 3600)
- `key_func` (Optional[Callable]): Custom cache key generation

**When to Cache:**
- ✅ External API calls with rate limits
- ✅ Data that changes infrequently (metadata, user profiles)
- ✅ Expensive computations
- ❌ Real-time data (messages, live streams)
- ❌ Side effects (send, create, delete operations)

**Custom Cache Keys:**
```python
def video_cache_key(video_id: str, **kwargs) -> str:
    return f"video_{video_id}"

@cache_tool(ttl=7200, key_func=video_cache_key)
async def get_video_metadata(video_id: str, include_stats: bool = False):
    # Caches by video_id only, ignores include_stats
    pass
```

**Integration:** Decorators chain naturally (order matters):
```python
@register_command("notion", "get_notion_page")  # Register first
@cache_tool(ttl=300)  # Then cache
async def get_notion_page(page_id: str) -> Dict[str, Any]:
    pass
```

### Creating MCP-Agent Tools

MCP-Agent tools (like YouTube analysis) use the `@app.tool` decorator pattern:

```python
from mcp_agent import MCPApp, Agent

app = MCPApp("tool-name")

@app.tool()
def sync_tool(param: str) -> str:
    """Synchronous tool description."""
    return f"Result: {param}"

@app.async_tool()
async def async_tool(param: str) -> str:
    """Asynchronous tool description."""
    result = await some_async_operation(param)
    return result

# Create agent with LLM
agent = Agent(
    name="agent-name",
    instructions="Agent behavior instructions",
    app=app,
    llm=llm_instance,
)
```

## Documentation Hierarchy

**Canonical Reference:** `.github/copilot-instructions.md` (this file)

This file is the single source of truth for repository patterns and conventions.

### Documentation Structure

```
.github/
├── copilot-instructions.md (CANONICAL - All patterns & architecture)
├── prompts/                (Custom Copilot prompts for specific tasks)
│   ├── architecture-review.prompt.md
│   ├── code-review.prompt.md
│   └── ...
└── instructions/           (Framework-specific patterns only)
    ├── mcp-agent.instructions.md (MCP-Agent patterns)
    ├── mcp-ce-tools.instructions.md (MCP CE tool patterns)
    └── pydantic-ai.instructions.md (Pydantic-AI patterns)

docs/
└── custom-prompts-guide.md (Guide for using custom prompts)

src/
└── mcp_ce/
    └── README.md           (MCP CE runtime usage examples)

Root level:
├── README.md               (Project overview and quickstart)
├── INSTALL.md              (Installation instructions)
├── CACHE_WRAPPER_DESIGN.md (Cache implementation spec)
├── IMPLEMENTATION_PLAN.md  (5-phase rollout plan)
└── ARCHITECTURE.md         (Architectural decisions - to be created)
```

### Documentation Roles

**`.github/copilot-instructions.md`** (This File)
- **Primary reference for all development**
- Architectural principles (atomic tools, agent composition)
- Tool development patterns (registration, caching, error handling)
- Code style and conventions
- Project structure and organization

**`.github/instructions/*.instructions.md`**
- **Framework-specific patterns only**
- Applied to specific file patterns via frontmatter
- Referenced by copilot-instructions.md
- Examples: MCP-Agent decorators, Pydantic-AI patterns

**`.github/prompts/*.prompt.md`**
- **Task-specific Copilot prompts**
- Architecture review, code review, refactoring, etc.
- Used via Copilot custom prompts feature

**`README.md` (Root)**
- **Public-facing project overview**
- Installation quickstart
- Available tools list
- License and contribution info

**`INSTALL.md`**
- **Detailed installation instructions**
- Environment setup
- Configuration steps
- Troubleshooting

**`CACHE_WRAPPER_DESIGN.md`**
- **Complete cache implementation specification**
- Decorator API, file structure, TTL configuration
- Integration with registry decorator
- Testing strategy

**`IMPLEMENTATION_PLAN.md`**
- **5-phase migration roadmap**
- Detailed tasks with code examples
- Validation commands and success criteria
- Timeline and risk mitigation

**`ARCHITECTURE.md`** (To be created)
- **Architectural Decision Records (ADRs)**
- Why decorator pattern chosen
- Why atomic tools + agent composition
- Cache design rationale
- Migration decisions

### Conflict Resolution

If documentation conflicts:
1. **`.github/copilot-instructions.md` takes precedence** (canonical)
2. Check git history to see which is newer
3. Update conflicting file to align with canonical source

### When to Update Documentation

| Change Type | Update Location |
|-------------|----------------|
| New tool pattern | `.github/copilot-instructions.md` |
| Framework-specific pattern | `.github/instructions/*.instructions.md` |
| Architectural decision | Create/update `ARCHITECTURE.md` with ADR |
| Installation step | `INSTALL.md` |
| Public-facing feature | `README.md` |
| Deprecation | `.github/copilot-instructions.md` + migration guide |

## Building and Running

### Environment Setup

**Always use `uv` for environment management:**

```bash
# Create virtual environment
uv venv

# Activate environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
uv sync

# For Python 3.13+, install audioop-lts
uv pip install audioop-lts
```

**Important:** The `.venv` directory is managed by `uv`. Never manually create or modify it.

### Running the Server

```bash
# Run Discord MCP server
python run.py

# Or use uv
uv run run.py
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_discord_tools.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### Validation Commands

**Always run before committing:**

```bash
# Check Python syntax
python -m py_compile src/mcp_ce/runtime.py

# Compile all Discord tools
Get-ChildItem -Path "src/mcp_ce/tools/discord/*.py" | ForEach-Object { 
    python -m py_compile $_.FullName 
}

# Test runtime integration
python -c "from src.mcp_ce.runtime import discovered_servers; import json; print(json.dumps(discovered_servers(), indent=2))"
```

## Configuration

### Environment Variables

Required for Discord functionality:
- `DISCORD_TOKEN` - Discord bot token (from Discord Developer Portal)

Optional configuration:
- `OPENAI_API_KEY` - For AI-powered features (YouTube agent, summarization)
- `NOTION_API_KEY` - For Notion integration
- `YOUTUBE_API_KEY` - For YouTube API features

### Discord Bot Setup

**Required Privileged Intents:**
- MESSAGE CONTENT INTENT
- PRESENCE INTENT  
- SERVER MEMBERS INTENT

**Bot Permissions:** Configure in Discord Developer Portal OAuth2 URL Generator

## Common Pitfalls and Solutions

### Issue: "Bot not ready" errors in Discord tools
**Solution:** Ensure `set_bot(bot)` is called during server initialization before any tool execution.

### Issue: Import errors in runtime.py
**Solution:** Use dynamic imports in `_execute_tool()`:
```python
# ✓ Correct - dynamic import
from mcp_ce.tools.server_name.tool_name import tool_name

# ✗ Wrong - top-level import (causes circular dependencies)
```

### Issue: Tool not appearing in discovered_servers()
**Solution:** Check all three registration points:
1. `_SERVERS_REGISTRY` - tool listed in tools array
2. `query_tool_docs()` - schema defined
3. `_execute_tool()` - execution handler added

### Issue: "Maximum recursion depth exceeded" in runtime
**Solution:** Avoid circular imports. Use lazy imports in `_execute_tool()`.

### Issue: Type errors with Optional parameters
**Solution:** Always import Optional from typing:
```python
from typing import Optional

def tool(param: Optional[str] = None) -> Dict[str, Any]:
    pass
```

### Issue: Discord API rate limits
**Solution:** Discord tools handle rate limits internally. If persistent, implement exponential backoff:
```python
import asyncio

for attempt in range(3):
    try:
        result = await discord_operation()
        break
    except discord.errors.RateLimited as e:
        await asyncio.sleep(e.retry_after)
```

## Error Handling

### Custom Exceptions Per Tool Server

**Best Practice:** Define custom exception classes for each tool server to provide clear, specific error handling.

**File Location:** `src/mcp_ce/tools/{server_name}/exceptions.py`

**Exception Hierarchy:**
```python
"""Custom exceptions for {server_name} tools."""

class {ServerName}Error(Exception):
    """Base exception for all {server_name} tool errors."""
    pass

class {ServerName}NotFoundError({ServerName}Error):
    """Raised when a resource is not found."""
    pass

class {ServerName}AuthenticationError({ServerName}Error):
    """Raised when authentication fails."""
    pass

class {ServerName}ValidationError({ServerName}Error):
    """Raised when input validation fails."""
    pass

class {ServerName}RateLimitError({ServerName}Error):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: float, message: str = None):
        self.retry_after = retry_after
        super().__init__(message or f"Rate limited. Retry after {retry_after}s")
```

**Usage Example:**
```python
"""Discord tool with custom exceptions."""

from typing import Dict, Any
from .exceptions import DiscordNotFoundError, DiscordAuthenticationError
from ._bot_helper import get_bot

async def send_message(channel_id: str, content: str) -> Dict[str, Any]:
    """
    Send a message to a Discord channel.
    
    Args:
        channel_id: Discord channel ID
        content: Message content
        
    Returns:
        Dictionary with success status and message info
        
    Raises:
        DiscordNotFoundError: If channel is not found
        DiscordAuthenticationError: If bot lacks permissions
    """
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channel_id))
        
        if not channel:
            raise DiscordNotFoundError(f"Channel {channel_id} not found")
        
        message = await channel.send(content)
        
        return {
            "success": True,
            "message_id": str(message.id),
            "channel_id": str(message.channel.id),
        }
    except DiscordNotFoundError:
        # Re-raise custom exceptions as-is
        raise
    except discord.Forbidden as e:
        # Convert Discord API exceptions to custom exceptions
        raise DiscordAuthenticationError(f"Bot lacks permission: {str(e)}") from e
    except ValueError as e:
        # Handle specific errors
        return {"success": False, "error": f"Invalid channel ID: {str(e)}"}
    except Exception as e:
        # Last resort - log unexpected errors
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
```

**Benefits:**
- Clear error semantics (NotFoundError vs AuthenticationError)
- Easier error handling in calling code
- Better logging and debugging
- Consistent error patterns across tools
- Type-safe exception handling

**Guidelines:**
1. **Create exceptions.py per server** - Each tool server should have its own exception module
2. **Inherit from base exception** - All server exceptions inherit from a base (e.g., `DiscordError`)
3. **Be specific** - Use specific exception types for different error conditions
4. **Include context** - Add relevant data as exception attributes (e.g., `retry_after` for rate limits)
5. **Convert library exceptions** - Transform third-party exceptions into custom ones for consistency
6. **Document exceptions** - List raised exceptions in docstrings
7. **Avoid bare except** - Never use `except:` without a type
8. **Re-raise custom exceptions** - Let custom exceptions propagate, catch library exceptions

**Exception Categories:**
- **NotFoundError** - Resource doesn't exist (404-like)
- **AuthenticationError** - Permission/auth issues (401/403-like)
- **ValidationError** - Invalid input data
- **RateLimitError** - API rate limiting
- **TimeoutError** - Operation timed out
- **ConnectionError** - Network/connection issues
- **ConfigurationError** - Missing/invalid configuration

## Code Style and Conventions

### Import Order
```python
# 1. Standard library
import asyncio
from typing import Dict, Any, Optional

# 2. Third-party packages
import discord
from mcp import Tool

# 3. Local imports
from ._bot_helper import get_bot
```

### Docstring Format
```python
def function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description on one line.
    
    Detailed description if needed.
    
    Args:
        param1: Parameter description
        param2: Parameter description
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception occurs
    """
```

### Error Messages
- Be specific and actionable
- Include parameter values when relevant
- Use custom exception classes per tool server (see Error Handling section)

Example:
```python
# ✓ Good
return {"success": False, "error": f"Channel {channel_id} not found"}

# ✗ Bad
return {"success": False, "error": "Error"}
```

## File Naming Conventions

- Tool files: `{tool_name}.py` (snake_case)
- Agent files: `{agent_name}_agent.py`
- Test files: `test_{module_name}.py` - **Must be placed in `TESTS/` directory with structure mirroring `src/`**
- Helper modules: `_{helper_name}.py` (private, prefixed with underscore)
- **Temporary/scratch files**: Always create in `TEMP/` directory, never in root

## Temporary File Policy

**IMPORTANT**: All test scripts, temporary files, and scratch work must be created in the `TEMP/` directory. **Production test suites belong in `TESTS/` with structure mirroring `src/`.**

### Files That Belong in TEMP/
- **Temporary test scripts**: `TEMP/test_*.py` (quick validation, proof-of-concept)
- Run scripts for testing: `TEMP/run_*.py`
- Temporary data files
- Debug/diagnostic scripts
- Proof-of-concept code
- Any file that is not part of the permanent codebase

### Files That Belong in TESTS/
- **Production test suites**: `TESTS/mcp_ce/tools/{category}/test_{category}_tools.py`
- Test structure mirrors `src/` directory structure
- Example: `src/mcp_ce/tools/youtube/get_transcript.py` → `TESTS/mcp_ce/tools/youtube/test_youtube_tools.py`

### Files That Stay in Root/Src
- Production code: `src/`
- Configuration: `pyproject.toml`, `requirements.txt`, `.env`
- Main entry point: `run.py` (permanent server startup)
- Documentation: `*.md` files that document the project

**Why?** Separating temporary files (TEMP/) from production tests (TESTS/) maintains a clean repository structure and makes it clear what is production code, production tests, vs. temporary/scratch work.

## Documentation Requirements

When creating new tools or agents:
1. **Docstring** - Complete function/class documentation
2. **README.md** - In tool/agent directory if complex
3. **Migration doc** - If replacing/deprecating code (see `DISCORD_MIGRATION.md`)
4. **Update this file** - Add to relevant section if new pattern introduced

## Version Information

- **Python:** 3.11+ (3.13+ requires audioop-lts)
- **discord.py:** 2.4.0
- **mcp:** 1.21.1
- **fastmcp:** 2.13.0.2
- **mcp-agent:** 0.2.5
- **OpenAI:** 2.8.0
- **LangChain:** 1.0.7

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP-Agent Documentation](https://github.com/hanselke/mcp-agent)
- [Anthropic Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- Installation Guide: `INSTALL.md`
- Cache Design: `CACHE_WRAPPER_DESIGN.md`
- Implementation Plan: `IMPLEMENTATION_PLAN.md`

## Search and Exploration Tips

When implementing changes:
1. **Check copilot-instructions.md first** - Canonical reference for all patterns
2. **Use decorator pattern** - Add `@register_command` to tools instead of modifying runtime.py
3. **Reference existing tools** - Look at `src/mcp_ce/tools/discord/send_message.py` or `src/mcp_ce/tools/youtube/get_video_metadata.py` for patterns
4. **Add caching for expensive operations** - Use `@cache_tool` for API calls with rate limits
5. **Test incrementally** - Use validation commands after each change
6. **Check framework-specific instructions** - `.github/instructions/*.md` for MCP-Agent, Pydantic-AI patterns

### Validation Commands

**Test tool registration:**
```powershell
# Verify decorator pattern works
python -c "from src.registry import get_registry; print(get_registry())"
```

**Test runtime integration:**
```powershell
# Verify tools are discoverable
python -c "from src.mcp_ce.runtime import discovered_servers; import json; print(json.dumps(discovered_servers(), indent=2))"
```

**Check Python syntax:**
```powershell
python -m py_compile src/mcp_ce/runtime.py
```

**Compile all tools in a server:**
```powershell
Get-ChildItem -Path "src/mcp_ce/tools/discord/*.py" | ForEach-Object { 
    python -m py_compile $_.FullName 
}
```

## Trust These Instructions

These instructions are validated against the current codebase (as of November 2025). Only search for additional information if:
- These instructions are unclear or incomplete
- You encounter errors following these patterns
- You need information about external dependencies (Discord API, etc.)
