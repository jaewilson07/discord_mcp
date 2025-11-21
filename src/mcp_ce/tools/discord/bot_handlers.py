"""
Discord bot handlers for @mentions and slash commands.

Handles:
- @mention the bot to share Tumblr links
- /share_tumblr_link slash command
- /add_event slash command to create Discord events from URLs
"""

import re
import logging
import sys
from pathlib import Path
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

# Add src to path for registry import
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from registry import get_tool
from mcp_ce.tools.model import ToolResponse

# Import tools to ensure they're registered
try:
    from mcp_ce.tools.tumblr.extract_post_urls import extract_post_urls
    from mcp_ce.tools.discord.send_message import send_message
except ImportError as e:
    logger.warning(f"Failed to import some tools: {e}")

# Event creation workflow will be imported lazily in the command handler
# to avoid agent initialization issues at module load time

logger = logging.getLogger(__name__)


def extract_tumblr_url(text: str) -> Optional[str]:
    """
    Extract Tumblr URL from text.
    
    Supports:
    - Full blog URLs: https://www.tumblr.com/soyeahbluesdance
    - Post URLs: https://www.tumblr.com/soyeahbluesdance/1234567890/post-title
    - Subdomain format: https://blogname.tumblr.com
    
    Args:
        text: Text to search for Tumblr URLs
        
    Returns:
        First Tumblr URL found, or None
    """
    # Pattern to match Tumblr URLs
    pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+\.)?tumblr\.com(?:/[^\s\)]+)?'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None


