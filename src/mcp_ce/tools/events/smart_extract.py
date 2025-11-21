"""
Smart event extraction with cache checking and adaptive deep crawling.
"""

import asyncio
from typing import Optional, Dict, Any, Tuple
from datetime import datetime


async def smart_extract_event(
    url: str,
    force_refresh: bool = False,
    max_cache_age_hours: int = 24,
    quality_threshold: float = 0.7,
    max_optimization_iterations: int = 2,
    enable_deep_crawl: bool = True,
    max_deep_crawl_depth: int = 2,
) -> Tuple[Any, Dict[str, Any]]:
    """
    Smart event extraction with cache checking and adaptive deep crawling.

    Workflow:
    1. Check Notion cache - skip scraping if recently scraped
    2. Scrape initial URL
    3. Extract event details with quality evaluation
    4. If quality is low, decide whether to:
       a. Optimize extraction (re-prompt with feedback)
       b. Deep crawl linked pages for more information
    5. Merge information from multiple pages if deep crawled
    6. Save to Notion with UPSERT

    Args:
        url: Event URL to scrape
        force_refresh: Force re-scrape even if cached
        max_cache_age_hours: Maximum age of cached data (default: 24 hours)
        quality_threshold: Minimum acceptable quality score
        max_optimization_iterations: Max iterations for optimization
        enable_deep_crawl: Allow deep crawling if quality is low
        max_deep_crawl_depth: Maximum depth for deep crawling

    Returns:
        Tuple of (EventDetails, metadata_dict)
        metadata includes: quality_score, cache_hit, deep_crawled, pages_crawled
    """
    from mcp_ce.cache import check_url_in_notion
    from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
    from mcp_ce.tools.crawl4ai.deep_crawl import deep_crawl_website
    from mcp_ce.tools.events.evaluator_optimizer import (
        extract_event_with_quality_control,
    )
    from mcp_ce.agentic_tools.graphs.extract_strucured_data.extract_structured_data import (
        extract_event_details,
    )

    metadata = {
        "cache_hit": False,
        "deep_crawled": False,
        "pages_crawled": 1,
        "quality_score": None,
        "optimization_iterations": 0,
        "deep_crawl_reason": None,
    }

    print(f"🎯 Smart event extraction: {url}")

    # Step 1: Check cache
    if not force_refresh:
        print(f"\n📦 Step 1: Checking Notion cache...")
        cached = await check_url_in_notion(url, max_cache_age_hours)

        if cached:
            metadata["cache_hit"] = True
            print(f"✅ Found cached data (age: {cached['age_hours']:.1f} hours)")
            print(f"   Title: {cached['title']}")
            print(f"   Locked: {cached['is_locked']}")

            if cached["is_locked"]:
                print(f"   🔒 Page is locked - using cached version")
                # TODO: Load full event data from cached page
                # For now, continue with scraping
                print(f"   ⚠️ Cannot load full data from cache yet, re-scraping...")
            else:
                print(f"   ℹ️ Page unlocked, will refresh with new scrape")
        else:
            print(f"   ℹ️ No recent cache found, will scrape")
    else:
        print(f"\n📦 Step 1: Skipping cache (force_refresh=True)")

    # Step 2: Scrape initial URL
    print(f"\n📡 Step 2: Scraping {url}...")
    scrape_result = await crawl_website(
        url=url,
        extract_images=False,
        extract_links=True,  # Need links for potential deep crawl
        word_count_threshold=5,
        headless=True,
        save_to_notion=False,  # We'll handle Notion saving at the end
    )

    if not scrape_result.get("success"):
        raise RuntimeError(f"Scraping failed: {scrape_result.get('error')}")

    content = scrape_result.get("content", {}).get("markdown", "")
    links = scrape_result.get("links", {})
    print(f"✅ Scraped {len(content)} characters")

    # Step 3: Extract and evaluate
    print(f"\n🤖 Step 3: Extracting event details with quality control...")
    event, quality_score = await extract_event_with_quality_control(
        url=url,
        content=content,
        quality_threshold=quality_threshold,
        max_iterations=max_optimization_iterations,
    )

    metadata["quality_score"] = {
        "overall": quality_score.overall_score,
        "completeness": quality_score.completeness,
        "accuracy": quality_score.accuracy,
        "confidence": quality_score.confidence,
        "is_acceptable": quality_score.is_acceptable(quality_threshold),
    }

    # Step 4: Decide on deep crawl OR use cached pages
    if enable_deep_crawl and quality_score.should_deep_crawl:
        print(f"\n🌐 Step 4: Quality check suggests more information needed")
        print(f"   Reason: {quality_score.deep_crawl_reason}")
        print(f"   Current quality: {quality_score.overall_score:.2f}")

        # Check cache for linked pages before crawling
        internal_links = links.get("internal", [])[:10]  # Limit to 10 links
        cached_content_pages = []
        uncached_links = []

        if internal_links:
            # Extract href strings from link dicts
            if isinstance(internal_links[0], dict):
                internal_links = [
                    link.get("href", link) if isinstance(link, dict) else link
                    for link in internal_links
                ]

            print(f"\n📦 Checking cache for {len(internal_links)} linked pages...")

            # Check which are already cached and load their content
            from mcp_ce.cache import check_url_in_notion

            for link in internal_links:
                cached = await check_url_in_notion(link, max_cache_age_hours)
                if cached:
                    cached_content_pages.append(
                        {
                            "url": link,
                            "title": cached.get("title", "Untitled"),
                            "content": cached.get("content", ""),
                            "age_hours": cached.get("age_hours", 0),
                        }
                    )
                else:
                    uncached_links.append(link)

            cached_count = len(cached_content_pages)
            uncached_count = len(uncached_links)

            print(f"   ✅ {cached_count} pages found in cache")
            print(f"   📡 {uncached_count} pages need scraping")

        # If we have enough cached pages, use them instead of deep crawl
        if cached_content_pages and len(cached_content_pages) >= 3:
            print(
                f"\n💾 Using {len(cached_content_pages)} cached pages (skipping deep crawl)..."
            )

            # Combine content from cached pages
            all_content = content  # Start with main page
            for page in cached_content_pages[:5]:  # Limit to 5 pages
                page_content = page.get("content", "")
                if page_content:
                    age = page.get("age_hours", 0)
                    print(f"   📄 {page['title']} ({age:.1f}h old)")
                    all_content += (
                        f"\n\n--- Page: {page['url']} ---\n\n{page_content[:3000]}"
                    )

            metadata["deep_crawled"] = False
            metadata["pages_crawled"] = len(cached_content_pages) + 1
            metadata["cache_aggregation"] = True

            print(
                f"\n🔄 Re-extracting with cached content ({len(all_content)} chars)..."
            )

            # Re-extract with all content
            improved_event = await extract_event_details(text=all_content, url=url)

            # Compare quality
            from mcp_ce.tools.events.evaluator_optimizer import evaluate_event_quality

            new_quality = await evaluate_event_quality(improved_event, all_content)

            print(f"   Before aggregation: {quality_score.overall_score:.2f}")
            print(f"   After aggregation:  {new_quality.overall_score:.2f}")

            if new_quality.overall_score > quality_score.overall_score:
                print(f"   🎉 Improved quality by using cached pages!")
                event = improved_event
                quality_score = new_quality
                metadata["quality_score"]["overall"] = new_quality.overall_score
                metadata["quality_score"]["completeness"] = new_quality.completeness
                metadata["quality_score"]["accuracy"] = new_quality.accuracy
                metadata["quality_score"]["confidence"] = new_quality.confidence
            else:
                print(f"   ℹ️ No significant improvement from cached pages")

        else:
            # Not enough cached pages, perform deep crawl
            print(f"\n🕸️ Starting deep crawl (max depth: {max_deep_crawl_depth})...")
            print(f"   Only {len(cached_content_pages)} pages cached, need more data")

            deep_result = await deep_crawl_website(
                url=url,
                max_depth=max_deep_crawl_depth,
                max_pages=10,
                save_to_notion=True,
                include_external=False,
            )

            if deep_result.get("success"):
                pages_crawled = deep_result.get("pages_crawled", 0)
                metadata["deep_crawled"] = True
                metadata["pages_crawled"] = pages_crawled
                metadata["deep_crawl_reason"] = quality_score.deep_crawl_reason

                print(f"\n✅ Deep crawl complete: {pages_crawled} pages")

                # Combine content from all pages for re-extraction
                all_content = content  # Start with main page
                for page in deep_result.get("pages", []):
                    if page.get("url") != url:  # Don't duplicate main page
                        page_content = page.get("content", "")
                        if page_content:
                            all_content += f"\n\n--- Page: {page['url']} ---\n\n{page_content[:2000]}"

                print(
                    f"\n🔄 Re-extracting with combined content ({len(all_content)} chars)..."
                )

                # Re-extract with all content
                improved_event = await extract_event_details(text=all_content, url=url)

                # Compare quality
                from mcp_ce.tools.events.evaluator_optimizer import (
                    evaluate_event_quality,
                )

                new_quality = await evaluate_event_quality(improved_event, all_content)

                print(f"   Before deep crawl: {quality_score.overall_score:.2f}")
                print(f"   After deep crawl:  {new_quality.overall_score:.2f}")

                if new_quality.overall_score > quality_score.overall_score:
                    print(f"   🎉 Improved quality!")
                    event = improved_event
                    quality_score = new_quality
                    metadata["quality_score"]["overall"] = new_quality.overall_score
                else:
                    print(f"   ℹ️ No significant improvement")
            else:
                print(f"   ⚠️ Deep crawl failed: {deep_result.get('error')}")

    elif not quality_score.is_acceptable(quality_threshold):
        print(f"\n⚠️ Quality below threshold but deep crawl disabled or not recommended")
        print(
            f"   Quality: {quality_score.overall_score:.2f} < {quality_threshold:.2f}"
        )

    print(f"\n✅ Final event extraction complete")
    print(f"   Event: {event.title}")
    print(f"   Quality: {metadata['quality_score']['overall']:.2f}")
    print(f"   Pages crawled: {metadata['pages_crawled']}")

    return event, metadata


# Test
if __name__ == "__main__":

    async def test():
        event, meta = await smart_extract_event(
            url="https://www.bluesmuse.dance/",
            force_refresh=False,
            enable_deep_crawl=True,
        )

        print(f"\n📊 Final Result:")
        print(f"  Event: {event.title}")
        print(f"  Date: {event.date}")
        print(f"  Location: {event.get_full_location()}")
        print(f"  Quality: {meta['quality_score']['overall']:.2f}")
        print(f"  Cache hit: {meta['cache_hit']}")
        print(f"  Deep crawled: {meta['deep_crawled']}")
        print(f"  Pages: {meta['pages_crawled']}")

    asyncio.run(test())
