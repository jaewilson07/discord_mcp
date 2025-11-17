#!/usr/bin/env python3
"""
Unified MCP CE Server with Discord Bot Integration.
Usage: python run.py
"""

import asyncio
import sys
import os
import logging
import discord
import warnings
from pathlib import Path
from discord.ext import commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s %(name)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger("mcp-ce-server")

# Suppress PyNaCl warning since we don't use voice features
warnings.filterwarnings('ignore', module='discord.client', message='PyNaCl is not installed')


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        logger.info("Loading environment from .env file")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    else:
        logger.warning(".env file not found")


def get_discord_token() -> str:
    """Get Discord token from environment."""
    token = os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError(
            "DISCORD_TOKEN or DISCORD_BOT_TOKEN environment variable is required"
        )
    return token


def create_discord_bot() -> commands.Bot:
    """Create and configure the Discord bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f"Discord bot logged in as {bot.user.name}")
        logger.info(f"Bot is in {len(bot.guilds)} server(s)")
        
        # Register bot with mcp_ce tools
        from src.mcp_ce.tools.discord._bot_helper import set_bot
        set_bot(bot)
        logger.info("Bot registered with MCP CE runtime")
    
    return bot


async def main():
    """Main entry point for unified MCP CE server with Discord."""
    try:
        # Load environment
        load_env()
        
        # Get Discord token
        logger.info("🤖 Initializing Discord bot...")
        token = get_discord_token()
        bot = create_discord_bot()
        
        # Start Discord bot in background
        bot_task = asyncio.create_task(bot.start(token))
        
        # Wait for bot to be ready
        logger.info("⏳ Waiting for Discord bot to connect...")
        await asyncio.sleep(3)
        
        logger.info("✅ MCP CE Server with Discord bot is running")
        logger.info("📡 Ready to receive tool calls via MCP protocol")
        logger.info("Press Ctrl+C to shutdown")
        
        # Keep running until interrupted
        await bot_task
        
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down MCP CE server...")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        print("🚀 Starting MCP CE Server with Discord Integration...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutdown complete")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
