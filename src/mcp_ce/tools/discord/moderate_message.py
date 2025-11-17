"""Moderate Discord message."""

from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import ModerationResult
from ._bot_helper import get_bot


@register_command("discord", "moderate_message")
async def moderate_message(
    channel_id: str, message_id: str, action: str
) -> ToolResponse:
    """
    Moderate a Discord message (delete or pin/unpin).

    Args:
        channel_id: Discord channel ID
        message_id: Discord message ID
        action: Moderation action ('delete', 'pin', or 'unpin')

    Returns:
        ToolResponse with ModerationResult dataclass
    """
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channel_id))

        if not channel:
            return ToolResponse(
                is_success=False, result=None, error="Channel not found"
            )

        message = await channel.fetch_message(int(message_id))

        if action == "delete":
            await message.delete()
        elif action == "pin":
            await message.pin()
        elif action == "unpin":
            await message.unpin()
        else:
            return ToolResponse(
                is_success=False, result=None, error=f"Invalid action: {action}"
            )

        result = ModerationResult(
            message_id=message_id,
            channel_id=channel_id,
            action=action,
            moderator_id=str(bot.user.id),
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
