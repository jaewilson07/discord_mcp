"""Add multiple reactions to Discord message."""

from typing import List
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import ReactionResult
from ._bot_helper import get_bot


@register_command("discord", "add_multiple_reactions")
async def add_multiple_reactions(
    channel_id: str, message_id: str, emojis: List[str]
) -> ToolResponse:
    """
    Add multiple reactions to a Discord message.

    Args:
        channel_id: Discord channel ID
        message_id: Discord message ID
        emojis: List of emojis to add as reactions

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
        added = 0

        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
                added += 1
            except Exception as e:
                # Continue adding other reactions even if one fails
                pass

        result = ReactionResult(
            message_id=message_id,
            channel_id=channel_id,
            emoji=",".join(emojis),
            action=f"added_{added}",
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
