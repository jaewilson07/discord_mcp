"""
Test Scrape Date functionality
"""

import asyncio
from datetime import datetime


async def test_scrape_date():
    """Test that Scrape Date is properly set when saving to Notion"""

    print("🧪 Testing Scrape Date functionality\n")

    # Test 1: Check cache with scrape date
    print("1️⃣  Testing cache checker with Scrape Date...")
dw    from mcp_ce.cache import check_url_in_notion as check_notion_cache

    test_url = "https://www.bluesmuse.dance/"
    cached = await check_notion_cache(test_url, max_age_hours=24)

    if cached:
        print(f"   ✅ Found cached page")
        print(f"   Scrape Date: {cached.get('scrape_date', 'N/A')}")
        print(f"   Age: {cached.get('age_hours', 0):.2f} hours")
        print(f"   Last Edited: {cached.get('last_edited', 'N/A')}")
    else:
        print(f"   ℹ️ No cache found (will be created on next scrape)")

    # Test 2: Scrape and save with Scrape Date
    print(f"\n2️⃣  Testing scrape with Scrape Date...")
    from mcp_ce.tools.crawl4ai.crawl_website import crawl_website

    result = await crawl_website(
        url=test_url,
        extract_images=False,
        extract_links=False,
        headless=True,
        save_to_notion=True,
    )

    if result.get("success"):
        print(f"   ✅ Scrape successful")
        notion_result = result.get("notion", {})
        if notion_result.get("success"):
            action = notion_result.get("action", "unknown")
            print(f"   ✅ Notion {action}")
            print(f"   Page ID: {notion_result.get('page_id', 'N/A')}")
            print(f"   Scrape Date should be set to: {datetime.now().isoformat()}")
        else:
            print(f"   ❌ Notion save failed: {notion_result.get('error')}")
    else:
        print(f"   ❌ Scrape failed: {result.get('error')}")

    # Test 3: Verify cache now shows updated scrape date
    print(f"\n3️⃣  Verifying updated cache...")
    cached_after = await check_notion_cache(test_url, max_age_hours=24)

    if cached_after:
        print(f"   ✅ Cache updated")
        print(f"   New Scrape Date: {cached_after.get('scrape_date', 'N/A')}")
        print(f"   Age: {cached_after.get('age_hours', 0):.2f} hours")

        # Should be very fresh (< 1 minute)
        if cached_after.get("age_hours", 999) < 0.017:  # < 1 minute
            print(f"   ✅ Scrape Date is fresh!")
        else:
            print(f"   ⚠️ Scrape Date seems old")
    else:
        print(f"   ❌ Cache not found after scrape")

    print(f"\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_scrape_date())
