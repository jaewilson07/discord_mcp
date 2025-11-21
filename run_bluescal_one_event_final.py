"""Run BluesCal sync workflow to create one Discord event using existing working function."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Use the existing working function
from mcp_ce.agentic_tools.events.create_from_url_supabase import (
    create_event_from_url_with_supabase,
)


async def main():
    """Run the workflow to create one Discord event."""
    print("=" * 60)
    print("BluesCal.com Event Sync - Creating 1 Discord Event")
    print("=" * 60)

    # Use the existing working function
    # This will scrape, extract, and create a Discord event
    result = await create_event_from_url_with_supabase(
        url="https://bluescal.com/",
        save_to_supabase=False,  # Skip Supabase for this test
        quality_threshold=0.7,
        max_iterations=3,
    )

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if result["success"]:
        print(f"✅ Successfully created Discord event!")
        if result.get("event"):
            event = result["event"]
            print(f"\n📅 Event Details:")
            print(f"   Title: {event.title}")
            print(f"   Date: {event.date or 'N/A'}")
            print(f"   Time: {event.start_time or 'N/A'}")
            if event.get_full_location():
                print(f"   Location: {event.get_full_location()}")
        
        if result.get("discord_event_url"):
            print(f"\n🔗 Discord Event:")
            print(f"   URL: {result['discord_event_url']}")
            print(f"   ID: {result.get('discord_event_id', 'N/A')}")
        
        if result.get("quality_score"):
            qs = result["quality_score"]
            print(f"\n📊 Quality Score: {qs.get('overall', 0):.2f}")
    else:
        print(f"❌ Failed to create event")
        if result.get("errors"):
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())

