"""Test extracting Tumblr post URLs from a blog feed."""

import asyncio
from src.mcp_ce.tools.tumblr.extract_post_urls import extract_post_urls

# Test URLs
TEST_BLOG_SOYEAH = "https://www.tumblr.com/soyeahbluesdance"
TEST_BLOG_OHYEAH = "https://ohyeahswingdance.tumblr.com"


async def test_extract_urls():
    """Test extracting post URLs from Tumblr blogs."""
    print("Testing Tumblr post URL extraction...")
    print()
    
    # Test 1: soyeahbluesdance
    print("=" * 70)
    print("Test 1: Extract from soyeahbluesdance")
    print("=" * 70)
    print(f"Blog URL: {TEST_BLOG_SOYEAH}")
    print()
    
    result = await extract_post_urls(
        tumblr_blog_url=TEST_BLOG_SOYEAH,
        max_posts=10,
        override_cache=True,  # Force fresh scrape
    )
    
    if result.is_success:
        print(f"✅ Success! Found {result.result['count']} post URLs")
        print(f"   Blog name: {result.result['blog_name']}")
        print()
        print("Post URLs:")
        for i, url in enumerate(result.result['post_urls'][:5], 1):  # Show first 5
            print(f"   {i}. {url}")
        if result.result['count'] > 5:
            print(f"   ... and {result.result['count'] - 5} more")
    else:
        print(f"❌ Failed: {result.error}")
    
    print()
    print()
    
    # Test 2: ohyeahswingdance
    print("=" * 70)
    print("Test 2: Extract from ohyeahswingdance")
    print("=" * 70)
    print(f"Blog URL: {TEST_BLOG_OHYEAH}")
    print()
    
    result = await extract_post_urls(
        tumblr_blog_url=TEST_BLOG_OHYEAH,
        max_posts=10,
        override_cache=True,
    )
    
    if result.is_success:
        print(f"✅ Success! Found {result.result['count']} post URLs")
        print(f"   Blog name: {result.result['blog_name']}")
        print()
        print("Post URLs:")
        for i, url in enumerate(result.result['post_urls'][:5], 1):
            print(f"   {i}. {url}")
        if result.result['count'] > 5:
            print(f"   ... and {result.result['count'] - 5} more")
    else:
        print(f"❌ Failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(test_extract_urls())

