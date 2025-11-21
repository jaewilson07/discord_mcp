"""
Simple Tumblr repost to Discord - just share the URLs!

DEPRECATED: For single URLs, use `mcp_ce.tools.discord.repost_tumblr` instead.
This file is kept for batch operations only.

Takes Tumblr post URLs and posts them to Discord.
Discord will auto-embed/preview the links.
"""

from typing import Optional, List, Dict, Any
import asyncio
from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
from mcp_ce.tools.discord.repost_tumblr import repost_tumblr


async def repost_tumblr_urls_to_discord(
    tumblr_urls: List[str],
    discord_channel_id: str,
) -> Dict[str, Any]:
    """
    Simple repost: Post Tumblr URLs to Discord (Discord auto-embeds them).
    
    Args:
        tumblr_urls: List of Tumblr post URLs to share
        discord_channel_id: Discord channel ID to post to
    
    Returns:
        Dict with:
        - success: bool
        - posts_posted: int
        - errors: List[str]
    """
    result = {
        "success": False,
        "posts_posted": 0,
        "errors": [],
    }
    
    try:
        print(f"📤 Posting {len(tumblr_urls)} Tumblr URLs to Discord...")
        print()
        
        for i, url in enumerate(tumblr_urls, 1):
            print(f"[{i}/{len(tumblr_urls)}] Posting: {url}")
            
            # Use repost_tumblr tool (handles channel routing automatically)
            # Note: This ignores the provided discord_channel_id and uses routing instead
            discord_result = await repost_tumblr(
                tumblr_url=url,
                dev_mode=False,  # Use PROD channels
            )
            
            if discord_result.is_success:
                result["posts_posted"] += 1
                print(f"   ✅ Posted!")
            else:
                error_msg = f"Failed to post {url}: {discord_result.error}"
                result["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
            
            # Rate limiting - wait between posts
            if i < len(tumblr_urls):
                await asyncio.sleep(1)
        
        result["success"] = result["posts_posted"] > 0
        print(f"\n✅ Posted {result['posts_posted']}/{len(tumblr_urls)} URLs")
        
        return result
        
    except Exception as e:
        result["errors"].append(f"Workflow error: {str(e)}")
        import traceback
        traceback.print_exc()
        return result


async def extract_tumblr_post_urls(
    tumblr_feed_url: str = "https://www.tumblr.com/soyeahbluesdance",
    max_posts: int = 10,
) -> List[str]:
    """
    Extract Tumblr post URLs from a feed.
    
    Args:
        tumblr_feed_url: Tumblr blog URL
        max_posts: Maximum number of post URLs to extract
    
    Returns:
        List of Tumblr post URLs
    """
    print(f"📡 Scraping Tumblr feed: {tumblr_feed_url}")
    
    scrape_result = await crawl_website(
        url=tumblr_feed_url,
        extract_images=False,
        extract_links=True,  # We need links to find post URLs
        word_count_threshold=5,
        headless=True,
    )
    
    # Handle ToolResponse
    is_success = scrape_result.get("success") if isinstance(scrape_result, dict) else (scrape_result.is_success if hasattr(scrape_result, 'is_success') else False)
    
    if not is_success:
        error_msg = scrape_result.get("error") if isinstance(scrape_result, dict) else (scrape_result.error if hasattr(scrape_result, 'error') else "Unknown error")
        print(f"❌ Scraping failed: {error_msg}")
        return []
    
    # Extract links
    scrape_data = scrape_result.get("result", {}) if isinstance(scrape_result, dict) else (scrape_result.result if hasattr(scrape_result, 'result') else {})
    links = scrape_data.get("links", {})
    
    # Find Tumblr post URLs (format: https://www.tumblr.com/soyeahbluesdance/1234567890/...)
    post_urls = []
    all_links = links.get("internal", []) + links.get("external", [])
    
    for link in all_links:
        link_url = link if isinstance(link, str) else (link.get("url", "") if isinstance(link, dict) else "")
        if link_url and "tumblr.com/soyeahbluesdance/" in link_url and "/" in link_url.split("soyeahbluesdance/")[-1]:
            # This looks like a post URL
            if link_url not in post_urls:
                post_urls.append(link_url)
                if len(post_urls) >= max_posts:
                    break
    
    print(f"✅ Found {len(post_urls)} post URLs")
    return post_urls


async def sync_tumblr_feed_simple(
    tumblr_feed_url: str = "https://www.tumblr.com/soyeahbluesdance",
    discord_channel_id: Optional[str] = None,
    max_posts: int = 10,
    check_duplicates: bool = True,
) -> Dict[str, Any]:
    """
    Simple Tumblr feed sync: Extract post URLs and share to Discord.
    
    Workflow:
    1. Scrape Tumblr feed
    2. Extract post URLs
    3. Check for duplicates (optional)
    4. Post URLs to Discord (Discord auto-embeds)
    
    Args:
        tumblr_feed_url: Tumblr blog URL
        discord_channel_id: Discord channel ID to post to
        max_posts: Maximum number of posts to process
        check_duplicates: Whether to check Supabase for already-posted URLs
    
    Returns:
        Dict with results
    """
    result = {
        "success": False,
        "urls_found": 0,
        "urls_posted": 0,
        "errors": [],
    }
    
    try:
        # Step 1: Extract post URLs
        print(f"🔍 Step 1: Extracting post URLs from feed...")
        post_urls = await extract_tumblr_post_urls(
            tumblr_feed_url=tumblr_feed_url,
            max_posts=max_posts,
        )
        
        result["urls_found"] = len(post_urls)
        
        if not post_urls:
            result["errors"].append("No post URLs found")
            return result
        
        # Step 2: Check duplicates (optional)
        new_urls = post_urls
        if check_duplicates:
            print(f"\n🔍 Step 2: Checking for duplicates...")
            from mcp_ce.tools.supabase.check_tumblr_post_duplicate import (
                check_tumblr_post_duplicate,
            )
            
            new_urls = []
            for url in post_urls:
                # Extract post ID from URL
                post_id = url.split("/soyeahbluesdance/")[-1].split("/")[0] if "/soyeahbluesdance/" in url else url.split("/")[-1]
                
                duplicate_result = await check_tumblr_post_duplicate(
                    post_id=post_id,
                    table_name="tumblr_posts",
                )
                
                if duplicate_result.is_success and not duplicate_result.result.get("exists"):
                    new_urls.append(url)
                else:
                    print(f"   ⏭️  Skipping duplicate: {post_id}")
            
            print(f"✅ {len(new_urls)} new posts to share")
        
        # Step 3: Post to Discord
        if discord_channel_id and new_urls:
            print(f"\n📤 Step 3: Posting {len(new_urls)} URLs to Discord...")
            repost_result = await repost_tumblr_urls_to_discord(
                tumblr_urls=new_urls,
                discord_channel_id=discord_channel_id,
            )
            
            result["urls_posted"] = repost_result["posts_posted"]
            result["errors"].extend(repost_result.get("errors", []))
        else:
            if not discord_channel_id:
                result["errors"].append("No Discord channel ID provided")
            else:
                result["errors"].append("No new URLs to post")
        
        result["success"] = result["urls_posted"] > 0
        return result
        
    except Exception as e:
        result["errors"].append(f"Workflow error: {str(e)}")
        import traceback
        traceback.print_exc()
        return result


# Example usage
if __name__ == "__main__":
    async def test():
        # Test with a single URL
        result = await repost_tumblr_urls_to_discord(
            tumblr_urls=[
                "https://www.tumblr.com/soyeahbluesdance/777638063054651392/leaving-the-late-night",
            ],
            discord_channel_id="YOUR_CHANNEL_ID",
        )
        print(f"\nResult: {result}")
    
    asyncio.run(test())

