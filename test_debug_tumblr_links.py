"""Debug what links are actually extracted from Tumblr pages."""

import asyncio
from src.mcp_ce.tools.crawl4ai.crawl_website import crawl_website
import json

TEST_BLOG = "https://www.tumblr.com/soyeahbluesdance"


async def debug_links():
    """Debug what links are extracted."""
    print("Debugging Tumblr link extraction...")
    print(f"Blog URL: {TEST_BLOG}")
    print()

    result = await crawl_website(
        url=TEST_BLOG,
        extract_images=False,
        extract_links=True,
        word_count_threshold=5,
        headless=True,
        override_cache=True,
    )

    if result.is_success:
        links = result.result.get("links", {})
        print(f"✅ Scraping successful")
        print(f"   Internal links: {len(links.get('internal', []))}")
        print(f"   External links: {len(links.get('external', []))}")
        print()

        # Show ALL links
        all_links = links.get("internal", []) + links.get("external", [])

        print(f"All {len(all_links)} links found:")
        print()
        for i, link in enumerate(all_links[:30], 1):  # Show first 30
            link_url = link if isinstance(link, str) else link.get("url", "")
            print(f"   {i}. {link_url}")

        if len(all_links) > 30:
            print(f"   ... and {len(all_links) - 30} more")

        # Show links containing "tumblr.com"
        tumblr_links = [
            link
            for link in all_links
            if "tumblr.com" in (link if isinstance(link, str) else link.get("url", ""))
        ]

        print()
        print(f"Links containing 'tumblr.com': {len(tumblr_links)}")
        for i, link in enumerate(tumblr_links[:20], 1):
            link_url = link if isinstance(link, str) else link.get("url", "")
            print(f"   {i}. {link_url}")

        # Check for post-like patterns
        print()
        print("Checking for post URL patterns...")
        post_patterns = []
        for link in tumblr_links:
            link_url = link if isinstance(link, str) else link.get("url", "")
            # Look for numeric IDs in URLs
            import re

            if re.search(r"/\d{9,}/", link_url):  # 9+ digit numbers
                post_patterns.append(link_url)

        print(f"Found {len(post_patterns)} URLs with numeric IDs (potential posts):")
        for i, url in enumerate(post_patterns[:10], 1):
            print(f"   {i}. {url}")
    else:
        print(f"❌ Failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(debug_links())
