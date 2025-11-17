"""Create text channel in Discord server."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import ChannelResult
from ._bot_helper import get_bot


@register_command("discord", "create_text_channel")
async def create_text_channel(
    server_id: str, name: str, category_id: Optional[str] = None
) -> ToolResponse:
    """
    Create a new text channel in a Discord server.

    Args:
        server_id: Discord server ID
        name: Channel name
        category_id: Optional category ID to create channel under

    Returns:
        ToolResponse with ChannelResult dataclass
    """
    try:
        bot = get_bot()
        guild = bot.get_guild(int(server_id))

        if not guild:
            return ToolResponse(is_success=False, result=None, error="Guild not found")

        category = None
        if category_id:
            category = guild.get_channel(int(category_id))

        channel = await guild.create_text_channel(name=name, category=category)

        result = ChannelResult(
            channel_id=str(channel.id),
            channel_name=channel.name,
            channel_type="text",
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
