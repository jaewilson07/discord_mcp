"""Delete Discord channel."""

from registry import register_command
from mcp_ce.tools.model import ToolResponse
from ._bot_helper import get_bot


@register_command("discord", "delete_channel")
async def delete_channel(channel_id: str) -> ToolResponse:
    """
    Delete a Discord channel.

    Args:
        channel_id: Discord channel ID to delete

    Returns:
        ToolResponse with no result model (deletion confirmation)
    """
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channel_id))

        if not channel:
            return ToolResponse(
                is_success=False, result=None, error="Channel not found"
            )

        await channel.delete()

        return ToolResponse(is_success=True, result={"channel_id": channel_id})
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
