"""Discord MCP Server Entry Point

Main entry point for the Discord MCP server that initializes the Discord bot
and runs the MCP Code Execution server.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s %(name)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger("discord-mcp-server")

# Suppress PyNaCl warning since we don't use voice features
import warnings
warnings.filterwarnings('ignore', module='discord.client', message='PyNaCl is not installed')


def load_env():
    """Load environment variables from .env file."""
    # Try to find .env file relative to project root
    # When installed as package, go up from src/discord_mcp/server.py -> src -> project root
    # When run as script, go up from src/discord_mcp/server.py -> src -> project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        logger.info("Loading environment from .env file")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    else:
        logger.debug(".env file not found (using environment variables)")


def get_discord_token() -> str:
    """Get Discord token from environment."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError(
            "DISCORD_TOKEN environment variable is required. "
            "Set it in your .env file or environment."
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
        from mcp_ce.tools.discord._bot_helper import set_bot
        set_bot(bot)
    
    return bot


async def start_discord_bot(bot: commands.Bot, token: str):
    """Start the Discord bot in the background."""
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error starting Discord bot: {e}")
        raise


def main():
    """Main entry point for Discord MCP server."""
    import sys
    
    # Check for --info or --discover flag
    if "--info" in sys.argv or "--discover" in sys.argv:
        from mcp_ce.server import show_sandbox_helpers
        show_sandbox_helpers()
        return
    
    # Load environment
    load_env()
    
    # Check if Discord token is available
    try:
        token = get_discord_token()
    except ValueError as e:
        logger.warning(f"{e}")
        logger.warning("Running MCP server without Discord bot (Discord tools will not work)")
        # Run MCP server without Discord bot
        from mcp_ce.server import mcp
        mcp.run()
        return
    
    # Initialize Discord bot
    logger.info("🤖 Initializing Discord bot...")
    bot = create_discord_bot()
    
    # Start bot in background task
    async def run_with_bot():
        bot_task = asyncio.create_task(start_discord_bot(bot, token))
        
        # Wait a bit for bot to connect
        await asyncio.sleep(2)
        
        # Run MCP server (this blocks)
        from mcp_ce.server import mcp
        logger.info("✅ Discord bot connected")
        logger.info("📡 Starting MCP server...")
        mcp.run()
        
        # Cleanup
        await bot.close()
    
    try:
        asyncio.run(run_with_bot())
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down Discord MCP server...")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

