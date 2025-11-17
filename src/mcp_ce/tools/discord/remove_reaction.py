"""Remove reaction from Discord message."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import ReactionResult
from ._bot_helper import get_bot


@register_command("discord", "remove_reaction")
async def remove_reaction(
    channel_id: str, message_id: str, emoji: str, user_id: Optional[str] = None
) -> ToolResponse:
    """
    Remove a reaction from a Discord message.

    Args:
        channel_id: Discord channel ID
        message_id: Discord message ID
        emoji: Emoji reaction to remove
        user_id: User ID whose reaction to remove (optional, defaults to bot)

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

        if user_id:
            user = await bot.fetch_user(int(user_id))
            await message.remove_reaction(emoji, user)
        else:
            await message.remove_reaction(emoji, bot.user)

        result = ReactionResult(
            message_id=message_id,
            channel_id=channel_id,
            emoji=emoji,
            action="removed",
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
