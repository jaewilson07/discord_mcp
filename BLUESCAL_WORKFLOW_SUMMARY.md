# BluesCal.com to Discord Event Sync - Implementation Summary

## What Was Built

A complete workflow to automatically extract events from BluesCal.com and sync them to Discord scheduled events, with Notion database integration for duplicate tracking.

## Files Created

### 1. Main Workflow
**File:** `src/mcp_ce/agentic_tools/events/sync_bluescal_events.py`

**Purpose:** Complete workflow that:
- Extracts all events from BluesCal.com
- Checks Notion database for duplicates
- Creates Discord events for new events
- Saves all events to Notion for tracking

**Key Functions:**
- `sync_bluescal_events_to_discord()` - Main workflow function
- `_check_event_duplicate_in_notion()` - Duplicate detection
- `_create_discord_event()` - Discord event creation
- `_save_event_to_notion()` - Notion database save

### 2. Documentation
**File:** `docs/BLUESCAL_WORKFLOW.md`

**Purpose:** Comprehensive documentation including:
- Setup instructions
- Notion database schema
- Usage examples
- Troubleshooting guide
- Best practices

### 3. Test Script
**File:** `test_bluescal_sync.py`

**Purpose:** Interactive test script that:
- Tests the workflow in dry-run mode
- Prompts user before actual sync
- Shows detailed results

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────┐
│ 1. Extract Events from BluesCal.com                    │
│    - Scrape website                                      │
│    - Use AI to extract structured event details          │
│    - Return list of EventDetails objects                 │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Check for Duplicates in Notion                        │
│    - Query Notion database                               │
│    - Match by: Title + Date, or URL                      │
│    - Separate new events from duplicates                 │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Create Discord Events (New Events Only)               │
│    - Parse event date/time                               │
│    - Format description                                   │
│    - Create scheduled event via Discord API              │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Save All Events to Notion                            │
│    - Create database pages                              │
│    - Store event details                                │
│    - Track for future duplicate checks                  │
└─────────────────────────────────────────────────────────┘
```

## Key Features

### ✅ Duplicate Prevention

The workflow uses Notion as a source of truth to prevent creating duplicate Discord events:

1. **Title + Date Matching**: Checks if an event with the same title and date exists
2. **URL Matching**: Checks if an event with the same URL exists
3. **Automatic Tracking**: All events are saved to Notion for future checks

### ✅ Multi-Event Extraction

Unlike single-event extraction workflows, this extracts ALL events from the BluesCal.com calendar page.

### ✅ Error Handling

- Graceful error handling at each step
- Continues processing even if individual events fail
- Collects all errors for review
- Logfire instrumentation for observability

### ✅ Dry Run Mode

Test the workflow without creating events:
```python
result = await sync_bluescal_events_to_discord(dry_run=True)
```

## Notion Database Schema

The workflow expects a Notion database with these properties:

| Property | Type | Purpose |
|----------|------|---------|
| **Name** | Title | Event title (required for duplicate check) |
| **URL** | URL | Event URL (optional, for duplicate check) |
| **Date** | Date | Event date (required for duplicate check) |
| **Location** | Text | Event location |
| **Source** | Select | Source identifier (e.g., "BluesCal.com") |
| **Scrape Date** | Date | When event was scraped |

## Usage Example

```python
from mcp_ce.agentic_tools.events.sync_bluescal_events import (
    sync_bluescal_events_to_discord
)

# Sync events
result = await sync_bluescal_events_to_discord(
    discord_server_id="your_server_id",
    notion_database_id="your_database_id",
    dry_run=False,
    max_events=None,  # Process all events
)

# Check results
print(f"Found {result['total_events_found']} events")
print(f"Created {result['discord_events_created']} Discord events")
print(f"Skipped {result['duplicates_skipped']} duplicates")
```

## Environment Variables Required

```bash
DISCORD_BOT_TOKEN=your_discord_bot_token
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
OPENAI_API_KEY=your_openai_key  # For event extraction
DISCORD_SERVER_ID=your_server_id  # Optional, auto-detected
LOGFIRE_TOKEN=your_logfire_token  # Optional, for observability
```

## Integration with Existing Codebase

The workflow reuses existing tools and patterns:

1. **Event Extraction**: Uses `extract_events_from_url()` from `agentic_tools`
2. **Discord Integration**: Uses `create_scheduled_event()` tool
3. **Notion Integration**: Uses `_client_helper` functions
4. **Logging**: Uses Logfire for observability
5. **Error Handling**: Follows existing error handling patterns

## Testing

### Test Script

Run the interactive test script:
```bash
python test_bluescal_sync.py
```

This will:
1. Check environment variables
2. Run a dry-run test
3. Show results
4. Prompt for actual sync

### Manual Testing

```python
# Dry run test
result = await sync_bluescal_events_to_discord(
    dry_run=True,
    max_events=5,
)

# Check results
assert result['total_events_found'] > 0
assert result['new_events'] >= 0
assert result['duplicates_skipped'] >= 0
```

## Next Steps

1. **Set up Notion database** with required properties
2. **Configure environment variables**
3. **Test with dry run**: `python test_bluescal_sync.py`
4. **Run actual sync** once confident
5. **Schedule regular runs** (daily/weekly)

## Future Enhancements

- [ ] Filter events by date range
- [ ] Filter events by location
- [ ] Filter events by dance style
- [ ] Automatic event updates
- [ ] Support multiple Discord servers
- [ ] Event cancellation detection
- [ ] Webhook notifications

## Related Documentation

- `docs/BLUESCAL_WORKFLOW.md` - Full workflow documentation
- `EVENT_AGENT_SUPABASE_SUMMARY.md` - Related event extraction workflow
- `docs/TUMBLR_FEED_WORKFLOW.md` - Similar feed workflow pattern

