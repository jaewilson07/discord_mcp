"""
Daily cron job to sync Tumblr feeds to Discord.

This workflow:
1. Extracts post URLs from configured Tumblr blogs
2. Checks Supabase for duplicates
3. Stores new posts in Supabase
4. Reposts new posts to Discord (with automatic channel routing)

Designed to run once per day via cron or scheduler.
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from mcp_ce.tools.tumblr.extract_post_urls import extract_post_urls
from mcp_ce.tools.discord.repost_tumblr import repost_tumblr
from mcp_ce.tools.supabase.check_tumblr_post_duplicate import check_tumblr_post_duplicate
from mcp_ce.tools.supabase.store_tumblr_post_url import store_tumblr_post_url


# Configure which blogs to sync
TUMBLR_BLOGS = [
    {
        "url": "https://www.tumblr.com/soyeahbluesdance",
        "name": "soyeahbluesdance",
    },
    {
        "url": "https://ohyeahswingdance.tumblr.com",
        "name": "ohyeahswingdance",
    },
]


async def daily_sync_tumblr_to_discord(
    blogs: Optional[List[Dict[str, str]]] = None,
    max_posts_per_blog: int = 20,
    dev_mode: bool = False,
) -> Dict[str, Any]:
    """
    Daily sync workflow: Extract Tumblr posts and repost new ones to Discord.
    
    This is designed to run as a cron job once per day.
    
    Args:
        blogs: List of blog configs with 'url' and 'name'. Defaults to TUMBLR_BLOGS.
        max_posts_per_blog: Maximum number of posts to extract per blog (default: 20)
        dev_mode: If True, use DEV Discord channels (default: False, uses PROD)
    
    Returns:
        Dict with sync results:
        - success: bool
        - blogs_processed: int
        - total_posts_found: int
        - new_posts: int
        - posts_posted: int
        - errors: List[str]
        - blog_results: List[Dict] with per-blog results
    """
    if blogs is None:
        blogs = TUMBLR_BLOGS
    
    result = {
        "success": False,
        "blogs_processed": 0,
        "total_posts_found": 0,
        "new_posts": 0,
        "posts_posted": 0,
        "errors": [],
        "blog_results": [],
        "started_at": datetime.now().isoformat(),
    }
    
    try:
        print(f"🔄 Starting daily Tumblr sync at {result['started_at']}")
        print(f"📋 Processing {len(blogs)} blog(s)")
        print()
        
        for blog_config in blogs:
            blog_url = blog_config["url"]
            blog_name = blog_config.get("name", "unknown")
            
            print(f"📖 Processing blog: {blog_name}")
            print(f"   URL: {blog_url}")
            
            blog_result = {
                "blog_name": blog_name,
                "blog_url": blog_url,
                "posts_found": 0,
                "new_posts": 0,
                "posts_posted": 0,
                "errors": [],
            }
            
            try:
                # Step 1: Extract post URLs from blog
                print(f"   🔍 Extracting post URLs...")
                extract_result = await extract_post_urls(
                    tumblr_blog_url=blog_url,
                    max_posts=max_posts_per_blog,
                    override_cache=True,  # Always get fresh content
                )
                
                if not extract_result.is_success:
                    error_msg = f"Failed to extract posts from {blog_name}: {extract_result.error}"
                    blog_result["errors"].append(error_msg)
                    result["errors"].append(error_msg)
                    print(f"   ❌ {error_msg}")
                    result["blog_results"].append(blog_result)
                    continue
                
                post_urls = extract_result.result.get("post_urls", [])
                blog_result["posts_found"] = len(post_urls)
                result["total_posts_found"] += len(post_urls)
                
                print(f"   ✅ Found {len(post_urls)} post URLs")
                
                if not post_urls:
                    print(f"   ⏭️  No posts found, skipping")
                    result["blog_results"].append(blog_result)
                    continue
                
                # Step 2: Check for duplicates and store new posts
                print(f"   🔍 Checking for duplicates...")
                new_post_urls = []
                
                for post_url in post_urls:
                    # Extract post_id from URL
                    import re
                    match = re.search(r"tumblr\.com/[^/]+/(\d+)/", post_url)
                    if not match:
                        continue
                    post_id = match.group(1)
                    
                    # Check if already exists
                    duplicate_check = await check_tumblr_post_duplicate(
                        post_id=post_id,
                        table_name="tumblr_posts",
                    )
                    
                    if duplicate_check.is_success and duplicate_check.result.get("exists"):
                        # Already posted, skip
                        continue
                    
                    # Store in Supabase (new post)
                    store_result = await store_tumblr_post_url(
                        post_url=post_url,
                        post_id=post_id,
                        blog_name=blog_name,
                        table_name="tumblr_posts",
                    )
                    
                    if store_result.is_success and store_result.result.get("is_new"):
                        new_post_urls.append(post_url)
                        blog_result["new_posts"] += 1
                        result["new_posts"] += 1
                
                print(f"   ✅ {len(new_post_urls)} new posts to repost")
                
                # Step 3: Repost new posts to Discord
                if new_post_urls:
                    print(f"   📤 Posting {len(new_post_urls)} new posts to Discord...")
                    
                    for post_url in new_post_urls:
                        repost_result = await repost_tumblr(
                            tumblr_url=post_url,
                            dev_mode=dev_mode,
                        )
                        
                        if repost_result.is_success:
                            blog_result["posts_posted"] += 1
                            result["posts_posted"] += 1
                            print(f"      ✅ Posted: {post_url[:60]}...")
                        else:
                            error_msg = f"Failed to post {post_url}: {repost_result.error}"
                            blog_result["errors"].append(error_msg)
                            result["errors"].append(error_msg)
                            print(f"      ❌ {error_msg}")
                        
                        # Rate limiting - wait between posts
                        await asyncio.sleep(2)
                
                result["blogs_processed"] += 1
                print(f"   ✅ Completed: {blog_result['posts_posted']} posts posted")
                
            except Exception as e:
                error_msg = f"Error processing blog {blog_name}: {str(e)}"
                blog_result["errors"].append(error_msg)
                result["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
                import traceback
                traceback.print_exc()
            
            result["blog_results"].append(blog_result)
            print()
        
        result["success"] = result["posts_posted"] > 0 or result["total_posts_found"] == 0
        result["completed_at"] = datetime.now().isoformat()
        
        print("=" * 70)
        print("📊 Sync Summary")
        print("=" * 70)
        print(f"Blogs processed: {result['blogs_processed']}/{len(blogs)}")
        print(f"Total posts found: {result['total_posts_found']}")
        print(f"New posts: {result['new_posts']}")
        print(f"Posts posted to Discord: {result['posts_posted']}")
        if result["errors"]:
            print(f"Errors: {len(result['errors'])}")
        print()
        
        return result
        
    except Exception as e:
        result["errors"].append(f"Workflow error: {str(e)}")
        result["completed_at"] = datetime.now().isoformat()
        import traceback
        traceback.print_exc()
        return result


# For running as a script
if __name__ == "__main__":
    async def main():
        result = await daily_sync_tumblr_to_discord(
            dev_mode=False,  # Set to True for testing
        )
        print("\nFinal result:", result)
    
    asyncio.run(main())

