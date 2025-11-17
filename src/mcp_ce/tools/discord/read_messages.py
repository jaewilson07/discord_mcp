"""Read messages from Discord channel."""

from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import MessageListResult
from ._bot_helper import get_bot


@register_command("discord", "read_messages")
@cache_tool(ttl=60, id_param="channel_id")  # Cache for 1 minute
async def read_messages(
    channel_id: str, limit: int = 10, override_cache: bool = False
) -> ToolResponse:
    """
    Read recent messages from a Discord channel.

    Args:
        channel_id: Discord channel ID
        limit: Number of messages to retrieve (default: 10, max: 100)
        override_cache: Whether to bypass cache and force fresh fetch (default: False)

    Returns:
        Dictionary with success status and messages list or error
    """
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channel_id))

        if not channel:
            return ToolResponse(
                is_success=False, result=None, error="Channel not found"
            )

        limit = min(limit, 100)
        messages = []

        async for message in channel.history(limit=limit):
            messages.append(
                {
                    "id": str(message.id),
                    "author_name": message.author.name,
                    "author_id": str(message.author.id),
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                    "attachments": [str(a.url) for a in message.attachments],
                    "embeds": len(message.embeds),
                }
            )

        result = MessageListResult(messages=messages, count=len(messages))
        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
