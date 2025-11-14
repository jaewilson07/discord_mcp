"""Discord bot setup and configuration."""

import os
import logging
import discord
from discord.ext import commands
from pathlib import Path

logger = logging.getLogger("discord-mcp-server")


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


def get_discord_token() -> str:
    """Get Discord token from environment."""
    # Load .env file if it exists
    load_env()

    # Try both DISCORD_TOKEN and DISCORD_BOT_TOKEN for compatibility
    token = os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError(
            "DISCORD_TOKEN or DISCORD_BOT_TOKEN environment variable is required"
        )
    return token


def create_bot() -> commands.Bot:
    """Create and configure the Discord bot."""
    # Initialize Discord bot with necessary intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user.name}")

    return bot
