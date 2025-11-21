"""
Test script for create_discord_event_from_url workflow with Blues Muse event.

This tests the full workflow:
1. Scrape https://www.bluesmuse.dance/
2. Extract event (should detect insufficient info)
3. Trigger deep crawl (multi-page)
4. Re-extract with combined content
5. Create Discord event

Uses the existing create_from_url_supabase pattern which already works.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Use the working create_from_url_supabase as a reference, but we'll test our new workflow
# For now, let's use the existing working function to verify the test setup works
from mcp_ce.agentic_tools.events.create_from_url_supabase import create_event_from_url_with_supabase


async def test_bluesmuse_event():
    """Test the workflow with Blues Muse event URL."""
    
    url = "https://www.bluesmuse.dance/"
    
    print("=" * 70)
    print("Testing: Create Discord Event from URL")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"Expected: Event for October 16-18, 2026 in Philadelphia, PA")
    print("=" * 70)
    print()
    
    # For testing, use the existing working function first to verify setup
    # Then we can test the new graph workflow
    print("Note: Using create_from_url_supabase for initial test")
    print("The new graph workflow (create_discord_event_from_url) will be tested next\n")
    
    result = await create_event_from_url_with_supabase(
        url=url,
        discord_server_id=None,  # Will use first available server
        save_to_supabase=False,  # Skip Supabase for this test
        quality_threshold=0.7,
        max_iterations=3,
    )
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print()
    
    if result["event"]:
        event = result["event"]
        print(f"Event Title: {event.title}")
        print(f"Date: {event.date}")
        print(f"Start Time: {event.start_time}")
        print(f"Location: {event.get_full_location()}")
        print(f"Description: {event.description[:100] if event.description else 'N/A'}...")
        print()
    
    if result["quality_score"]:
        qs = result["quality_score"]
        print(f"Quality Score: {qs['overall']:.2f}")
        print(f"  Completeness: {qs['completeness']:.2f}")
        print(f"  Accuracy: {qs['accuracy']:.2f}")
        print(f"  Confidence: {qs['confidence']:.2f}")
        print(f"  Acceptable: {qs['is_acceptable']}")
        if qs.get("issues"):
            print(f"  Issues: {', '.join(qs['issues'][:3])}")
        print()
    
    if result["discord_event_id"]:
        print(f"✅ Discord Event Created!")
        print(f"   Event ID: {result['discord_event_id']}")
        print(f"   Event URL: {result['discord_event_url']}")
    else:
        print("❌ Discord event not created")
        print()
    
    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")
    
    print()
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    asyncio.run(test_bluesmuse_event())

