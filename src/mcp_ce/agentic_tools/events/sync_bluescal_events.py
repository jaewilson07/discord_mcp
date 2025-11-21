"""
Workflow to sync events from BluesCal.com to Discord with Notion duplicate tracking.

This workflow:
1. Scrapes bluescal.com to extract all events
2. Checks Notion database for duplicates (by event title + date)
3. Creates Discord events for new events
4. Saves all events to Notion to track them and prevent future duplicates

Usage:
    result = await sync_bluescal_events_to_discord(
        discord_server_id="your_server_id",
        notion_database_id="your_database_id",
        dry_run=False
    )
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import logfire

from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
from mcp_ce.tools.discord.create_scheduled_event import create_scheduled_event
from mcp_ce.tools.discord.list_servers import list_servers
from mcp_ce.tools.discord._bot_helper import is_bot_ready
from mcp_ce.agentic_tools import (
    extract_events_from_url,
    EventExtractionWorkflowResult,
    EventDetails,
)
from mcp_ce.tools.notion._client_helper import (
    get_data_source_id_from_database,
    query_data_source,
    create_page,
)
from mcp_ce.tools.notion.query_database import query_notion_database


@logfire.instrument()
async def sync_bluescal_events_to_discord(
    bluescal_url: str = "https://bluescal.com/",
    discord_server_id: Optional[str] = None,
    notion_database_id: Optional[str] = None,
    dry_run: bool = False,
    max_events: Optional[int] = None,
    quality_threshold: float = 0.7,
) -> Dict[str, Any]:
    """
    Sync events from BluesCal.com to Discord with Notion duplicate tracking.

    Args:
        bluescal_url: URL to BluesCal.com (default: "https://bluescal.com/")
        discord_server_id: Discord server ID (uses first available if not provided)
        notion_database_id: Notion database ID (uses NOTION_DATABASE_ID env var if not provided)
        dry_run: If True, don't create Discord events or save to Notion (default: False)
        max_events: Maximum number of events to process (None for all)
        quality_threshold: Minimum quality score for event extraction (default: 0.7)

    Returns:
        Dict containing:
        - success: bool indicating if workflow succeeded
        - total_events_found: int - Total events extracted from BluesCal
        - new_events: int - Number of new events (not in Notion)
        - duplicates_skipped: int - Number of events already in Notion
        - discord_events_created: int - Number of Discord events created
        - notion_pages_created: int - Number of Notion pages created
        - events: List[Dict] - Details of all processed events
        - errors: List[str] - Any errors encountered
    """
    errors = []
    result = {
        "success": False,
        "total_events_found": 0,
        "new_events": 0,
        "duplicates_skipped": 0,
        "discord_events_created": 0,
        "notion_pages_created": 0,
        "events": [],
        "errors": errors,
    }

    try:
        # Step 1: Get configuration
        logfire.info("Starting BluesCal sync workflow", url=bluescal_url, dry_run=dry_run)
        print(f"\n🎵 Step 1: Starting BluesCal.com event sync...")
        print(f"   URL: {bluescal_url}")
        print(f"   Dry run: {dry_run}")

        # Get Discord server ID
        if not discord_server_id:
            discord_server_id = os.getenv("DISCORD_SERVER_ID")
            if not discord_server_id and is_bot_ready():
                servers_result = await list_servers()
                if servers_result.is_success and servers_result.result:
                    servers = servers_result.result.servers
                    if servers:
                        discord_server_id = servers[0]["id"]
                        print(f"   Using Discord server: {servers[0]['name']}")

        # Get Notion database ID
        if not notion_database_id:
            notion_database_id = os.getenv("NOTION_DATABASE_ID")
            if not notion_database_id:
                errors.append("NOTION_DATABASE_ID not configured")
                logfire.warn("Notion database ID not configured")

        # Step 2: Extract events from BluesCal.com
        logfire.info("Extracting events from BluesCal", url=bluescal_url)
        print(f"\n📅 Step 2: Extracting events from BluesCal.com...")

        extraction_result: EventExtractionWorkflowResult = (
            await extract_events_from_url(
                url=bluescal_url,
                max_iterations=2,
                confidence_threshold=quality_threshold,
            )
        )

        events = extraction_result.events
        result["total_events_found"] = len(events)

        if not events:
            errors.append("No events found on BluesCal.com")
            logfire.warn("No events extracted from BluesCal")
            return result

        print(f"✅ Found {len(events)} events")

        # Limit events if max_events specified
        if max_events and len(events) > max_events:
            events = events[:max_events]
            print(f"   Processing first {max_events} events")

        # Step 3: Check for duplicates in Notion
        print(f"\n🔍 Step 3: Checking for duplicates in Notion...")
        new_events = []
        duplicate_events = []

        if notion_database_id:
            for event in events:
                is_duplicate = await _check_event_duplicate_in_notion(
                    event, notion_database_id
                )
                if is_duplicate:
                    duplicate_events.append(event)
                    print(f"   ⏭️  Skipping duplicate: {event.title} ({event.date})")
                else:
                    new_events.append(event)
                    print(f"   ✨ New event: {event.title} ({event.date})")

            result["new_events"] = len(new_events)
            result["duplicates_skipped"] = len(duplicate_events)
        else:
            # If Notion not configured, treat all as new
            new_events = events
            result["new_events"] = len(new_events)
            print(f"   ⚠️  Notion not configured - treating all events as new")

        # Step 4: Create Discord events for new events
        if not dry_run and new_events and discord_server_id:
            print(f"\n📢 Step 4: Creating Discord events...")
            logfire.info("Creating Discord events", count=len(new_events))

            for event in new_events:
                try:
                    discord_result = await _create_discord_event(
                        event, discord_server_id
                    )
                    if discord_result["success"]:
                        result["discord_events_created"] += 1
                        event_data = {
                            "title": event.title,
                            "date": event.date,
                            "discord_event_id": discord_result.get("event_id"),
                            "discord_event_url": discord_result.get("event_url"),
                        }
                        result["events"].append(event_data)
                        print(f"   ✅ Created Discord event: {event.title}")
                    else:
                        errors.append(
                            f"Failed to create Discord event for {event.title}: {discord_result.get('error')}"
                        )
                        logfire.warn(
                            "Discord event creation failed",
                            event_title=event.title,
                            error=discord_result.get("error"),
                        )
                except Exception as e:
                    error_msg = f"Error creating Discord event for {event.title}: {str(e)}"
                    errors.append(error_msg)
                    logfire.error("Discord event creation exception", error=str(e))
        elif dry_run:
            print(f"   🔍 Dry run: Would create {len(new_events)} Discord events")
        elif not discord_server_id:
            errors.append("Discord server ID not available")
            print(f"   ⚠️  Discord server ID not available")

        # Step 5: Save events to Notion
        if not dry_run and notion_database_id:
            print(f"\n💾 Step 5: Saving events to Notion...")
            logfire.info("Saving events to Notion", count=len(events))

            for event in events:
                try:
                    notion_result = await _save_event_to_notion(event, notion_database_id)
                    if notion_result["success"]:
                        result["notion_pages_created"] += 1
                        # Update event data with Notion info
                        for event_data in result["events"]:
                            if event_data["title"] == event.title:
                                event_data["notion_page_id"] = notion_result.get("page_id")
                                event_data["notion_page_url"] = notion_result.get("page_url")
                                break
                        else:
                            # Event not in result["events"] yet (duplicate that we're still saving)
                            result["events"].append(
                                {
                                    "title": event.title,
                                    "date": event.date,
                                    "notion_page_id": notion_result.get("page_id"),
                                    "notion_page_url": notion_result.get("page_url"),
                                }
                            )
                        print(f"   ✅ Saved to Notion: {event.title}")
                    else:
                        errors.append(
                            f"Failed to save {event.title} to Notion: {notion_result.get('error')}"
                        )
                        logfire.warn(
                            "Notion save failed",
                            event_title=event.title,
                            error=notion_result.get("error"),
                        )
                except Exception as e:
                    error_msg = f"Error saving {event.title} to Notion: {str(e)}"
                    errors.append(error_msg)
                    logfire.error("Notion save exception", error=str(e))
        elif dry_run:
            print(f"   🔍 Dry run: Would save {len(events)} events to Notion")
        elif not notion_database_id:
            print(f"   ⚠️  Notion database ID not available")

        # Determine overall success
        result["success"] = (
            result["total_events_found"] > 0
            and (result["discord_events_created"] > 0 or dry_run)
            and len([e for e in errors if "critical" in e.lower()]) == 0
        )

        print(f"\n📊 Summary:")
        print(f"   Total events found: {result['total_events_found']}")
        print(f"   New events: {result['new_events']}")
        print(f"   Duplicates skipped: {result['duplicates_skipped']}")
        if not dry_run:
            print(f"   Discord events created: {result['discord_events_created']}")
            print(f"   Notion pages created: {result['notion_pages_created']}")
        print(f"   Errors: {len(errors)}")

        logfire.info(
            "BluesCal sync complete",
            success=result["success"],
            total_events=result["total_events_found"],
            new_events=result["new_events"],
            discord_created=result["discord_events_created"],
            notion_created=result["notion_pages_created"],
            errors=len(errors),
        )

        return result

    except Exception as e:
        error_msg = f"Workflow failed: {str(e)}"
        errors.append(error_msg)
        logfire.error("BluesCal sync workflow exception", error=str(e), exc_info=True)
        return result


async def _check_event_duplicate_in_notion(
    event: EventDetails, notion_database_id: str
) -> bool:
    """
    Check if an event already exists in Notion database.

    Checks by:
    1. Event title + date combination
    2. Event URL (if available)

    Args:
        event: EventDetails object to check
        notion_database_id: Notion database ID

    Returns:
        True if duplicate found, False otherwise
    """
    try:
        # Get data source ID
        data_source_id = await get_data_source_id_from_database(notion_database_id)

        # Build search query - check by title
        # Note: Notion filters are limited, so we'll query and check in Python
        # For better performance, we could use a formula property in Notion
        result = await query_data_source(data_source_id, filter_obj=None)

        pages = result.get("results", [])
        if not pages:
            return False

        # Check each page for duplicate
        for page in pages:
            properties = page.get("properties", {})

            # Check title
            title_match = False
            if "Name" in properties or "Title" in properties:
                title_prop = properties.get("Name") or properties.get("Title")
                if title_prop and title_prop.get("type") == "title":
                    title_text = title_prop.get("title", [])
                    if title_text:
                        page_title = title_text[0].get("text", {}).get("content", "")
                        if page_title.lower() == event.title.lower():
                            title_match = True

            # Check date
            date_match = False
            if "Date" in properties or "Event Date" in properties:
                date_prop = properties.get("Date") or properties.get("Event Date")
                if date_prop and date_prop.get("type") == "date":
                    date_value = date_prop.get("date")
                    if date_value:
                        page_date = date_value.get("start", "")
                        # Simple date comparison (could be improved)
                        if event.date and event.date in page_date:
                            date_match = True

            # Check URL
            url_match = False
            if event.url and "URL" in properties:
                url_prop = properties.get("URL")
                if url_prop and url_prop.get("type") == "url":
                    page_url = url_prop.get("url", "")
                    if page_url == event.url:
                        url_match = True

            # If title + date match, or URL matches, it's a duplicate
            if (title_match and date_match) or url_match:
                return True

        return False

    except Exception as e:
        logfire.warn("Error checking duplicate in Notion", error=str(e))
        # On error, assume not duplicate to avoid skipping events
        return False


async def _create_discord_event(
    event: EventDetails, discord_server_id: str
) -> Dict[str, Any]:
    """
    Create a Discord scheduled event from EventDetails.

    Args:
        event: EventDetails object
        discord_server_id: Discord server ID

    Returns:
        Dict with success status, event_id, and event_url
    """
    try:
        # Parse datetime for Discord
        start_dt, end_dt = event.convert_datetime_for_discord()

        if not start_dt:
            return {
                "success": False,
                "error": "Could not parse event date/time for Discord",
            }

        # Prepare event details
        location = event.get_full_location() or "See event details"
        if len(location) > 100:
            location = location[:97] + "..."

        description_parts = []
        if event.organizer:
            description_parts.append(f"Host: {event.organizer}")
        if event.price:
            description_parts.append(f"Price: {event.price}")
        if event.description:
            desc = (
                event.description[:900]
                if len(event.description) > 900
                else event.description
            )
            description_parts.append(desc)
        if event.url:
            description_parts.append(f"More info: {event.url}")

        description = "\n\n".join(description_parts) if description_parts else None

        # Format datetime for Discord API (ISO 8601)
        start_time_iso = start_dt.isoformat()
        end_time_iso = end_dt.isoformat() if end_dt else None

        # Create Discord event
        discord_result = await create_scheduled_event(
            server_id=discord_server_id,
            name=event.title[:100],  # Discord limit is 100 chars
            start_time=start_time_iso,
            end_time=end_time_iso,
            description=description,
            entity_type="external",
            location=location,
        )

        if discord_result.is_success and discord_result.result:
            return {
                "success": True,
                "event_id": discord_result.result.event_id,
                "event_url": discord_result.result.url,
            }
        else:
            return {
                "success": False,
                "error": discord_result.error or "Unknown error",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def _save_event_to_notion(
    event: EventDetails, notion_database_id: str
) -> Dict[str, Any]:
    """
    Save an event to Notion database.

    Args:
        event: EventDetails object
        notion_database_id: Notion database ID

    Returns:
        Dict with success status, page_id, and page_url
    """
    try:
        from notion_blockify import Blockizer

        # Prepare content for Notion
        content_parts = []
        if event.description:
            content_parts.append(f"## Description\n\n{event.description}")
        if event.organizer:
            content_parts.append(f"## Organizer\n\n{event.organizer}")
        if event.price:
            content_parts.append(f"## Price\n\n{event.price}")
        if event.get_full_location():
            content_parts.append(f"## Location\n\n{event.get_full_location()}")

        content_markdown = "\n\n".join(content_parts) if content_parts else ""

        # Convert markdown to blocks
        blockizer = Blockizer()
        blocks = blockizer.convert(content_markdown) if content_markdown else []

        # Prepare properties
        properties = {
            "Name": {
                "title": [{"text": {"content": event.title[:100]}}]
            },
        }

        # Add URL if available
        if event.url:
            properties["URL"] = {"url": event.url}

        # Add date if available
        if event.date:
            # Try to parse date for Notion date property
            try:
                # Simple date parsing - could be improved
                date_str = event.date
                # Notion expects ISO format or date string
                properties["Date"] = {"date": {"start": date_str}}
            except:
                pass

        # Add location as text
        if event.get_full_location():
            properties["Location"] = {
                "rich_text": [{"text": {"content": event.get_full_location()[:2000]}}]
            }

        # Add source
        properties["Source"] = {
            "select": {"name": "BluesCal.com"}
        }

        # Add scrape date
        properties["Scrape Date"] = {
            "date": {"start": datetime.now().isoformat()}
        }

        # Create page in database
        created_page = await create_page(
            parent_database_id=notion_database_id,
            properties=properties,
            children=blocks[:100] if blocks else None,  # Notion limit is 100 blocks per request
        )

        page_id = created_page.get("id", "")
        page_url = created_page.get("url", "")

        # Append remaining blocks if any
        if len(blocks) > 100:
            from mcp_ce.tools.notion._client_helper import append_blocks
            for i in range(100, len(blocks), 100):
                chunk = blocks[i : i + 100]
                await append_blocks(page_id, chunk)

        return {
            "success": True,
            "page_id": page_id,
            "page_url": page_url,
        }

    except Exception as e:
        logfire.error("Error saving event to Notion", error=str(e))
        return {"success": False, "error": str(e)}


# Test function
if __name__ == "__main__":
    import asyncio

    async def test():
        result = await sync_bluescal_events_to_discord(
            dry_run=True,  # Test without creating events
            max_events=5,  # Limit to 5 events for testing
        )

        print(f"\n📊 Test Result:")
        print(f"  Success: {result['success']}")
        print(f"  Total events found: {result['total_events_found']}")
        print(f"  New events: {result['new_events']}")
        print(f"  Duplicates skipped: {result['duplicates_skipped']}")
        if result["errors"]:
            print(f"  Errors: {result['errors']}")

    asyncio.run(test())

