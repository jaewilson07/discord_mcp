"""Run BluesCal sync workflow to create one Discord event - minimal version."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Import only what we need, avoiding problematic imports
from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
from mcp_ce.tools.discord.create_scheduled_event import create_scheduled_event
from mcp_ce.tools.discord.list_servers import list_servers
from mcp_ce.tools.discord._bot_helper import is_bot_ready

# Import extract_event_details directly
import sys
import importlib.util
spec = importlib.util.spec_from_file_location(
    "extract_structured_data",
    os.path.join(os.path.dirname(__file__), "src", "mcp_ce", "agentic_tools", "graphs", "extract_strucured_data", "extract_structured_data.py")
)
extract_module = importlib.util.module_from_spec(spec)
sys.modules["_extract_structured_data_direct"] = extract_module
spec.loader.exec_module(extract_module)
extract_event_details = extract_module.extract_event_details


async def create_one_discord_event():
    """Create one Discord event from BluesCal.com."""
    print("=" * 60)
    print("BluesCal.com Event Sync - Creating 1 Discord Event")
    print("=" * 60)

    # Step 1: Scrape BluesCal.com
    print("\n📅 Step 1: Scraping BluesCal.com...")
    scrape_result = await crawl_website(
        url="https://bluescal.com/",
        extract_images=False,
        extract_links=False,
        word_count_threshold=5,
        headless=True,
    )

    if not scrape_result.is_success:
        print(f"❌ Scraping failed: {scrape_result.error or 'Unknown error'}")
        return {"success": False, "error": "Scraping failed"}

    result_dict = scrape_result.result if scrape_result.result else {}
    content_markdown = result_dict.get("content_markdown", "")
    print(f"✅ Scraped {len(content_markdown)} characters")

    # Step 2: Extract event details
    print("\n🤖 Step 2: Extracting event details...")
    event = await extract_event_details(
        text=content_markdown,
        url="https://bluescal.com/",
    )

    print(f"✅ Extracted event: {event.title}")
    if event.date:
        print(f"   Date: {event.date}")
    if event.start_time:
        print(f"   Time: {event.start_time}")

    # Step 3: Get Discord server
    print("\n📢 Step 3: Getting Discord server...")
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
        return {"success": False, "error": "No Discord server ID"}

    # Step 4: Create Discord event
    print("\n📢 Step 4: Creating Discord event...")
    
    # Parse datetime
    start_dt, end_dt = event.convert_datetime_for_discord()
    if not start_dt:
        print("❌ Could not parse event date/time")
        return {"success": False, "error": "Could not parse date/time"}

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
            "event_time": event.start_time,
            "location": location,
            "discord_event_url": discord_result.result.url,
            "discord_event_id": discord_result.result.event_id,
        }
    else:
        error_msg = discord_result.error or "Unknown error"
        print(f"❌ Failed to create Discord event: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
        }


async def main():
    """Run the workflow to create one Discord event."""
    result = await create_one_discord_event()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    if result.get("success"):
        print(f"✅ Successfully created Discord event!")
        print(f"\n📅 Event Details:")
        print(f"   Title: {result['event_title']}")
        print(f"   Date: {result.get('event_date', 'N/A')}")
        print(f"   Time: {result.get('event_time', 'N/A')}")
        print(f"   Location: {result.get('location', 'N/A')}")
        print(f"\n🔗 Discord Event:")
        print(f"   URL: {result['discord_event_url']}")
        print(f"   ID: {result['discord_event_id']}")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())

