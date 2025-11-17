"""Helper to get Discord bot client for tool execution."""

import os
from typing import Optional
from discord.ext import commands


# Singleton bot instance
_bot_instance: Optional[commands.Bot] = None


def get_bot() -> commands.Bot:
    """
    Get or create the Discord bot instance.
    
    The bot must be already running (started by server.py or bot.py).
    This helper retrieves the existing bot instance.
    
    Returns:
        commands.Bot: The Discord bot instance
        
    Raises:
        RuntimeError: If bot is not initialized
    """
    global _bot_instance
    
    if _bot_instance is None:
        raise RuntimeError(
            "Discord bot not initialized. "
            "Make sure the Discord MCP server is running with a valid bot token."
        )
    
    return _bot_instance


def set_bot(bot: commands.Bot) -> None:
    """
    Set the Discord bot instance (called during server startup).
    
    Args:
        bot: The Discord bot instance
    """
    global _bot_instance
    _bot_instance = bot


def is_bot_ready() -> bool:
    """Check if bot is ready."""
    return _bot_instance is not None and _bot_instance.is_ready()
