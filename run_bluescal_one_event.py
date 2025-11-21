"""Run BluesCal sync workflow to create one Discord event."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import directly to avoid __init__ issues
from mcp_ce.agentic_tools.graphs.extract_event.extract_event import extract_events_from_url
from mcp_ce.tools.discord.create_scheduled_event import create_scheduled_event
from mcp_ce.tools.discord.list_servers import list_servers
from mcp_ce.tools.discord._bot_helper import is_bot_ready
from mcp_ce.models.events import EventDetails
from mcp_ce.tools.notion._client_helper import (
    get_data_source_id_from_database,
    query_data_source,
    create_page,
)
from datetime import datetime
import asyncio


async def create_one_discord_event():
    """Create one Discord event from BluesCal.com."""
    print("=" * 60)
    print("BluesCal.com Event Sync - Creating 1 Discord Event")
    print("=" * 60)

    # Step 1: Extract events
    print("\n📅 Step 1: Extracting events from BluesCal.com...")
    extraction_result = await extract_events_from_url(
        url="https://bluescal.com/",
        max_iterations=2,
        confidence_threshold=0.7,
    )

    events = extraction_result.events
    if not events:
        print("❌ No events found")
        return

    print(f"✅ Found {len(events)} events")
    
    # Take the first event
    event = events[0]
    print(f"\n📅 Selected event: {event.title} ({event.date})")

    # Step 2: Get Discord server
    print("\n📢 Step 2: Getting Discord server...")
    discord_server_id = os.getenv("DISCORD_SERVER_ID")
    if not discord_server_id and is_bot_ready():
        servers_result = await list_servers()
        if servers_result.is_success and servers_result.result:
            servers = servers_result.result.servers
            if servers:
                discord_server_id = servers[0]["id"]
                print(f"   Using server: {servers[0]['name']}")

    if not discord_server_id:
        print("❌ No Discord server ID available")
        return

    # Step 3: Create Discord event
    print("\n📢 Step 3: Creating Discord event...")
    
    # Parse datetime
    start_dt, end_dt = event.convert_datetime_for_discord()
    if not start_dt:
        print("❌ Could not parse event date/time")
        return

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
        desc = event.description[:900] if len(event.description) > 900 else event.description
        description_parts.append(desc)
    if event.url:
        description_parts.append(f"More info: {event.url}")

    description = "\n\n".join(description_parts) if description_parts else None

    # Create Discord event
    discord_result = await create_scheduled_event(
        server_id=discord_server_id,
        name=event.title[:100],
        start_time=start_dt.isoformat(),
        end_time=end_dt.isoformat() if end_dt else None,
        description=description,
        entity_type="external",
        location=location,
    )

    if discord_result.is_success and discord_result.result:
        print(f"✅ Discord event created!")
        print(f"   Event URL: {discord_result.result.url}")
        print(f"   Event ID: {discord_result.result.event_id}")
        return {
            "success": True,
            "event_title": event.title,
            "event_date": event.date,
            "discord_event_url": discord_result.result.url,
            "discord_event_id": discord_result.result.event_id,
        }
    else:
        print(f"❌ Failed to create Discord event: {discord_result.error}")
        return {
            "success": False,
            "error": discord_result.error or "Unknown error",
        }


async def main():
    """Run the workflow to create one Discord event."""
    result = await create_one_discord_event()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    if result["success"]:
        print(f"✅ Successfully created Discord event!")
        print(f"   Title: {result['event_title']}")
        print(f"   Date: {result['event_date']}")
        print(f"   Discord URL: {result['discord_event_url']}")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")



if __name__ == "__main__":
    asyncio.run(main())

