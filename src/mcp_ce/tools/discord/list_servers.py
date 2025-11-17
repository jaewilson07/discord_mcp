"""List all Discord servers the bot has access to."""

from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import ServerListResult
from ._bot_helper import get_bot


@register_command("discord", "list_servers")
async def list_servers() -> ToolResponse:
    """
    List all Discord servers the bot has access to.

    Returns:
        ToolResponse with ServerListResult dataclass
    """
    try:
        bot = get_bot()

        servers = [
            {
                "id": str(guild.id),
                "name": guild.name,
                "member_count": guild.member_count,
                "owner": guild.owner_id == bot.user.id if guild.owner_id else False,
            }
            for guild in bot.guilds
        ]

        result = ServerListResult(servers=servers, count=len(servers))

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
