"""Create category channel in Discord server."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import CategoryResult
from ._bot_helper import get_bot


@register_command("discord", "create_category")
async def create_category(
    server_id: str, name: str, position: Optional[int] = None
) -> ToolResponse:
    """
    Create a new category channel in a Discord server.

    Args:
        server_id: Discord server ID
        name: Category name
        position: Optional position in the channel list (0-indexed)

    Returns:
        ToolResponse with CategoryResult dataclass
    """
    try:
        bot = get_bot()
        guild = bot.get_guild(int(server_id))

        if not guild:
            return ToolResponse(is_success=False, result=None, error="Guild not found")

        kwargs = {"name": name}
        if position is not None:
            kwargs["position"] = position

        category = await guild.create_category(**kwargs)

        result = CategoryResult(
            category_id=str(category.id),
            name=category.name,
            position=category.position,
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
