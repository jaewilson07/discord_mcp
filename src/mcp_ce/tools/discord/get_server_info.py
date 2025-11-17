"""Get Discord server information."""

from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import ServerInfo
from ._bot_helper import get_bot


@register_command("discord", "get_server_info")
@cache_tool(ttl=600, id_param="server_id")  # Cache for 10 minutes
async def get_server_info(server_id: str, override_cache: bool = False) -> ToolResponse:
    """
    Get detailed information about a Discord server.

    Args:
        server_id: Discord server ID
        override_cache: Whether to bypass cache and force fresh fetch (default: False)

    Returns:
        ToolResponse with ServerInfo dataclass
    """
    try:
        bot = get_bot()
        guild = await bot.fetch_guild(int(server_id))

        result = ServerInfo(
            server_id=str(guild.id),
            name=guild.name,
            description=guild.description or "",
            member_count=guild.member_count,
            owner_id=str(guild.owner_id),
            created_at=guild.created_at.isoformat(),
            icon_url=str(guild.icon.url) if guild.icon else "",
            features=[str(f) for f in guild.features],
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
