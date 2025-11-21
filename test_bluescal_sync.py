"""
Test script for BluesCal.com event sync workflow.

This script demonstrates how to use the sync_bluescal_events_to_discord workflow.

Usage:
    python test_bluescal_sync.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from mcp_ce.agentic_tools.events.sync_bluescal_events import (
    sync_bluescal_events_to_discord,
)


async def main():
    """Test the BluesCal sync workflow."""
    print("=" * 60)
    print("BluesCal.com Event Sync Test")
    print("=" * 60)

    # Check environment variables
    required_vars = ["DISCORD_BOT_TOKEN", "NOTION_TOKEN", "NOTION_DATABASE_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file or environment")
        return

    print("\n✅ Environment variables configured")

    # Run sync with dry run first
    print("\n" + "=" * 60)
    print("DRY RUN - Testing without creating events")
    print("=" * 60)

    result = await sync_bluescal_events_to_discord(
        dry_run=True,
        max_events=5,  # Limit to 5 events for testing
    )

    print("\n" + "=" * 60)
    print("DRY RUN RESULTS")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Total events found: {result['total_events_found']}")
    print(f"New events: {result['new_events']}")
    print(f"Duplicates skipped: {result['duplicates_skipped']}")
    print(f"Errors: {len(result['errors'])}")

    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")

    if result["events"]:
        print("\nEvents found:")
        for event in result["events"][:5]:  # Show first 5
            print(
                f"  - {event.get('title', 'Unknown')} ({event.get('date', 'No date')})"
            )

    # Ask user if they want to proceed with actual sync
    print("\n" + "=" * 60)
    response = input("Proceed with actual sync? (yes/no): ").strip().lower()

    if response == "yes":
        print("\n" + "=" * 60)
        print("ACTUAL SYNC - Creating Discord events and saving to Notion")
        print("=" * 60)

        result = await sync_bluescal_events_to_discord(
            dry_run=False,
            max_events=10,  # Limit to 10 events for initial sync
        )

        print("\n" + "=" * 60)
        print("SYNC RESULTS")
        print("=" * 60)
        print(f"Success: {result['success']}")
        print(f"Total events found: {result['total_events_found']}")
        print(f"New events: {result['new_events']}")
        print(f"Duplicates skipped: {result['duplicates_skipped']}")
        print(f"Discord events created: {result['discord_events_created']}")
        print(f"Notion pages created: {result['notion_pages_created']}")
        print(f"Errors: {len(result['errors'])}")

        if result["events"]:
            print("\nCreated events:")
            for event in result["events"]:
                print(f"\n  📅 {event.get('title', 'Unknown')}")
                print(f"     Date: {event.get('date', 'No date')}")
                if "discord_event_url" in event:
                    print(f"     Discord: {event['discord_event_url']}")
                if "notion_page_url" in event:
                    print(f"     Notion: {event['notion_page_url']}")

        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")
    else:
        print("\nSkipping actual sync. Run again when ready!")


if __name__ == "__main__":
    asyncio.run(main())
