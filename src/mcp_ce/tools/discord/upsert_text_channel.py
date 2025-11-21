"""Upsert text channel in Discord server - checks for existing channels first."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import ChannelResult
from ._bot_helper import get_bot


@register_command("discord", "upsert_text_channel")
async def upsert_text_channel(
    server_id: str,
    name: str,
    category_id: Optional[str] = None,
    force_create_duplicate: bool = False,
) -> ToolResponse:
    """
    Create a text channel in a Discord server, or return existing channel if it already exists.
    
    This tool prevents duplicate channels by checking for existing channels with the same name.
    If a duplicate is found, it returns the existing channel unless force_create_duplicate=True.

    Args:
        server_id: Discord server ID
        name: Channel name
        category_id: Optional category ID to create channel under
        force_create_duplicate: If True, creates a duplicate even if channel with same name exists.
                              If False (default), returns existing channel if found.

    Returns:
        ToolResponse with ChannelResult dataclass.
        If duplicate found and force_create_duplicate=False, returns existing channel info.
        If duplicate found and force_create_duplicate=True, creates new channel.
        If no duplicate, creates new channel.
    """
    try:
        bot = get_bot()
        guild = bot.get_guild(int(server_id))

        if not guild:
            return ToolResponse(is_success=False, result=None, error="Guild not found")

        # Normalize channel name for comparison (Discord converts spaces to hyphens)
        normalized_name = name.lower().replace(" ", "-")

        # Check for existing channels with the same name
        existing_channels = []
        for channel in guild.channels:
            if (
                channel.name.lower() == normalized_name
                and str(channel.type) == "text"
            ):
                existing_channels.append(channel)

        # If duplicates found and not forcing, return the first existing channel
        if existing_channels and not force_create_duplicate:
            existing = existing_channels[0]
            result = ChannelResult(
                channel_id=str(existing.id),
                name=existing.name,
                type="text",
                category_id=str(existing.category_id) if existing.category_id else "",
                position=existing.position,
            )
            return ToolResponse(
                is_success=True,
                result=result,
                error=f"Channel '{name}' already exists (found {len(existing_channels)} duplicate(s)). Use force_create_duplicate=True to create a duplicate.",
            )

        # Create new channel
        category = None
        if category_id:
            category = guild.get_channel(int(category_id))

        channel = await guild.create_text_channel(name=name, category=category)

        result = ChannelResult(
            channel_id=str(channel.id),
            name=channel.name,
            type="text",
            category_id=str(channel.category_id) if channel.category_id else "",
            position=channel.position,
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))

