"""Sync Tumblr feed to Discord channel workflow."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio


async def sync_tumblr_feed(
    tumblr_url: str = "https://www.tumblr.com/soyeahbluesdance",
    discord_channel_id: Optional[str] = None,
    discord_server_id: Optional[str] = None,
    supabase_source: str = "tumblr_feed",
    max_posts: int = 10,
    check_duplicates: bool = True,
) -> Dict[str, Any]:
    """
    Sync Tumblr feed to Discord channel.
    
    This workflow:
    1. Scrapes the Tumblr feed using crawl4ai
    2. Extracts posts (images, GIFs, text, reblogs) using extraction agent
    3. Checks for duplicates in Supabase
    4. Stores new posts in Supabase
    5. Posts new content to Discord channel
    
    Args:
        tumblr_url: Tumblr blog URL (default: soyeahbluesdance)
        discord_channel_id: Discord channel ID to post to
        discord_server_id: Discord server ID (optional)
        supabase_source: Supabase source name for storage
        max_posts: Maximum number of posts to process
        check_duplicates: Whether to check for duplicate posts
    
    Returns:
        Dictionary with sync results:
        - success: bool
        - posts_scraped: int
        - posts_extracted: int
        - posts_new: int
        - posts_posted: int
        - errors: List[str]
    """
    results = {
        "success": False,
        "posts_scraped": 0,
        "posts_extracted": 0,
        "posts_new": 0,
        "posts_posted": 0,
        "errors": [],
    }
    
    try:
        # Step 1: Scrape Tumblr feed
        print(f"📡 Step 1: Scraping Tumblr feed: {tumblr_url}")
        
        # Use MCP tools via runtime
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
        
        from mcp_ce.runtime import create_tool_proxy
        
        crawl_website = create_tool_proxy("crawl4ai", "crawl_website")
        
        scrape_result = await crawl_website(
            url=tumblr_url,
            extract_images=True,
            extract_links=True,
            word_count_threshold=5,
            headless=True,
            js_code="window.scrollTo(0, document.body.scrollHeight); setTimeout(() => {}, 2000);",
            wait_for_selector="article",
        )
        
        if not scrape_result.is_success:
            results["errors"].append(f"Scraping failed: {scrape_result.error}")
            return results
        
        content = scrape_result.result.get("content_markdown", "")
        images = scrape_result.result.get("images", [])
        
        print(f"✅ Scraped {len(content)} characters, {len(images)} images")
        results["posts_scraped"] = 1
        
        # Step 2: Extract posts using extraction agent
        print(f"\n🤖 Step 2: Extracting posts from content...")
        
        extraction_agent = create_tool_proxy("agents", "extraction_agent")
        
        # Register Tumblr post schema (would need to be done in agent registry)
        # For now, use generic extraction
        extraction_result = await extraction_agent(
            content=content[:50000],  # Limit content size
            extraction_type="generic",
            context={
                "url": tumblr_url,
                "max_posts": max_posts,
                "post_type": "tumblr",
            },
        )
        
        if not extraction_result.is_success:
            results["errors"].append(f"Extraction failed: {extraction_result.error}")
            return results
        
        # Parse extracted items
        items = extraction_result.result.items if hasattr(extraction_result.result, 'items') else []
        posts = items[:max_posts] if isinstance(items, list) else []
        
        print(f"✅ Extracted {len(posts)} posts")
        results["posts_extracted"] = len(posts)
        
        # Step 3: Check duplicates and store in Supabase
        if check_duplicates:
            print(f"\n📦 Step 3: Checking for duplicates in Supabase...")
        
        search_documents = create_tool_proxy("supabase", "search_documents")
        add_document = create_tool_proxy("supabase", "add_document")
        
        new_posts = []
        for i, post in enumerate(posts):
            post_id = post.get("post_id") or post.get("url", f"post_{i}")
            
            if check_duplicates:
                # Check if post already exists
                search_result = await search_documents(
                    source=supabase_source,
                    query=f"post_id:{post_id}",
                    limit=1,
                )
                
                if search_result.is_success and search_result.result.get("documents"):
                    print(f"   ⏭️  Skipping duplicate: {post_id}")
                    continue  # Skip duplicate
            
            # Store in Supabase
            post_content = post.get("content", "") or post.get("text", "") or str(post)
            metadata = {
                "post_id": post_id,
                "post_type": post.get("post_type", "unknown"),
                "image_urls": post.get("image_urls", []),
                "original_poster": post.get("original_poster"),
                "post_url": post.get("post_url") or post.get("url", tumblr_url),
                "timestamp": post.get("timestamp", datetime.now().isoformat()),
                "tags": post.get("tags", []),
            }
            
            doc_result = await add_document(
                source=supabase_source,
                content=post_content,
                metadata=metadata,
            )
            
            if doc_result.is_success:
                new_posts.append(post)
                results["posts_new"] += 1
                print(f"   ✅ Stored new post: {post_id}")
            else:
                results["errors"].append(f"Failed to store {post_id}: {doc_result.error}")
        
        # Step 4: Post to Discord (simple repost: image + caption)
        if discord_channel_id and new_posts:
            print(f"\n📤 Step 4: Reposting {len(new_posts)} posts to Discord...")
            
            for post in new_posts:
                # Extract image/GIF URL (first image if multiple)
                image_url = None
                if post.get("image_url"):
                    image_url = post["image_url"]
                elif post.get("image_urls") and len(post["image_urls"]) > 0:
                    image_url = post["image_urls"][0]
                elif post.get("all_image_urls") and len(post["all_image_urls"]) > 0:
                    image_url = post["all_image_urls"][0]
                
                # Extract caption
                caption = post.get("caption") or post.get("content") or post.get("text")
                
                # Only post if we have an image or caption
                if image_url or caption:
                    success = await _post_to_discord(
                        channel_id=discord_channel_id,
                        image_url=image_url,
                        caption=caption,
                    )
                    
                    if success:
                        results["posts_posted"] += 1
                        print(f"   ✅ Reposted: {post.get('post_id', 'unknown')}")
                        if image_url:
                            print(f"      Image: {image_url[:50]}...")
                        if caption:
                            print(f"      Caption: {caption[:50]}...")
                    else:
                        results["errors"].append(f"Failed to post {post.get('post_id')}")
                else:
                    print(f"   ⏭️  Skipping post {post.get('post_id')}: no image or caption")
                
                # Rate limiting - wait between posts
                await asyncio.sleep(1)
        else:
            if not discord_channel_id:
                print(f"\n⚠️  No Discord channel ID provided, skipping posting")
            else:
                print(f"\n⚠️  No new posts to post")
        
        results["success"] = True
        print(f"\n✅ Sync complete: {results['posts_posted']} posts posted, {len(results['errors'])} errors")
        return results
        
    except Exception as e:
        error_msg = f"Workflow error: {str(e)}"
        results["errors"].append(error_msg)
        print(f"\n❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return results


async def _post_to_discord(
    channel_id: str,
    image_url: Optional[str],
    caption: Optional[str],
) -> bool:
    """
    Post image/GIF and caption to Discord.
    
    Simple repost: Send the image URL (auto-embedded) with the caption.
    """
    from mcp_ce.runtime import create_tool_proxy
    
    send_message_with_image = create_tool_proxy("discord", "send_message_with_image")
    
    result = await send_message_with_image(
        channel_id=channel_id,
        content=caption,
        image_url=image_url,
    )
    
    return result.is_success if hasattr(result, 'is_success') else False


# Example usage
if __name__ == "__main__":
    async def main():
        result = await sync_tumblr_feed(
            tumblr_url="https://www.tumblr.com/soyeahbluesdance",
            discord_channel_id=None,  # Set your channel ID
            max_posts=5,
        )
        print(f"\nResults: {result}")
    
    asyncio.run(main())

