"""Edit scheduled event in Discord server."""

from typing import Optional
from datetime import datetime
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import EventResult
from ._bot_helper import get_bot
import discord


@register_command("discord", "edit_scheduled_event")
async def edit_scheduled_event(
    server_id: str,
    event_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    status: Optional[str] = None,
) -> ToolResponse:
    """
    Edit a scheduled event in a Discord server.

    Args:
        server_id: Discord server ID
        event_id: Event ID to edit
        name: New event name (optional)
        description: New event description (optional)
        start_time: New start time (ISO format, optional)
        end_time: New end time (ISO format, optional)
        status: Event status ('scheduled', 'active', 'completed', 'canceled', optional)

    Returns:
        ToolResponse with EventResult dataclass
    """
    try:
        bot = get_bot()
        guild = bot.get_guild(int(server_id))

        if not guild:
            return ToolResponse(is_success=False, result=None, error="Guild not found")

        event = await guild.fetch_scheduled_event(int(event_id))

        # Build kwargs for edit
        kwargs = {}

        if name:
            kwargs["name"] = name
        if description:
            kwargs["description"] = description
        if start_time:
            kwargs["start_time"] = datetime.fromisoformat(
                start_time.replace("Z", "+00:00")
            )
        if end_time:
            kwargs["end_time"] = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        if status:
            status_map = {
                "scheduled": discord.EventStatus.scheduled,
                "active": discord.EventStatus.active,
                "completed": discord.EventStatus.completed,
                "canceled": discord.EventStatus.cancelled,
            }
            if status in status_map:
                kwargs["status"] = status_map[status]

        await event.edit(**kwargs)

        result = EventResult(
            event_id=str(event.id),
            name=name or event.name,
            description=description or event.description or "",
            start_time=start_time or event.start_time.isoformat(),
            end_time=end_time or (event.end_time.isoformat() if event.end_time else ""),
            location=location or event.location or "",
            url=event.url or "",
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
