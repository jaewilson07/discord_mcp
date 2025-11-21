"""
Simple test for Tumblr repost - just test scraping and extraction first.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
from mcp_ce.agentic_tools.graphs.extract_strucured_data.extract_structured_data import (
    extract_structured_data,
)
from mcp_ce.models.tumblr import TumblrPost


async def test_scraping_and_extraction():
    """Test just the scraping and extraction parts."""
    
    TEST_URL = "https://www.tumblr.com/soyeahbluesdance/777638063054651392/leaving-the-late-night"
    
    print("=" * 70)
    print("Tumblr Scraping & Extraction Test")
    print("=" * 70)
    print()
    print(f"📡 Testing URL: {TEST_URL}")
    print()
    
    # Step 1: Scrape
    print("Step 1: Scraping...")
    scrape_result = await crawl_website(
        url=TEST_URL,
        extract_images=True,
        extract_links=False,
        word_count_threshold=5,
        headless=True,
    )
    
    # Handle ToolResponse
    is_success = scrape_result.get("success") if isinstance(scrape_result, dict) else (scrape_result.is_success if hasattr(scrape_result, 'is_success') else False)
    
    if not is_success:
        error_msg = scrape_result.get("error") if isinstance(scrape_result, dict) else (scrape_result.error if hasattr(scrape_result, 'error') else "Unknown error")
        print(f"❌ Scraping failed: {error_msg}")
        return
    
    # Extract data
    scrape_data = scrape_result.get("result", {}) if isinstance(scrape_result, dict) else (scrape_result.result if hasattr(scrape_result, 'result') else {})
    
    content_markdown = scrape_data.get("content_markdown", "") or scrape_data.get("markdown", "")
    images = scrape_data.get("images", [])
    
    print(f"✅ Scraped {len(content_markdown)} characters")
    print(f"✅ Found {len(images)} images")
    
    if images:
        print(f"\n📸 First image:")
        if isinstance(images[0], dict):
            print(f"   URL: {images[0].get('src', images[0].get('url', 'N/A'))}")
            print(f"   Alt: {images[0].get('alt', 'N/A')}")
        else:
            print(f"   URL: {images[0]}")
    
    print(f"\n📄 Content preview (first 500 chars):")
    print(content_markdown[:500])
    print("...")
    
    # Step 2: Extract
    print(f"\nStep 2: Extracting with AI...")
    try:
        post = await extract_structured_data(
            text=content_markdown[:10000],
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
        
        print(f"✅ Extraction successful!")
        print(f"\n📊 Extracted Data:")
        print(f"   Post ID: {post.post_id}")
        print(f"   Image URL: {post.image_url or 'None'}")
        print(f"   Caption: {post.caption[:100] if post.caption else 'None'}...")
        print(f"   Post URL: {post.post_url}")
        print(f"   Timestamp: {post.timestamp}")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_scraping_and_extraction())

