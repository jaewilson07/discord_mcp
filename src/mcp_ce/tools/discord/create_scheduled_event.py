"""Create scheduled event in Discord server."""

from typing import Optional
from datetime import datetime
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import EventResult
from ._bot_helper import get_bot
import discord


@register_command("discord", "create_scheduled_event")
async def create_scheduled_event(
    server_id: str,
    name: str,
    start_time: str,
    description: Optional[str] = None,
    end_time: Optional[str] = None,
    entity_type: str = "external",
    channel_id: Optional[str] = None,
    location: Optional[str] = None,
) -> ToolResponse:
    """
    Create a scheduled event in a Discord server.

    Args:
        server_id: Discord server ID
        name: Event name
        start_time: ISO format datetime string for event start
        description: Event description (optional)
        end_time: ISO format datetime string for event end (required for external events)
        entity_type: Event type ('voice', 'stage_instance', or 'external')
        channel_id: Channel ID (required for voice/stage_instance)
        location: Location (required for external events)

    Returns:
        ToolResponse with EventResult dataclass
    """
    try:
        bot = get_bot()
        guild = bot.get_guild(int(server_id))

        if not guild:
            return ToolResponse(is_success=False, result=None, error="Guild not found")

        # Parse datetime
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = None
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        # Determine entity type
        entity_type_map = {
            "voice": discord.EntityType.voice,
            "stage_instance": discord.EntityType.stage_instance,
            "external": discord.EntityType.external,
        }
        entity = entity_type_map.get(entity_type, discord.EntityType.external)

        # Build kwargs
        kwargs = {
            "name": name,
            "start_time": start_dt,
            "entity_type": entity,
            "privacy_level": discord.PrivacyLevel.guild_only,  # Required parameter
        }

        if description:
            kwargs["description"] = description
        if end_dt:
            kwargs["end_time"] = end_dt
        if channel_id:
            kwargs["channel"] = bot.get_channel(int(channel_id))
        if location:
            kwargs["location"] = location

        event = await guild.create_scheduled_event(**kwargs)

        result = EventResult(
            event_id=str(event.id),
            name=event.name,
            description=event.description or "",
            start_time=start_time,
            end_time=end_time or "",
            location=event.location or "",
            url=event.url or "",
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
