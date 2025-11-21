"""
Test deep crawl functionality - crawl multiple pages and cache in Notion
"""

import asyncio
from datetime import datetime


async def test_deep_crawl():
    """
    Test deep crawling of a website with multiple pages.

    Success criteria:
    - Multiple pages crawled (> 1)
    - All pages saved to Notion
    - Scrape Date set on all pages
    - Cache detection working for all pages
    """

    url = "https://www.bluesmuse.dance/"

    print("Deep Crawl Test")
    print(f"URL: {url}")
    print(f"Time: {datetime.now().isoformat()}\n")

    # Step 1: Perform deep crawl
    print("=" * 70)
    print("STEP 1: Deep Crawl Website")
    print("=" * 70)

    from mcp_ce.tools.crawl4ai.deep_crawl import deep_crawl_website

    try:
        result = await deep_crawl_website(
            url=url,
            max_depth=2,  # Crawl 2 levels deep
            max_pages=10,  # Limit to 10 pages
            save_to_notion=True,  # Save all pages to Notion
            include_external=False,  # Only same domain
        )

        if result.get("success"):
            pages_crawled = result.get("pages_crawled", 0)
            pages = result.get("pages", [])

            print(f"\n✅ Deep crawl complete!")
            print(f"   Pages crawled: {pages_crawled}")
            print(f"   Time taken: {result.get('time_taken', 0):.2f}s")

            if pages_crawled > 1:
                print(f"\n✅ SUCCESS: Multiple pages crawled ({pages_crawled})")
            else:
                print(f"\n⚠️ Only {pages_crawled} page(s) crawled")

            print(f"\n📄 Pages found:")
            for i, page in enumerate(pages[:10], 1):
                page_url = page.get("url", "N/A")
                title = page.get("title", "Untitled")
                notion_saved = "✅" if page.get("notion_saved") else "❌"
                print(f"   {i}. {notion_saved} {title}")
                print(f"      {page_url}")

        else:
            print(f"\n❌ Deep crawl failed: {result.get('error')}")
            return

    except Exception as e:
        print(f"\n❌ Deep crawl error: {e}")
        import traceback

        traceback.print_exc()
        return

    # Step 2: Verify all pages in Notion cache
    print(f"\n{'='*70}")
    print("STEP 2: Verify Notion Cache")
    print("=" * 70)

    from mcp_ce.cache import check_url_in_notion as check_notion_cache

    print(f"\nChecking cache for all crawled pages...\n")

    cached_count = 0
    fresh_count = 0
    stale_count = 0
    missing_count = 0

    for i, page in enumerate(pages, 1):
        page_url = page.get("url")
        if not page_url:
            continue

        # Check cache
        cached = await check_notion_cache(page_url, max_age_hours=24)

        if cached:
            cached_count += 1
            age_hours = cached.get("age_hours", 999)

            if age_hours < 1:  # Fresh (< 1 hour)
                fresh_count += 1
                status = f"✅ FRESH ({age_hours*60:.1f} min)"
            else:
                stale_count += 1
                status = f"⏰ OLD ({age_hours:.1f} hrs)"

            print(f"{i}. {status}")
            print(f"   URL: {page_url}")
            print(f"   Title: {cached.get('title', 'N/A')}")
            print(f"   Scrape Date: {cached.get('scrape_date', 'N/A')}")
            print(f"   Locked: {cached.get('is_locked', False)}")
        else:
            missing_count += 1
            print(f"{i}. ❌ NOT CACHED")
            print(f"   URL: {page_url}")

        print()

    # Step 3: Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    print(f"📊 Crawl Statistics:")
    print(f"   Pages crawled: {pages_crawled}")
    print(f"   Pages saved to Notion: {sum(1 for p in pages if p.get('notion_saved'))}")
    print()

    print(f"💾 Cache Statistics:")
    print(f"   Total checked: {len(pages)}")
    print(f"   ✅ Cached: {cached_count}")
    print(f"   🆕 Fresh (< 1 hour): {fresh_count}")
    print(f"   ⏰ Stale (> 1 hour): {stale_count}")
    print(f"   ❌ Missing: {missing_count}")
    print()

    # Success criteria
    success = True
    success_criteria = []

    if pages_crawled > 1:
        success_criteria.append("✅ Multiple pages crawled")
    else:
        success_criteria.append("❌ Only 1 page crawled")
        success = False

    if cached_count > 1:
        success_criteria.append("✅ Multiple pages cached in Notion")
    else:
        success_criteria.append("❌ Less than 2 pages cached")
        success = False

    if fresh_count > 1:
        success_criteria.append("✅ Multiple fresh pages (< 1 hour old)")
    else:
        success_criteria.append("❌ Not enough fresh pages")
        success = False

    if missing_count == 0:
        success_criteria.append("✅ All pages cached (no missing)")
    else:
        success_criteria.append(f"⚠️ {missing_count} page(s) not cached")

    print("🎯 Success Criteria:")
    for criterion in success_criteria:
        print(f"   {criterion}")
    print()

    if success:
        print("=" * 70)
        print("🎉 TEST PASSED - Deep Crawl Successful!")
        print("=" * 70)
        print()
        print(f"✅ Crawled {pages_crawled} pages")
        print(f"✅ Cached {cached_count} pages in Notion")
        print(f"✅ {fresh_count} pages are fresh (< 1 hour)")
        print(f"✅ Scrape Date tracking working")
    else:
        print("=" * 70)
        print("⚠️ TEST INCOMPLETE - Check Results Above")
        print("=" * 70)

    print()
    print("💡 Tip: Check your Notion database to see all the crawled pages!")
    print(f"   Filter by: Scrape Date > {datetime.now().isoformat()[:10]}")


if __name__ == "__main__":
    asyncio.run(test_deep_crawl())
