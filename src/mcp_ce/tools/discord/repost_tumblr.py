"""
Repost Tumblr posts to Discord with automatic channel routing.

Routes posts to appropriate Discord channels based on the Tumblr blog:
- soyeahbluesdance → PROD channel (or DEV channel if in dev mode)
- ohyeahswingdance → Creates/finds channel named "ohyeahswingdance"
"""

import os
import re
from typing import Optional, Tuple
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import MessageResult
from .send_message import send_message
from .upsert_text_channel import upsert_text_channel
from ._bot_helper import get_bot


# Channel routing configuration
TUMBLR_BLOG_ROUTING = {
    "soyeahbluesdance": {
        "prod_channel_id": "1441205355995463822",  # PROD: so yeah, blues dance
        "dev_channel_id": "1439978275517763684",   # DEV: bot testing channel
    },
    "ohyeahswingdance": {
        "channel_name": "ohyeahswingdance",  # Will create/find this channel
    },
}

# Server ID (same for both dev and prod)
DISCORD_SERVER_ID = "1438957830064570402"


def extract_tumblr_blog_name(tumblr_url: str) -> Optional[str]:
    """
    Extract blog name from Tumblr URL.
    
    Examples:
        https://www.tumblr.com/soyeahbluesdance/123456/... → "soyeahbluesdance"
        https://ohyeahswingdance.tumblr.com/post/123456/... → "ohyeahswingdance"
        https://www.tumblr.com/soyeahbluesdance → "soyeahbluesdance"
    """
    # Pattern 1: blogname.tumblr.com/... (subdomain format)
    # Match: blogname.tumblr.com (not www.tumblr.com)
    match = re.search(r"([a-zA-Z0-9-]+)\.tumblr\.com", tumblr_url)
    if match:
        blog_name = match.group(1)
        if blog_name != "www":
            return blog_name
    
    # Pattern 2: www.tumblr.com/blogname/... (path format)
    # Match: tumblr.com/blogname/ (skip www and common path segments)
    match = re.search(r"tumblr\.com/([a-zA-Z0-9-]+)", tumblr_url)
    if match:
        blog_name = match.group(1)
        # Skip common path segments and www
        skip_words = ["post", "reblog", "tagged", "search", "www"]
        if blog_name not in skip_words:
            return blog_name
    
    return None


def get_target_channel_id(
    blog_name: str, 
    server_id: str,
    dev_mode: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """
    Get target Discord channel ID for a Tumblr blog.
    
    Returns:
        (channel_id, error_message)
    """
    routing = TUMBLR_BLOG_ROUTING.get(blog_name)
    
    if not routing:
        return None, f"No routing configured for blog: {blog_name}"
    
    # Check if blog has direct channel ID mapping
    if "prod_channel_id" in routing:
        # Use dev channel in dev mode, prod channel otherwise
        channel_id = routing.get("dev_channel_id" if dev_mode else "prod_channel_id")
        return channel_id, None
    
    # Blog needs channel creation/finding
    if "channel_name" in routing:
        channel_name = routing["channel_name"]
        # Use upsert_text_channel to find or create
        # Note: We'll need to call this synchronously or handle it differently
        # For now, return the channel name and let the caller handle it
        return None, f"Channel needs to be created/found: {channel_name}"
    
    return None, f"Invalid routing configuration for blog: {blog_name}"


@register_command("discord", "repost_tumblr")
async def repost_tumblr(
    tumblr_url: str,
    dev_mode: Optional[bool] = None,
    server_id: Optional[str] = None,
) -> ToolResponse:
    """
    Repost a Tumblr post URL to Discord with automatic channel routing.
    
    Routes posts to appropriate Discord channels based on the Tumblr blog:
    - soyeahbluesdance → PROD channel (or DEV channel if dev_mode=True)
    - ohyeahswingdance → Creates/finds channel named "ohyeahswingdance"
    
    Args:
        tumblr_url: Full Tumblr post URL (e.g., https://www.tumblr.com/soyeahbluesdance/123456/...)
        dev_mode: If True, use dev channel for soyeahbluesdance. Defaults to False (PROD).
        server_id: Discord server ID. Defaults to configured server ID.
    
    Returns:
        ToolResponse with MessageResult dataclass
    """
    try:
        # Determine dev mode (default to False, but check env var)
        if dev_mode is None:
            dev_mode = os.getenv("DISCORD_DEV_MODE", "false").lower() == "true"
        
        # Use provided server_id or default
        target_server_id = server_id or DISCORD_SERVER_ID
        
        # Extract blog name from URL
        blog_name = extract_tumblr_blog_name(tumblr_url)
        if not blog_name:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"Could not extract blog name from URL: {tumblr_url}",
            )
        
        # Get target channel
        routing = TUMBLR_BLOG_ROUTING.get(blog_name)
        if not routing:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"No routing configured for blog: {blog_name}",
            )
        
        # Handle blogs with direct channel IDs
        if "prod_channel_id" in routing:
            channel_id = routing.get("dev_channel_id" if dev_mode else "prod_channel_id")
        # Handle blogs that need channel creation/finding
        elif "channel_name" in routing:
            channel_name = routing["channel_name"]
            # Find or create the channel
            channel_result = await upsert_text_channel(
                server_id=target_server_id,
                name=channel_name,
                force_create_duplicate=False,
            )
            
            if not channel_result.is_success:
                return ToolResponse(
                    is_success=False,
                    result=None,
                    error=f"Failed to find/create channel '{channel_name}': {channel_result.error}",
                )
            
            channel_id = channel_result.result.channel_id
        else:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"Invalid routing configuration for blog: {blog_name}",
            )
        
        # Post the URL to Discord
        message_result = await send_message(
            channel_id=channel_id,
            content=tumblr_url,
        )
        
        if not message_result.is_success:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"Failed to post message: {message_result.error}",
            )
        
        return ToolResponse(is_success=True, result=message_result.result)
        
    except Exception as e:
        return ToolResponse(is_success=False, result=None, error=str(e))

