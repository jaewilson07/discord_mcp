"""
DEPRECATED: This workflow is deprecated in favor of the simpler repost_tumblr tool.

Use `mcp_ce.tools.discord.repost_tumblr` instead, which:
- Automatically routes to correct Discord channels based on Tumblr blog
- Simply posts the URL (Discord auto-embeds)
- No complex extraction needed

This file is kept for reference only.
"""

from typing import Optional, Dict, Any
import asyncio
from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
from mcp_ce.agentic_tools.graphs.extract_strucured_data.extract_structured_data import (
    extract_structured_data,
)
from mcp_ce.models.tumblr import TumblrPost
from mcp_ce.tools.discord.send_message_with_image import send_message_with_image


async def repost_tumblr_to_discord(
    tumblr_url: str,
    discord_channel_id: str,
) -> Dict[str, Any]:
    """
    Simple repost: Extract image/GIF and caption from Tumblr post, post to Discord.
    
    This is a simplified workflow that:
    1. Scrapes the Tumblr post URL
    2. Extracts the image/GIF URL and caption
    3. Posts both to Discord (image auto-embeds, caption as text)
    
    Args:
        tumblr_url: Full Tumblr post URL (e.g., https://www.tumblr.com/soyeahbluesdance/777638063054651392/...)
        discord_channel_id: Discord channel ID to post to
    
    Returns:
        Dict with:
        - success: bool
        - image_url: str or None
        - caption: str or None
        - discord_message_id: str or None
        - errors: List[str]
    """
    result = {
        "success": False,
        "image_url": None,
        "caption": None,
        "discord_message_id": None,
        "errors": [],
    }
    
    try:
        # Step 1: Scrape the Tumblr post
        print(f"📡 Scraping Tumblr post: {tumblr_url}")
        scrape_result = await crawl_website(
            url=tumblr_url,
            extract_images=True,
            extract_links=False,
            word_count_threshold=5,
            headless=True,
        )
        
        # Handle ToolResponse
        is_success = scrape_result.get("success") if isinstance(scrape_result, dict) else (scrape_result.is_success if hasattr(scrape_result, 'is_success') else False)
        
        if not is_success:
            error_msg = scrape_result.get("error") if isinstance(scrape_result, dict) else (scrape_result.error if hasattr(scrape_result, 'error') else "Unknown error")
            result["errors"].append(f"Scraping failed: {error_msg}")
            return result
        
        # Extract content from ToolResponse
        scrape_data = scrape_result.get("result", {}) if isinstance(scrape_result, dict) else (scrape_result.result if hasattr(scrape_result, 'result') else {})
        
        content_markdown = scrape_data.get("content_markdown", "") or scrape_data.get("markdown", "")
        images = scrape_data.get("images", [])
        
        print(f"✅ Scraped {len(content_markdown)} characters, {len(images)} images")
        
        # Step 2: Extract image URL and caption using AI
        print(f"\n🤖 Extracting image and caption...")
        
        # Use structured extraction to get image and caption
        # We'll extract a simplified TumblrPost
        try:
            post = await extract_structured_data(
                text=content_markdown[:10000],  # Limit content size
                model_class=TumblrPost,
                instructions="""
Extract the image/GIF URL and caption from this Tumblr post.

Focus on:
1. The primary image or GIF URL (first image if multiple)
2. The caption/comment text from soyeahbluesdance (not reblog attribution)
3. The post ID from the URL

Ignore:
- Reblog attribution (unless it's the main content)
- Tags (unless they're part of the caption)
- Engagement metrics (likes, reblogs)
""",
            )
            
            result["image_url"] = post.image_url
            result["caption"] = post.caption
            
            print(f"✅ Extracted:")
            if post.image_url:
                print(f"   Image: {post.image_url[:60]}...")
            if post.caption:
                print(f"   Caption: {post.caption[:60]}...")
                
        except Exception as e:
            # Fallback: Try to extract from scraped content directly
            print(f"⚠️  AI extraction failed, trying fallback: {e}")
            
            # Use first image if available
            if images:
                # Images are dicts with 'src' key
                if isinstance(images[0], dict):
                    result["image_url"] = images[0].get("src") or images[0].get("url", "")
                else:
                    result["image_url"] = str(images[0])
            
            # Try to find caption in markdown (look for text after images)
            if content_markdown:
                # Simple heuristic: text after image URLs
                lines = content_markdown.split("\n")
                caption_lines = []
                found_image = False
                for line in lines:
                    if "http" in line and any(ext in line.lower() for ext in [".jpg", ".png", ".gif", ".webp"]):
                        found_image = True
                    elif found_image and line.strip() and not line.strip().startswith("#"):
                        caption_lines.append(line.strip())
                
                if caption_lines:
                    result["caption"] = "\n".join(caption_lines[:5])  # First 5 lines
        
        # Step 3: Post to Discord
        if result["image_url"] or result["caption"]:
            print(f"\n📤 Posting to Discord...")
            
            discord_result = await send_message_with_image(
                channel_id=discord_channel_id,
                content=result["caption"],
                image_url=result["image_url"],
            )
            
            if discord_result.is_success:
                result["discord_message_id"] = discord_result.result.message_id
                result["success"] = True
                print(f"✅ Posted to Discord!")
            else:
                result["errors"].append(f"Discord post failed: {discord_result.error}")
        else:
            result["errors"].append("No image or caption found to post")
        
        return result
        
    except Exception as e:
        result["errors"].append(f"Workflow error: {str(e)}")
        import traceback
        traceback.print_exc()
        return result


# Example usage
if __name__ == "__main__":
    async def test():
        result = await repost_tumblr_to_discord(
            tumblr_url="https://www.tumblr.com/soyeahbluesdance/777638063054651392/leaving-the-late-night",
            discord_channel_id="YOUR_CHANNEL_ID",
        )
        print(f"\nResult: {result}")
    
    asyncio.run(test())

