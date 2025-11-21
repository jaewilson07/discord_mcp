# Event Agent with Supabase Integration - Summary

## Overview

This document summarizes the event extraction agent that scrapes URLs, saves content to Supabase, extracts event details, and creates Discord events.

## What Was Built

### 1. Agent Function: `create_event_from_url_with_supabase`

**Location:** `src/mcp_ce/agentic_tools/events/create_from_url_supabase.py`

**Purpose:** Complete workflow that:

1. Scrapes a URL using `crawl_website`
2. Saves scraped content to Supabase using `add_document`
3. Extracts structured event details using `extract_event_with_quality_control`
4. Creates a Discord scheduled event using `create_scheduled_event`

**Key Features:**

- ✅ Reuses existing tools from the codebase
- ✅ Logfire instrumentation for monitoring
- ✅ Quality control with evaluator-optimizer pattern
- ✅ Error handling with detailed error reporting
- ✅ Flexible configuration (optional Supabase save, Discord server selection)

**Function Signature:**

```python
async def create_event_from_url_with_supabase(
    url: str,
    discord_server_id: Optional[str] = None,
    save_to_supabase: bool = True,
    supabase_table_name: str = "documents",
    quality_threshold: float = 0.7,
    max_iterations: int = 3,
) -> Dict[str, Any]
```

**Returns:**

```python
{
    "success": bool,
    "event": EventDetails,
    "quality_score": {
        "overall": float,
        "completeness": float,
        "accuracy": float,
        "confidence": float,
        "issues": List[str],
        "is_acceptable": bool
    },
    "discord_event_id": Optional[str],
    "discord_event_url": Optional[str],
    "supabase_document_id": Optional[str],
    "errors": List[str]
}
```

### 2. Test Notebook: `test_event_agent_supabase.ipynb`

**Purpose:** Staged testing with Logfire monitoring

**Sections:**

1. **Setup:** Environment variables and Logfire configuration
2. **Stage Testing:** Test each component individually:
   - Web scraping
   - Supabase storage
   - Event extraction
   - Discord event creation
3. **Complete Workflow:** Test the full agent end-to-end
4. **Logfire Traces:** Instructions for viewing detailed traces

**Benefits:**

- Test each stage independently
- View Logfire traces for debugging
- Understand workflow execution
- Identify bottlenecks

## Tools Reused

The agent reuses existing tools from the codebase:

1. **`crawl_website`** (`src/mcp_ce/tools/crawl4ai/crawl_website.py`)

   - Web scraping with crawl4ai
   - Returns markdown content

2. **`add_document`** (`src/mcp_ce/tools/supabase/add_document.py`)

   - Stores documents in Supabase
   - Handles metadata

3. **`extract_event_with_quality_control`** (`src/mcp_ce/tools/events/evaluator_optimizer.py`)

   - Extracts event details with quality evaluation
   - Uses evaluator-optimizer pattern for refinement

4. **`create_scheduled_event`** (`src/mcp_ce/tools/discord/create_scheduled_event.py`)

   - Creates Discord scheduled events
   - Handles datetime formatting

5. **`list_servers`** (`src/mcp_ce/tools/discord/list_servers.py`)
   - Lists available Discord servers
   - Used for auto-selecting server if not provided

## Models Used

- **`EventDetails`** (`src/mcp_ce/models/events.py`)
  - Comprehensive event data model
  - Includes location, date/time, organizer, pricing, etc.
  - Methods: `get_full_location()`, `convert_datetime_for_discord()`

## Logfire Instrumentation

The agent is fully instrumented with Logfire:

- **Function-level:** `@logfire.instrument()` decorator
- **Span-level:** `logfire.span()` for major operations
- **Event-level:** `logfire.info()`, `logfire.warn()`, `logfire.error()`
- **Context:** URL, event title, quality scores, error messages

**View traces at:** https://logfire.pydantic.dev/

## Usage Example

