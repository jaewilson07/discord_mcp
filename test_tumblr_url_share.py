"""
Test script for simple Tumblr URL sharing to Discord.

Just extracts and shares Tumblr post URLs - Discord auto-embeds them!
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from mcp_ce.agentic_tools.graphs.tumblr_feed.repost_tumblr_urls import (
    repost_tumblr_urls_to_discord,
    sync_tumblr_feed_simple,
)
from mcp_ce.tools.discord.list_servers import list_servers
from mcp_ce.tools.discord.get_channels import get_channels
from mcp_ce.tools.discord._bot_helper import is_bot_ready


async def test_single_url():
    """Test sharing a single Tumblr URL."""
    
    TEST_URL = "https://www.tumblr.com/soyeahbluesdance/777638063054651392/leaving-the-late-night"
    
    print("=" * 70)
    print("Tumblr URL Share Test - Single URL")
    print("=" * 70)
    print()
    
    # Check Discord bot
    if not is_bot_ready():
        print("❌ Discord bot not ready")
        return
    
    # Get Discord channel ID
    discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
    
    if not discord_channel_id:
        print("⚠️  DISCORD_CHANNEL_ID not set, trying to find a channel...")
        servers_result = await list_servers()
        if servers_result.is_success and servers_result.result:
            servers = servers_result.result.servers
            if servers:
                server_id = servers[0]["id"]
                channels_result = await get_channels(server_id=server_id)
                if channels_result.is_success and channels_result.result:
                    channels = channels_result.result.channels
                    text_channels = [c for c in channels if c.get("type") == "text"]
                    if text_channels:
                        discord_channel_id = text_channels[0]["id"]
                        print(f"   Using channel: {text_channels[0]['name']}")
    
    if not discord_channel_id:
        print("❌ No Discord channel available")
        return
    
    print(f"\n📋 Test Configuration:")
    print(f"   Tumblr URL: {TEST_URL}")
    print(f"   Discord Channel ID: {discord_channel_id}")
    print()
    
    # Share the URL
    print("🚀 Sharing URL to Discord...")
    print("   (Discord will auto-embed/preview the link)")
    print()
    
    result = await repost_tumblr_urls_to_discord(
        tumblr_urls=[TEST_URL],
        discord_channel_id=discord_channel_id,
    )
    
    # Print results
    print()
    print("=" * 70)
    print("Results")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Posts posted: {result['posts_posted']}")
    
    if result.get("errors"):
        print(f"\n⚠️  Errors:")
        for error in result["errors"]:
            print(f"   - {error}")
    
    if result["success"]:
        print("\n🎉 URL shared successfully!")
        print("   Check Discord - the link should be auto-embedded!")


async def test_feed_sync():
    """Test syncing the full feed."""
    
    print("\n" + "=" * 70)
    print("Tumblr Feed Sync Test")
    print("=" * 70)
    print()
    
    if not is_bot_ready():
        print("❌ Discord bot not ready")
        return
    
    discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
    if not discord_channel_id:
        print("⚠️  Set DISCORD_CHANNEL_ID to test feed sync")
        return
    
    result = await sync_tumblr_feed_simple(
        tumblr_feed_url="https://www.tumblr.com/soyeahbluesdance",
        discord_channel_id=discord_channel_id,
        max_posts=5,
        check_duplicates=False,  # Skip duplicate check for testing
    )
    
    print(f"\n📊 Results:")
    print(f"   URLs found: {result['urls_found']}")
    print(f"   URLs posted: {result['urls_posted']}")
    if result.get("errors"):
        for error in result["errors"]:
            print(f"   Error: {error}")


if __name__ == "__main__":
    # Test single URL first
    asyncio.run(test_single_url())
    
    # Uncomment to test full feed sync:
    # asyncio.run(test_feed_sync())

