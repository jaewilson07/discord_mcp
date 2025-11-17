"""Send message to Discord channel."""

from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import MessageResult
from ._bot_helper import get_bot


@register_command("discord", "send_message")
async def send_message(channel_id: str, content: str) -> ToolResponse:
    """
    Send a message to a Discord channel.

    Args:
        channel_id: Discord channel ID
        content: Message content (max 2000 characters)

    Returns:
        ToolResponse with MessageResult dataclass
    """
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channel_id))

        if not channel:
            return ToolResponse(
                is_success=False, result=None, error="Channel not found"
            )

        if len(content) > 2000:
            return ToolResponse(
                is_success=False,
                result=None,
                error="Message content exceeds 2000 characters",
            )

        message = await channel.send(content)

        result = MessageResult(
            message_id=str(message.id),
            channel_id=str(message.channel.id),
            content=content,
            timestamp=message.created_at.isoformat(),
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