async def share_tumblr_link(
    tumblr_url: str,
    channel: discord.TextChannel,
    max_posts: int = 1
) -> tuple[bool, str]:
    """
    Share Tumblr link(s) to a Discord channel using MCP tools.
    
    Args:
        tumblr_url: Tumblr blog URL or post URL
        channel: Discord channel to send to
        max_posts: Maximum number of posts to share (default: 1)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Get the tumblr extract_post_urls tool
        extract_tool = get_tool("tumblr", "extract_post_urls")
        if not extract_tool:
            return False, "Tumblr extraction tool not available"
        
        # Check if it's a post URL or blog URL
        is_post_url = "/" in tumblr_url.split("tumblr.com/")[-1] if "tumblr.com/" in tumblr_url else False
        
        if is_post_url:
            # Direct post URL - just send it
            send_tool = get_tool("discord", "send_message")
            if not send_tool:
                return False, "Discord send_message tool not available"
            
            result = await send_tool(
                channel_id=str(channel.id),
                content=tumblr_url
            )
            
            if result.is_success:
                return True, f"Shared Tumblr post: {tumblr_url}"
            else:
                return False, f"Failed to send message: {result.error}"
        else:
            # Blog URL - extract post URLs
            logger.info(f"Extracting post URLs from blog: {tumblr_url}")
            
            result: ToolResponse = await extract_tool(
                tumblr_blog_url=tumblr_url,
                max_posts=max_posts,
                override_cache=False
            )
            
            if not result.is_success:
                return False, f"Failed to extract posts: {result.error}"
            
            post_urls = result.result.get("post_urls", [])
            if not post_urls:
                return False, f"No posts found in blog: {tumblr_url}"
            
            # Send each post URL
            send_tool = get_tool("discord", "send_message")
            if not send_tool:
                return False, "Discord send_message tool not available"
            
            shared_count = 0
            for post_url in post_urls[:max_posts]:
                send_result = await send_tool(
                    channel_id=str(channel.id),
                    content=post_url
                )
                if send_result.is_success:
                    shared_count += 1
                else:
                    logger.warning(f"Failed to send post URL {post_url}: {send_result.error}")
            
            if shared_count > 0:
                return True, f"Shared {shared_count} post(s) from {tumblr_url}"
            else:
                return False, "Failed to share any posts"
                
    except Exception as e:
        logger.error(f"Error sharing Tumblr link: {e}", exc_info=True)
        return False, f"Error: {str(e)}"


def setup_bot_handlers(bot: commands.Bot):
    """
    Set up Discord bot handlers for @mentions and slash commands.
    
    Args:
        bot: Discord bot instance
    """
    
    # Slash command: /share_tumblr_link
    @bot.tree.command(name="share_tumblr_link", description="Share a Tumblr blog or post link")
    @app_commands.describe(
        url="Tumblr blog URL or post URL to share",
        max_posts="Maximum number of posts to share (default: 1, max: 10)"
    )
    async def share_tumblr_link_command(
        interaction: discord.Interaction,
        url: str,
        max_posts: int = 1
    ):
        """Slash command to share Tumblr links."""
        # Validate max_posts
        max_posts = max(1, min(max_posts, 10))
        
        # Validate URL
        if not extract_tumblr_url(url):
            await interaction.response.send_message(
                f"❌ Invalid Tumblr URL: {url}\n"
                "Please provide a valid Tumblr blog or post URL.",
                ephemeral=True
            )
            return
        
        # Acknowledge the interaction
        await interaction.response.defer(thinking=True)
        
        # Share the link
        success, message = await share_tumblr_link(
            tumblr_url=url,
            channel=interaction.channel,
            max_posts=max_posts
        )
        
        if success:
            await interaction.followup.send(f"✅ {message}", ephemeral=False)
        else:
            await interaction.followup.send(f"❌ {message}", ephemeral=True)
    
    # Slash command: /add_event
    @bot.tree.command(name="add_event", description="Create a Discord scheduled event from a website URL")
    @app_commands.describe(
        url="Website URL containing event information to scrape and create event from"
    )
    async def add_event_command(
        interaction: discord.Interaction,
        url: str
    ):
        """Slash command to create Discord event from URL."""
        # Lazy import to avoid agent initialization issues
        try:
            from mcp_ce.agentic_tools.graphs.create_discord_event_from_url.create_discord_event_from_url import (
                create_discord_event_from_url,
            )
        except ImportError as e:
            logger.error(f"Failed to import event creation workflow: {e}")
            await interaction.response.send_message(
                "❌ Event creation workflow not available. Please check bot configuration.",
                ephemeral=True
            )
            return
        
        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            await interaction.response.send_message(
                f"❌ Invalid URL: {url}\n"
                "Please provide a valid URL starting with http:// or https://",
                ephemeral=True
            )
            return
        
        # Acknowledge the interaction (this can take a while)
        await interaction.response.defer(thinking=True)
        
        try:
            # Get the server ID from the interaction
            server_id = str(interaction.guild.id) if interaction.guild else None
            
            # Run the workflow
            result = await create_discord_event_from_url(
                url=url,
                discord_server_id=server_id,
                quality_threshold=0.7,
                max_iterations=3,
            )
            
            if result.get("success") and result.get("discord_event_url"):
                event = result.get("event")
                event_title = event.title if event else "Event"
                event_url = result["discord_event_url"]
                
                message = f"✅ **Event Created!**\n\n"
                message += f"**{event_title}**\n"
                if event and event.date:
                    message += f"📅 {event.date}"
                    if event.start_time:
                        message += f" at {event.start_time}"
                    message += "\n"
                if event and event.get_full_location():
                    message += f"📍 {event.get_full_location()}\n"
                message += f"\n🔗 [View Event]({event_url})"
                
                await interaction.followup.send(message, ephemeral=False)
            else:
                # Build error message
                error_parts = ["❌ **Failed to create event**\n"]
                
                if result.get("event"):
                    event = result["event"]
                    error_parts.append(f"Extracted: {event.title}\n")
                
                if result.get("quality_score"):
                    qs = result["quality_score"]
                    error_parts.append(f"Quality: {qs['overall']:.2f}\n")
                
                errors = result.get("errors", [])
                if errors:
                    error_parts.append("\n**Errors:**")
                    for error in errors[:3]:  # Show first 3 errors
                        error_parts.append(f"- {error}")
                
                await interaction.followup.send(
                    "\n".join(error_parts),
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error in /add_event command: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error creating event: {str(e)}",
                ephemeral=True
            )
    
    # @mention handler
    @bot.event
    async def on_message(message: discord.Message):
        """Handle @mentions of the bot."""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Check if bot is mentioned
        if bot.user and bot.user.mentioned_in(message):
            # Extract Tumblr URL from message
            tumblr_url = extract_tumblr_url(message.content)
            
            if not tumblr_url:
                # No Tumblr URL found - send help message
                await message.channel.send(
                    f"👋 Hi {message.author.mention}! I can help you share Tumblr links.\n\n"
                    "**Usage:**\n"
                    f"- Mention me with a Tumblr URL: `@{bot.user.name} https://www.tumblr.com/soyeahbluesdance`\n"
                    f"- Use slash command: `/share_tumblr_link`\n\n"
                    "**Examples:**\n"
                    "- Blog URL: `https://www.tumblr.com/soyeahbluesdance`\n"
                    "- Post URL: `https://www.tumblr.com/soyeahbluesdance/1234567890/post-title`"
                )
                return
            
            # React to show we're processing
            await message.add_reaction("⏳")
            
            try:
                # Share the link
                success, response_message = await share_tumblr_link(
                    tumblr_url=tumblr_url,
                    channel=message.channel,
                    max_posts=1  # Default to 1 post for @mentions
                )
                
                # Remove processing reaction
                await message.remove_reaction("⏳", bot.user)
                
                if success:
                    await message.add_reaction("✅")
                else:
                    await message.add_reaction("❌")
                    # Send error message
                    await message.channel.send(
                        f"❌ {response_message}",
                        reference=message
                    )
            except Exception as e:
                logger.error(f"Error handling @mention: {e}", exc_info=True)
                await message.remove_reaction("⏳", bot.user)
                await message.add_reaction("❌")
                await message.channel.send(
                    f"❌ Error processing request: {str(e)}",
                    reference=message
                )
        
        # Process commands (for prefix commands if any)
        await bot.process_commands(message)
    
    logger.info("Discord bot handlers registered: @mentions, /share_tumblr_link, /add_event")

