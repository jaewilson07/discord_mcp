"""Remove role from Discord user."""

from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import RoleResult
from ._bot_helper import get_bot


@register_command("discord", "remove_role")
async def remove_role(server_id: str, user_id: str, role_id: str) -> ToolResponse:
    """
    Remove a role from a Discord user.

    Args:
        server_id: Discord server ID
        user_id: Discord user ID
        role_id: Discord role ID to remove

    Returns:
        ToolResponse with RoleResult dataclass
    """
    try:
        bot = get_bot()
        guild = bot.get_guild(int(server_id))

        if not guild:
            return ToolResponse(is_success=False, result=None, error="Guild not found")

        member = await guild.fetch_member(int(user_id))
        role = guild.get_role(int(role_id))

        if not role:
            return ToolResponse(is_success=False, result=None, error="Role not found")

        await member.remove_roles(role)

        result = RoleResult(
            user_id=user_id,
            role_id=role_id,
            role_name=role.name,
            server_id=server_id,
            action="removed",
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
