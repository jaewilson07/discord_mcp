"""
Extract Tumblr post URLs from a blog feed.

Scrapes a Tumblr blog URL and extracts all post URLs (share links).
"""

import re
from typing import List, Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.crawl4ai.crawl_website import crawl_website


def extract_blog_name_from_url(tumblr_url: str) -> Optional[str]:
    """
    Extract blog name from Tumblr URL.
    
    Examples:
        https://www.tumblr.com/soyeahbluesdance → "soyeahbluesdance"
        https://ohyeahswingdance.tumblr.com → "ohyeahswingdance"
    """
    # Pattern 1: blogname.tumblr.com (subdomain format)
    match = re.search(r"([a-zA-Z0-9-]+)\.tumblr\.com", tumblr_url)
    if match:
        blog_name = match.group(1)
        if blog_name != "www":
            return blog_name
    
    # Pattern 2: www.tumblr.com/blogname (path format)
    match = re.search(r"tumblr\.com/([a-zA-Z0-9-]+)", tumblr_url)
    if match:
        blog_name = match.group(1)
        skip_words = ["post", "reblog", "tagged", "search", "www"]
        if blog_name not in skip_words:
            return blog_name
    
    return None


def is_tumblr_post_url(url: str, blog_name: Optional[str] = None) -> bool:
    """
    Check if a URL is a Tumblr post URL.
    
    Post URLs have formats like:
    - https://www.tumblr.com/blogname/1234567890/post-title
    - https://blogname.tumblr.com/post/1234567890/post-title
    
    Args:
        url: URL to check
        blog_name: Optional blog name to filter by specific blog
    
    Returns:
        True if URL looks like a Tumblr post URL
    """
    if not url or "tumblr.com" not in url:
        return False
    
    # Pattern 1: www.tumblr.com/blogname/numeric-id/...
    match = re.search(r"tumblr\.com/([^/]+)/(\d+)/", url)
    if match:
        url_blog_name = match.group(1)
        post_id = match.group(2)
        # Check if it's a numeric post ID (Tumblr post IDs are numeric)
        if post_id.isdigit() and len(post_id) >= 9:  # Tumblr post IDs are typically 10+ digits
            if blog_name is None or url_blog_name == blog_name:
                return True
    
    # Pattern 2: blogname.tumblr.com/post/numeric-id/...
    match = re.search(r"([^.]+)\.tumblr\.com/post/(\d+)/", url)
    if match:
        url_blog_name = match.group(1)
        post_id = match.group(2)
        if post_id.isdigit() and len(post_id) >= 9:
            if blog_name is None or url_blog_name == blog_name:
                return True
    
    return False


@register_command("tumblr", "extract_post_urls")
async def extract_post_urls(
    tumblr_blog_url: str,
    max_posts: int = 20,
    override_cache: bool = False,
) -> ToolResponse:
    """
    Extract Tumblr post URLs (share links) from a blog feed.
    
    Scrapes the Tumblr blog page and extracts all post URLs that can be shared.
    
    Args:
        tumblr_blog_url: Tumblr blog URL (e.g., https://www.tumblr.com/soyeahbluesdance)
        max_posts: Maximum number of post URLs to extract (default: 20)
        override_cache: Whether to bypass cache and force fresh scrape (default: False)
    
    Returns:
        ToolResponse containing:
        - blog_name: Extracted blog name
        - post_urls: List of post URLs found
        - count: Number of post URLs found
        - blog_url: Original blog URL
    """
    try:
        # Extract blog name for filtering
        blog_name = extract_blog_name_from_url(tumblr_blog_url)
        
        if not blog_name:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"Could not extract blog name from URL: {tumblr_blog_url}",
            )
        
        # Scrape the Tumblr blog page
        # Tumblr uses infinite scroll, so we need to:
        # 1. Use scan_full_page to auto-scroll and load dynamic content
        # 2. Wait for content to load using a simple selector
        # 3. Extract links from both the links dict and markdown content
        
        # Note: crawl_website doesn't directly support VirtualScrollConfig,
        # but we can use scan_full_page via js_code or wait for content
        # For now, use js_code with scrolling and wait_for with a simple selector
        
        scrape_result = await crawl_website(
            url=tumblr_blog_url,
            extract_images=False,
            extract_links=True,  # We need links to find post URLs
            word_count_threshold=5,
            headless=True,
            wait_for_selector="body",  # Simple wait - Tumblr loads dynamically
            js_code="""
            // Wait for initial load
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Scroll multiple times to trigger infinite scroll
            for (let i = 0; i < 10; i++) {
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(resolve => setTimeout(resolve, 1500));
            }
            
            // Final wait for content to settle
            await new Promise(resolve => setTimeout(resolve, 2000));
            """,
            override_cache=override_cache,
        )
        
        if not scrape_result.is_success:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"Failed to scrape Tumblr blog: {scrape_result.error}",
            )
        
        # Extract links from scrape result
        scrape_data = scrape_result.result
        links = scrape_data.get("links", {})
        content_markdown = scrape_data.get("content_markdown", "")
        
        # Method 1: Extract from links dict
        all_links = []
        for link_list in links.values():
            if isinstance(link_list, list):
                all_links.extend(link_list)
        
        # Method 2: Extract from markdown content (Tumblr URLs might be in text)
        # Look for URLs in markdown content
        import re
        url_pattern = r'https?://[^\s\)]+tumblr\.com[^\s\)]+'
        markdown_urls = re.findall(url_pattern, content_markdown)
        all_links.extend(markdown_urls)
        
        # Filter for Tumblr post URLs
        post_urls = []
        seen_urls = set()  # Deduplicate
        
        for link in all_links:
            # Handle different link formats (string or dict)
            link_url = link if isinstance(link, str) else (link.get("url", "") if isinstance(link, dict) else "")
            
            if link_url and is_tumblr_post_url(link_url, blog_name):
                # Normalize URL (remove query params, fragments)
                normalized_url = link_url.split("?")[0].split("#")[0]
                
                if normalized_url not in seen_urls:
                    seen_urls.add(normalized_url)
                    post_urls.append(normalized_url)
                    
                    if len(post_urls) >= max_posts:
                        break
        
        result = {
            "blog_name": blog_name,
            "post_urls": post_urls,
            "count": len(post_urls),
            "blog_url": tumblr_blog_url,
        }
        
        return ToolResponse(is_success=True, result=result)
        
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Error extracting post URLs: {str(e)}",
        )

