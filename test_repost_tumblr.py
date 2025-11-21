"""Test the repost_tumblr Discord tool."""

import asyncio
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

from src.mcp_ce.tools.discord.repost_tumblr import repost_tumblr
from src.mcp_ce.tools.discord._bot_helper import set_bot

# Test URLs
TEST_URL_SOYEAH = "https://www.tumblr.com/soyeahbluesdance/777551231593988096/balancing-dance-travel-in-town-events"
TEST_URL_OHYEAH = "https://ohyeahswingdance.tumblr.com/post/123456/test"


async def test_repost_tumblr():
    """Test reposting Tumblr URLs to Discord."""
    print("Testing repost_tumblr tool...")
    
    # Initialize bot for testing
    token = os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ No Discord token found in environment variables")
        return
    
    print("\n🤖 Initializing Discord bot...")
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Bot connected: {bot.user.name}")
        # Register bot with tools
        set_bot(bot)
        
        # Test 1: soyeahbluesdance in DEV mode
        print("\n" + "=" * 70)
        print("Test 1: soyeahbluesdance (DEV mode)")
        print("=" * 70)
        result = await repost_tumblr(
            tumblr_url=TEST_URL_SOYEAH,
            dev_mode=True,
        )
        
        if result.is_success:
            print("✅ Success! Posted to DEV channel")
            print(f"   Message ID: {result.result.message_id}")
            print(f"   Channel ID: {result.result.channel_id}")
        else:
            print(f"❌ Failed: {result.error}")
        
        # Test 2: soyeahbluesdance in PROD mode
        print("\n" + "=" * 70)
        print("Test 2: soyeahbluesdance (PROD mode)")
        print("=" * 70)
        result = await repost_tumblr(
            tumblr_url=TEST_URL_SOYEAH,
            dev_mode=False,
        )
        
        if result.is_success:
            print("✅ Success! Posted to PROD channel")
            print(f"   Message ID: {result.result.message_id}")
            print(f"   Channel ID: {result.result.channel_id}")
        else:
            print(f"❌ Failed: {result.error}")
        
        # Test 3: ohyeahswingdance (should create/find channel)
        print("\n" + "=" * 70)
        print("Test 3: ohyeahswingdance (should create/find channel)")
        print("=" * 70)
        result = await repost_tumblr(
            tumblr_url=TEST_URL_OHYEAH,
            dev_mode=False,
        )
        
        if result.is_success:
            print("✅ Success! Posted to ohyeahswingdance channel")
            print(f"   Message ID: {result.result.message_id}")
            print(f"   Channel ID: {result.result.channel_id}")
        else:
            print(f"❌ Failed: {result.error}")
        
        # Close bot after testing
        await bot.close()
    
    # Start bot
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")


if __name__ == "__main__":
    asyncio.run(test_repost_tumblr())

