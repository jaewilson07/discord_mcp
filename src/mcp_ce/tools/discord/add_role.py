"""Add role to Discord user."""

from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import RoleResult
from ._bot_helper import get_bot


@register_command("discord", "add_role")
async def add_role(server_id: str, user_id: str, role_id: str) -> ToolResponse:
    """
    Add a role to a Discord user.

    Args:
        server_id: Discord server ID
        user_id: Discord user ID
        role_id: Discord role ID to add

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

        await member.add_roles(role)

        result = RoleResult(
            user_id=user_id,
            role_id=role_id,
            role_name=role.name,
            server_id=server_id,
            action="added",
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
