"""Add reaction to Discord message."""

from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import ReactionResult
from ._bot_helper import get_bot


@register_command("discord", "add_reaction")
async def add_reaction(channel_id: str, message_id: str, emoji: str) -> ToolResponse:
    """
    Add a reaction to a Discord message.

    Args:
        channel_id: Discord channel ID
        message_id: Discord message ID
        emoji: Emoji to react with (Unicode or custom emoji ID)

    Returns:
        ToolResponse with ReactionResult dataclass
    """
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channel_id))

        if not channel:
            return ToolResponse(
                is_success=False, result=None, error="Channel not found"
            )

        message = await channel.fetch_message(int(message_id))
        await message.add_reaction(emoji)

        result = ReactionResult(
            message_id=message_id,
            channel_id=channel_id,
            emoji=emoji,
            action="added",
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
