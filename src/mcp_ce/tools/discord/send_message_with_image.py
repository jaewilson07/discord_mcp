"""Send message to Discord channel with image/GIF support."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import MessageResult
from ._bot_helper import get_bot
import discord


@register_command("discord", "send_message_with_image")
async def send_message_with_image(
    channel_id: str,
    content: Optional[str] = None,
    image_url: Optional[str] = None,
) -> ToolResponse:
    """
    Send a message to a Discord channel with an image/GIF.
    
    Discord will auto-embed image URLs, so we can send the image URL
    along with the caption text in the same message.
    
    Args:
        channel_id: Discord channel ID
        content: Message content/caption (optional, max 2000 characters)
        image_url: URL to image or GIF to embed (optional)
    
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

        # Build message content
        message_parts = []
        
        # Add caption if provided
        if content:
            if len(content) > 2000:
                return ToolResponse(
                    is_success=False,
                    result=None,
                    error="Message content exceeds 2000 characters",
                )
            message_parts.append(content)
        
        # Add image URL if provided (Discord will auto-embed)
        if image_url:
            message_parts.append(image_url)
        
        if not message_parts:
            return ToolResponse(
                is_success=False,
                result=None,
                error="Either content or image_url must be provided",
            )
        
        # Send message with image URL (Discord auto-embeds)
        message_content = "\n".join(message_parts)
        message = await channel.send(message_content)

        result = MessageResult(
            message_id=str(message.id),
            channel_id=str(message.channel.id),
            content=message_content,
            timestamp=message.created_at.isoformat(),
        )

        return ToolResponse(is_success=True, result=result)
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))

