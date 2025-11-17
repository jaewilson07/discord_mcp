"""Move Discord channel."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import ChannelMoveResult
from ._bot_helper import get_bot


@register_command("discord", "move_channel")
async def move_channel(
    channel_id: str, category_id: Optional[str] = None, position: Optional[int] = None
) -> ToolResponse:
    """
    Move a Discord channel to a different category or position.

    Args:
        channel_id: Discord channel ID to move
        category_id: Target category ID (None to remove from category)
        position: Optional position in the channel list

    Returns:
        ToolResponse with ChannelMoveResult dataclass
    """
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channel_id))

        if not channel:
            return ToolResponse(
                is_success=False, result=None, error="Channel not found"
            )

        kwargs = {}
        if category_id is not None:
            category = bot.get_channel(int(category_id))
            kwargs["category"] = category
        if position is not None:
            kwargs["position"] = position

        await channel.edit(**kwargs)

        result = ChannelMoveResult(
            channel_id=channel_id,
            new_category_id=category_id or "",
            new_position=position or channel.position,
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
