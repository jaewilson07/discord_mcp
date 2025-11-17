"""Delete scheduled event from Discord server."""

from registry import register_command
from mcp_ce.tools.model import ToolResponse
from ._bot_helper import get_bot


@register_command("discord", "delete_scheduled_event")
async def delete_scheduled_event(
    server_id: str,
    event_id: str,
) -> ToolResponse:
    """
    Delete a scheduled event from a Discord server.

    Args:
        server_id: Discord server ID
        event_id: Event ID to delete

    Returns:
        ToolResponse with success status
    """
    try:
        bot = get_bot()
        guild = bot.get_guild(int(server_id))

        if not guild:
            return ToolResponse(is_success=False, result=None, error="Guild not found")

        # Fetch the event
        event = guild.get_scheduled_event(int(event_id))

        if not event:
            # Try fetching from API if not in cache
            try:
                event = await guild.fetch_scheduled_event(int(event_id))
            except Exception:
                return ToolResponse(
                    is_success=False, result=None, error=f"Event {event_id} not found"
                )

        # Delete the event
        await event.delete()

        return ToolResponse(
            is_success=True, result={"event_id": event_id, "deleted": True}
        )
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
