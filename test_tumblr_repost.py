"""
Test script for Tumblr repost to Discord workflow.

Tests the simple repost function with a real Tumblr URL.
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

from mcp_ce.agentic_tools.graphs.tumblr_feed.repost_tumblr_to_discord import (
    repost_tumblr_to_discord,
)
from mcp_ce.tools.discord.list_servers import list_servers
from mcp_ce.tools.discord.get_channels import get_channels
from mcp_ce.tools.discord._bot_helper import is_bot_ready


async def test_tumblr_repost():
    """Test reposting a Tumblr post to Discord."""
    
    # Test URL
    TEST_URL = "https://www.tumblr.com/soyeahbluesdance/777638063054651392/leaving-the-late-night"
    
    print("=" * 70)
    print("Tumblr Repost to Discord - Test")
    print("=" * 70)
    print()
    
    # Check Discord bot
    if not is_bot_ready():
        print("❌ Discord bot not ready")
        print("   Make sure DISCORD_BOT_TOKEN is set and bot is running")
        return
    
    # Get Discord channel ID
    discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
    
    if not discord_channel_id:
        print("⚠️  DISCORD_CHANNEL_ID not set, trying to find a channel...")
        
        # Get first available server
        servers_result = await list_servers()
        if servers_result.is_success and servers_result.result:
            servers = servers_result.result.servers
            if servers:
                server_id = servers[0]["id"]
                print(f"   Using server: {servers[0]['name']}")
                
                # Get channels
                channels_result = await get_channels(server_id=server_id)
                if channels_result.is_success and channels_result.result:
                    channels = channels_result.result.channels
                    # Find first text channel
                    text_channels = [c for c in channels if c.get("type") == "text"]
                    if text_channels:
                        discord_channel_id = text_channels[0]["id"]
                        print(f"   Using channel: {text_channels[0]['name']} (ID: {discord_channel_id})")
    
    if not discord_channel_id:
        print("❌ No Discord channel available")
        print("   Set DISCORD_CHANNEL_ID environment variable or ensure bot has access to channels")
        return
    
    print(f"\n📋 Test Configuration:")
    print(f"   Tumblr URL: {TEST_URL}")
    print(f"   Discord Channel ID: {discord_channel_id}")
    print()
    
    # Run the repost workflow
    print("🚀 Starting repost workflow...")
    print()
    
    result = await repost_tumblr_to_discord(
        tumblr_url=TEST_URL,
        discord_channel_id=discord_channel_id,
    )
    
    # Print results
    print()
    print("=" * 70)
    print("Results")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print()
    
    if result.get("image_url"):
        print(f"✅ Image URL extracted:")
        print(f"   {result['image_url']}")
        print()
    
    if result.get("caption"):
        print(f"✅ Caption extracted:")
        print(f"   {result['caption'][:200]}...")
        print()
    
    if result.get("discord_message_id"):
        print(f"✅ Posted to Discord!")
        print(f"   Message ID: {result['discord_message_id']}")
        print()
    
    if result.get("errors"):
        print(f"⚠️  Errors:")
        for error in result["errors"]:
            print(f"   - {error}")
        print()
    
    if result["success"]:
        print("🎉 Test completed successfully!")
    else:
        print("❌ Test failed - check errors above")


if __name__ == "__main__":
    asyncio.run(test_tumblr_repost())

