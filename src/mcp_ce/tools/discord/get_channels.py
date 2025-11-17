"""Get Discord server channels."""

from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import ChannelListResult
from ._bot_helper import get_bot


@register_command("discord", "get_channels")
@cache_tool(ttl=300, id_param="server_id")  # Cache for 5 minutes
async def get_channels(server_id: str, override_cache: bool = False) -> ToolResponse:
    """
    Get a list of all channels in a Discord server.

    Args:
        server_id: Discord server ID
        override_cache: Whether to bypass cache and force fresh fetch (default: False)

    Returns:
        ToolResponse with ChannelListResult dataclass
    """
    try:
        bot = get_bot()
        guild = bot.get_guild(int(server_id))

        if not guild:
            return ToolResponse(is_success=False, result=None, error="Guild not found")

        channels = [
            {"name": channel.name, "id": str(channel.id), "type": str(channel.type)}
            for channel in guild.channels
        ]

        result = ChannelListResult(channels=channels, count=len(channels))

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