```python
from mcp_ce.agentic_tools.events.create_from_url_supabase import (
    create_event_from_url_with_supabase
)

# Run the complete workflow
result = await create_event_from_url_with_supabase(
    url="https://www.bluesmuse.dance/",
    save_to_supabase=True,
    quality_threshold=0.7,
    max_iterations=3
)

if result['success']:
    print(f"✅ Created event: {result['event'].title}")
    print(f"   Discord: {result['discord_event_url']}")
    print(f"   Supabase: {result['supabase_document_id']}")
else:
    print(f"❌ Errors: {result['errors']}")
```

## Testing

### Using the Notebook

1. Open `test_event_agent_supabase.ipynb`
2. Run cells sequentially:
   - Section 1: Setup environment
   - Section 2: Test individual stages
   - Section 3: Test complete workflow
3. View Logfire traces for detailed execution logs

### Direct Testing

```python
import asyncio
from mcp_ce.agentic_tools.events.create_from_url_supabase import (
    create_event_from_url_with_supabase
)

async def test():
    result = await create_event_from_url_with_supabase(
        url="https://www.bluesmuse.dance/",
        save_to_supabase=True
    )
    print(result)

asyncio.run(test())
```

## Environment Variables Required

- `OPENAI_API_KEY` - For event extraction
- `DISCORD_BOT_TOKEN` - For Discord bot
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase API key
- `DISCORD_SERVER_ID` (optional) - Discord server ID (auto-detected if not set)
- `LOGFIRE_TOKEN` (optional) - For Logfire monitoring

## Architecture

```
User Request
    ↓
create_event_from_url_with_supabase()
    ↓
┌─────────────────────────────────────┐
│ Step 1: Scrape URL                  │
│ - crawl_website()                    │
│ - Returns markdown content           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Step 2: Save to Supabase            │
│ - add_document()                    │
│ - Stores scraped content            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Step 3: Extract Event Details      │
│ - extract_event_with_quality_      │
│   control()                         │
│ - Evaluator-optimizer pattern       │
│ - Returns EventDetails + quality    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Step 4: Create Discord Event       │
│ - create_scheduled_event()         │
│ - Formats datetime                 │
│ - Creates external event           │
└─────────────────────────────────────┘
    ↓
Return Result Dict
```

## Error Handling

The agent handles errors gracefully:

- **Scraping failures:** Returns error, continues if possible
- **Supabase failures:** Logs warning, continues workflow
- **Extraction failures:** Returns minimal event, logs issues
- **Discord failures:** Logs error, returns partial result

All errors are collected in `result["errors"]` list.

## Quality Control

The agent uses the evaluator-optimizer pattern:

1. **Initial Extraction:** Extract event details
2. **Quality Evaluation:** Score completeness, accuracy, confidence
3. **Optimization:** If quality < threshold, refine extraction
4. **Iteration:** Repeat up to `max_iterations` times

Quality metrics:

- **Overall Score:** Weighted combination
- **Completeness:** Required fields present
- **Accuracy:** Data matches source
- **Confidence:** LLM confidence in extraction

## Next Steps

1. **Test with real URLs:** Run the notebook with various event pages
2. **Monitor Logfire:** View traces to identify bottlenecks
3. **Tune Quality Threshold:** Adjust based on results
4. **Add Customization:** Extend for specific event types
5. **Add Validation:** Additional validation rules if needed

## Files Created

1. `src/mcp_ce/agentic_tools/events/create_from_url_supabase.py` - Main agent function
2. `test_event_agent_supabase.ipynb` - Test notebook with staged execution
3. `EVENT_AGENT_SUPABASE_SUMMARY.md` - This document

## Dependencies

All dependencies are already in the project:

- `crawl4ai` - Web scraping
- `supabase` - Database client
- `discord.py` - Discord bot
- `pydantic-ai` - AI agents
- `logfire` - Observability
- `openai` - LLM for extraction
