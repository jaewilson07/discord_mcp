"""Get Discord user information."""

from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import UserInfo
from ._bot_helper import get_bot


@register_command("discord", "get_user_info")
@cache_tool(ttl=1800, id_param="user_id")  # Cache for 30 minutes
async def get_user_info(user_id: str, override_cache: bool = False) -> ToolResponse:
    """
    Get information about a Discord user.

    Args:
        user_id: Discord user ID
        override_cache: Whether to bypass cache and force fresh fetch (default: False)

    Returns:
        ToolResponse with UserInfo dataclass
    """
    try:
        bot = get_bot()
        user = await bot.fetch_user(int(user_id))

        result = UserInfo(
            user_id=str(user.id),
            username=user.name,
            discriminator=user.discriminator,
            display_name=user.display_name or user.name,
            avatar_url=str(user.avatar.url) if user.avatar else "",
            bot=user.bot,
            created_at=user.created_at.isoformat(),
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
