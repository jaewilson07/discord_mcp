# BluesCal.com to Discord Event Sync Workflow

## Overview

This workflow automatically extracts events from [BluesCal.com](https://bluescal.com/) and syncs them to Discord scheduled events, using Notion as a database to track events and prevent duplicates.

## Features

- ✅ **Multi-event extraction**: Extracts all events from BluesCal.com calendar
- ✅ **Duplicate prevention**: Checks Notion database before creating Discord events
- ✅ **Automatic tracking**: Saves all events to Notion for future reference
- ✅ **Dry run mode**: Test the workflow without creating events
- ✅ **Error handling**: Graceful error handling with detailed reporting
- ✅ **Logfire instrumentation**: Full observability with Logfire

## Workflow Steps

1. **Extract Events**: Scrapes BluesCal.com and extracts all events using AI
2. **Check Duplicates**: Queries Notion database to find existing events
3. **Create Discord Events**: Creates Discord scheduled events for new events only
4. **Save to Notion**: Saves all events to Notion for tracking and future duplicate checks

## Setup

### 1. Environment Variables

Set the following environment variables:

```bash
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id

# Optional
DISCORD_SERVER_ID=your_discord_server_id  # Auto-detected if not set
OPENAI_API_KEY=your_openai_key  # For event extraction
LOGFIRE_TOKEN=your_logfire_token  # For observability
```

### 2. Notion Database Setup

Create a Notion database with the following properties:

#### Required Properties

| Property Name   | Type  | Description                                       |
| --------------- | ----- | ------------------------------------------------- |
| **Name**        | Title | Event title (used for duplicate checking)         |
| **URL**         | URL   | Event URL (optional, used for duplicate checking) |
| **Date**        | Date  | Event date (used for duplicate checking)          |
| **Scrape Date** | Date  | When the event was scraped                        |

#### Recommended Properties

| Property Name         | Type   | Description                                   |
| --------------------- | ------ | --------------------------------------------- |
| **Location**          | Text   | Event location                                |
| **Source**            | Select | Source of event (e.g., "BluesCal.com")        |
| **Discord Event ID**  | Text   | Discord event ID (if created)                 |
| **Discord Event URL** | URL    | Discord event URL (if created)                |
| **Status**            | Select | Event status (e.g., "New", "Synced", "Error") |

#### Example Notion Database Schema

```
┌─────────────────────────────────────────────────────────────┐
│ BluesCal Events Database                                     │
├─────────────────────────────────────────────────────────────┤
│ Name (Title) │ Date │ Location │ Source │ Discord Event URL │
├─────────────────────────────────────────────────────────────┤
│ Guadalajara  │ Nov  │ Guadalaj│ BluesC│ https://discord... │
│ Lindy Exch.  │ 7    │ ara, MX │ al.com│                    │
└─────────────────────────────────────────────────────────────┘
```

### 3. Notion Integration Setup

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create a new integration
3. Copy the integration token
4. Share your database with the integration:
   - Open your database
   - Click "..." → "Add connections"
   - Select your integration

## Usage

### Basic Usage

```python
from mcp_ce.agentic_tools.events.sync_bluescal_events import (
    sync_bluescal_events_to_discord
)

# Sync all events from BluesCal.com
result = await sync_bluescal_events_to_discord()

if result['success']:
    print(f"✅ Synced {result['discord_events_created']} new events")
    print(f"   Skipped {result['duplicates_skipped']} duplicates")
else:
    print(f"❌ Errors: {result['errors']}")
```

### Advanced Usage

```python
# Custom configuration
result = await sync_bluescal_events_to_discord(
    bluescal_url="https://bluescal.com/",
    discord_server_id="your_server_id",
    notion_database_id="your_database_id",
    dry_run=False,  # Set to True to test without creating events
    max_events=10,  # Limit number of events to process
    quality_threshold=0.7,  # Minimum quality score for extraction
)

# Check results
print(f"Total events found: {result['total_events_found']}")
print(f"New events: {result['new_events']}")
print(f"Duplicates skipped: {result['duplicates_skipped']}")
print(f"Discord events created: {result['discord_events_created']}")
print(f"Notion pages created: {result['notion_pages_created']}")

# View event details
for event in result['events']:
    print(f"  - {event['title']} ({event['date']})")
    if 'discord_event_url' in event:
        print(f"    Discord: {event['discord_event_url']}")
    if 'notion_page_url' in event:
        print(f"    Notion: {event['notion_page_url']}")
```

### Dry Run Mode

Test the workflow without creating events:

```python
result = await sync_bluescal_events_to_discord(
    dry_run=True,
    max_events=5,  # Test with first 5 events
)

# This will show what would be created without actually creating
print(f"Would create {result['new_events']} Discord events")
print(f"Would save {result['total_events_found']} events to Notion")
```

## Duplicate Detection

The workflow uses multiple strategies to detect duplicates:

1. **Title + Date Match**: If an event with the same title and date exists in Notion
2. **URL Match**: If an event with the same URL exists in Notion

### How It Works

```python
# For each extracted event:
1. Query Notion database
2. Check if event title matches (case-insensitive)
3. Check if event date matches
4. Check if event URL matches (if available)
5. If any match found → Skip (duplicate)
6. If no match → New event (create Discord event)
```

### Improving Duplicate Detection

For better duplicate detection, you can:

1. **Add a formula property** in Notion that combines title + date
2. **Use a unique identifier** field (e.g., event ID from BluesCal)
3. **Normalize event titles** before comparison (remove extra spaces, special chars)

## Event Extraction

The workflow uses the `extract_events_from_url` function which:

- Scrapes the BluesCal.com page
- Uses AI to extract structured event details
- Returns multiple events with quality scores
- Handles calendar views, list views, and event cards

### Event Details Extracted

- Title
- Date and time
- Location (name, address, city, state, country)
- Description
- Organizer
- Price
- URL
- Category/Tags

## Error Handling

The workflow handles errors gracefully:

- **Scraping failures**: Logs error, continues if possible
- **Notion failures**: Logs warning, continues workflow
- **Discord failures**: Logs error, continues with other events
- **Extraction failures**: Returns partial results

All errors are collected in `result['errors']` for review.

## Monitoring

### Logfire Traces

View detailed execution traces at [Logfire Dashboard](https://logfire.pydantic.dev/):

- Event extraction quality scores
- Duplicate check results
- Discord event creation status
- Notion save operations
- Error details

### Console Output

The workflow provides detailed console output:

```
🎵 Step 1: Starting BluesCal.com event sync...
   URL: https://bluescal.com/
   Dry run: False

📅 Step 2: Extracting events from BluesCal.com...
✅ Found 15 events

🔍 Step 3: Checking for duplicates in Notion...
   ✨ New event: Guadalajara Lindy Exchange (11/7/2025)
   ⏭️  Skipping duplicate: Hop that Swing Rostock (11/7/2025)
   ✨ New event: N/evermore '25 (11/6/2025)

📢 Step 4: Creating Discord events...
   ✅ Created Discord event: Guadalajara Lindy Exchange
   ✅ Created Discord event: N/evermore '25

💾 Step 5: Saving events to Notion...
   ✅ Saved to Notion: Guadalajara Lindy Exchange
   ✅ Saved to Notion: N/evermore '25

📊 Summary:
   Total events found: 15
   New events: 2
   Duplicates skipped: 13
   Discord events created: 2
   Notion pages created: 15
   Errors: 0
```

## Scheduling

You can schedule this workflow to run automatically:

### Using Cron (Linux/Mac)

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/project && python -m mcp_ce.agentic_tools.events.sync_bluescal_events
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 9:00 AM)
4. Set action: Start a program
5. Program: `python`
6. Arguments: `-m mcp_ce.agentic_tools.events.sync_bluescal_events`

### Using GitHub Actions

```yaml
name: Sync BluesCal Events

on:
  schedule:
    - cron: "0 9 * * *" # Daily at 9 AM UTC
  workflow_dispatch: # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -e .
      - run: python -m mcp_ce.agentic_tools.events.sync_bluescal_events
        env:
          DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
```

## Troubleshooting

### No Events Found

- Check if BluesCal.com is accessible
- Verify the URL is correct
- Check extraction quality threshold (may be too high)
- Review Logfire traces for extraction issues

### Duplicates Not Detected

- Verify Notion database has correct properties (Name, Date, URL)
- Check that events are being saved to Notion
- Review duplicate detection logic in code
- Consider adding formula property for better matching

### Discord Events Not Created

- Verify Discord bot token is valid
- Check bot has permissions to create scheduled events
- Verify server ID is correct
- Check Discord API rate limits

### Notion Save Failures

- Verify Notion token is valid
- Check database is shared with integration
- Verify database properties match expected schema
- Check Notion API rate limits

## Best Practices

1. **Start with dry run**: Test the workflow with `dry_run=True` first
2. **Limit events initially**: Use `max_events=5` to test with a small batch
3. **Monitor Logfire**: Watch for extraction quality issues
4. **Review Notion database**: Check that events are being saved correctly
5. **Schedule regularly**: Run daily or weekly to catch new events
6. **Handle errors**: Review `result['errors']` after each run

## Related Files

- `src/mcp_ce/agentic_tools/events/sync_bluescal_events.py` - Main workflow
- `src/mcp_ce/agentic_tools/graphs/extract_event/extract_event.py` - Event extraction
- `src/mcp_ce/models/events.py` - EventDetails model
- `src/mcp_ce/tools/notion/` - Notion integration tools
- `src/mcp_ce/tools/discord/` - Discord integration tools

## Future Enhancements

- [ ] Support for filtering events by date range
- [ ] Support for filtering events by location
- [ ] Support for filtering events by dance style
- [ ] Automatic event updates (if event details change)
- [ ] Support for multiple Discord servers
- [ ] Support for event reminders
- [ ] Webhook notifications for new events
- [ ] Event cancellation detection
