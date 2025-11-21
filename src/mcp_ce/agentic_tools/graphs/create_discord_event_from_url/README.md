# Create Discord Event from URL

Graph workflow that scrapes websites, extracts event information, and creates Discord scheduled events.

## Overview

This workflow follows the atomic tool pattern:
1. **Scrape** - Uses `crawl_website` tool to extract content
2. **Extract** - Uses quality-controlled event extraction to get structured event details
3. **Create** - Uses `create_scheduled_event` tool to create Discord event

## Usage

```python
from mcp_ce.agentic_tools.graphs.create_discord_event_from_url import (
    create_discord_event_from_url
)

result = await create_discord_event_from_url(
    url="https://www.bluesmuse.dance/",
    discord_server_id=None,  # Uses first available server if not provided
    quality_threshold=0.7,
    max_iterations=3,
)

if result['success']:
    print(f"Created event: {result['event'].title}")
    print(f"Discord URL: {result['discord_event_url']}")
else:
    print(f"Errors: {result['errors']}")
```

## Architecture

This workflow uses **atomic tools** directly, following the repository's design patterns:

- ✅ **Atomic Tools** - Each tool performs a single, well-defined task
- ✅ **No Cross-Tool Dependencies** - Tools don't call other tools
- ✅ **Composable** - Workflow composes tools to create complex behavior
- ✅ **Logfire Instrumentation** - Full observability

## Tools Used

1. **`crawl_website`** - Web scraping tool (from `mcp_ce.tools.crawl4ai`)
2. **`extract_event_with_quality_control`** - Event extraction with quality evaluation
3. **`create_scheduled_event`** - Discord event creation (from `mcp_ce.tools.discord`)
4. **`list_servers`** - Discord server discovery (from `mcp_ce.tools.discord`)

## Return Value

```python
{
    "success": bool,              # Overall workflow success
    "event": EventDetails,         # Extracted event details
    "quality_score": {             # Extraction quality metrics
        "overall": float,
        "completeness": float,
        "accuracy": float,
        "confidence": float,
        "issues": List[str],
        "is_acceptable": bool,
    },
    "discord_event_id": str,        # Discord event ID (if created)
    "discord_event_url": str,       # Discord event URL (if created)
    "errors": List[str],           # Any errors encountered
}
```

## Related Workflows

- **`create_event_from_url_with_supabase`** - Same workflow but also saves to Supabase
- **`extract_events_from_url`** - Multi-agent workflow for extracting multiple events

## Error Handling

The workflow handles errors gracefully:
- Scraping failures are caught and reported
- Event extraction quality issues are logged
- Discord bot readiness is checked before attempting creation
- All errors are collected and returned in the `errors` list

## Example Output

```
📡 Step 1: Scraping https://www.bluesmuse.dance/...
✅ Scraped 15234 characters

🤖 Step 2: Extracting event details with quality control...
✅ Final extraction quality: 0.85
   Event: Blues Dance Social
   Date: November 23, 2025
   Time: 7:00 PM

📅 Step 3: Creating Discord event...
   Using first available server: My Server
✅ Discord event created: https://discord.com/events/...
```

