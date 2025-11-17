"""List Discord server members."""

from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import MemberListResult
from ._bot_helper import get_bot


@register_command("discord", "list_members")
@cache_tool(ttl=300, id_param="server_id")  # Cache for 5 minutes
async def list_members(
    server_id: str, limit: int = 100, override_cache: bool = False
) -> ToolResponse:
    """
    List members in a Discord server.

    Args:
        server_id: Discord server ID
        limit: Maximum number of members to retrieve (default: 100, max: 1000)
        override_cache: Whether to bypass cache and force fresh fetch (default: False)

    Returns:
        ToolResponse with MemberListResult dataclass
    """
    try:
        bot = get_bot()
        guild = await bot.fetch_guild(int(server_id))
        limit = min(limit, 1000)

        members = []
        async for member in guild.fetch_members(limit=limit):
            members.append(
                {
                    "id": str(member.id),
                    "name": member.name,
                    "nick": member.nick or member.name,
                    "joined_at": (
                        member.joined_at.isoformat() if member.joined_at else ""
                    ),
                    "roles": [
                        str(role.id) for role in member.roles[1:]
                    ],  # Skip @everyone
                }
            )

        result = MemberListResult(members=members, count=len(members))

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
