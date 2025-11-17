"""Test crawling and deep crawling the Blues Muse website.

Tests:
1. Single page crawl - Crawl homepage
2. Deep crawl - Crawl multiple pages following links
3. Specific page crawl - Crawl team page
4. Content validation - Verify extracted content quality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncio
from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
from mcp_ce.tools.crawl4ai.deep_crawl import deep_crawl_website


async def test_single_page_crawl():
    """Test crawling the Blues Muse homepage."""
    print("\n" + "=" * 60)
    print("TEST 1: Single Page Crawl - Homepage")
    print("=" * 60)

    response = await crawl_website(
        url="https://www.bluesmuse.dance/",
        extract_images=True,
        extract_links=True,
        override_cache=True,  # Force fresh crawl for testing
    )

    assert response.is_success, f"Crawl failed: {response.error}"
    result = response.result
    assert result["title"], "No title extracted"
    assert result["content_length"] > 0, "No content extracted"

    print(f"✅ Success: {response.is_success}")
    print(f"📄 Title: {result['title']}")
    print(
        f"📝 Description: {result['description'][:100]}..."
        if result["description"]
        else "📝 Description: N/A"
    )
    print(f"📏 Content length: {result['content_length']} chars")
    print(f"🖼️  Images: {len(result.get('images', []))}")
    print(f"🔗 Internal links: {len(result.get('links', {}).get('internal', []))}")
    print(f"🔗 External links: {len(result.get('links', {}).get('external', []))}")

    return response


async def test_specific_page_crawl():
    """Test crawling the Blues Muse team page."""
    print("\n" + "=" * 60)
    print("TEST 2: Specific Page Crawl - Team Page")
    print("=" * 60)

    response = await crawl_website(
        url="https://www.bluesmuse.dance/blues-muse-team",
        extract_images=True,
        extract_links=True,
        override_cache=True,  # Force fresh crawl for testing
    )

    assert response.is_success, f"Crawl failed: {response.error}"
    result = response.result
    assert result["title"], "No title extracted"
    assert result["content_length"] > 0, "No content extracted"

    print(f"✅ Success: {response.is_success}")
    print(f"📄 Title: {result['title']}")
    print(
        f"📝 Description: {result['description'][:100]}..."
        if result["description"]
        else "📝 Description: N/A"
    )
    print(f"📏 Content length: {result['content_length']} chars")
    print(f"🖼️  Images: {len(result.get('images', []))}")

    # Show first 500 chars of content
    content_preview = result["content_markdown"][:500]
    print(f"\n📄 Content Preview:")
    print(content_preview + "...")

    return response


async def test_deep_crawl():
    """Test deep crawling the Blues Muse website."""
    print("\n" + "=" * 60)
    print("TEST 3: Deep Crawl - Multiple Pages")
    print("=" * 60)
    print("⚠️  This will take a few minutes...\n")

    response = await deep_crawl_website(
        url="https://www.bluesmuse.dance/",
        max_depth=2,  # Start with depth 2 for testing
        max_pages=10,  # Cap at 10 pages for testing
        include_external=False,
        override_cache=True,  # Force fresh crawl for testing
    )

    assert response.is_success, f"Deep crawl failed: {response.error}"
    result = response.result
    assert result["pages_crawled"] > 0, "No pages crawled"

    print(f"\n✅ Success: {response.is_success}")
    print(f"📊 Pages crawled: {result['pages_crawled']}")
    print(f"🌐 Domain: {result['domain']}")
    print(f"🔢 Max depth: {result['max_depth']}")

    print(f"\n📄 Pages crawled:")
    for idx, page in enumerate(result["pages"], 1):
        print(f"  {idx}. {page['url']}")
        print(f"     Title: {page['title'][:60]}...")
        print(f"     Content: {page['content_length']} chars")

    return response


async def test_deep_crawl_with_depth():
    """Test deep crawl with different depth settings."""
    print("\n" + "=" * 60)
    print("TEST 4: Deep Crawl with Depth 3")
    print("=" * 60)
    print("⚠️  This may take several minutes...\n")

    response = await deep_crawl_website(
        url="https://www.bluesmuse.dance/blues-muse-team",
        max_depth=3,
        max_pages=20,  # Cap at 20 pages
        include_external=False,
        override_cache=True,  # Force fresh crawl for testing
    )

    assert response.is_success, f"Deep crawl failed: {response.error}"
    result = response.result

    print(f"\n✅ Success: {response.is_success}")
    print(f"📊 Pages crawled: {result['pages_crawled']}")
    print(f"🔢 Max depth: {result['max_depth']}")

    # Group pages by domain path
    pages_by_path = {}
    for page in result["pages"]:
        path = (
            page["url"].split(".dance")[1] if ".dance" in page["url"] else page["url"]
        )
        path_prefix = "/".join(path.split("/")[:3])  # Group by first 2 path segments
        if path_prefix not in pages_by_path:
            pages_by_path[path_prefix] = []
        pages_by_path[path_prefix].append(page)

    print(f"\n📂 Pages by path:")
    for path, pages in sorted(pages_by_path.items()):
        print(f"  {path}/ ({len(pages)} pages)")

    return response


async def test_content_quality():
    """Test content extraction quality."""
    print("\n" + "=" * 60)
    print("TEST 5: Content Quality Validation")
    print("=" * 60)

    response = await crawl_website(
        url="https://www.bluesmuse.dance/blues-muse-team",
        word_count_threshold=10,  # Filter out very short blocks
        override_cache=True,  # Force fresh crawl for testing
    )

    assert response.is_success, f"Crawl failed: {response.error}"
    result = response.result

    content = result["content_markdown"]

    # Quality checks
    word_count = len(content.split())
    line_count = len(content.split("\n"))
    has_headings = "#" in content
    has_links = "[" in content and "]" in content

    print(f"✅ Content extracted: {len(content)} chars")
    print(f"📊 Quality Metrics:")
    print(f"   - Word count: {word_count}")
    print(f"   - Line count: {line_count}")
    print(f"   - Has headings: {has_headings}")
    print(f"   - Has links: {has_links}")

    # Assertions
    assert word_count > 50, "Content has too few words"
    assert line_count > 10, "Content has too few lines"
    assert has_headings, "Content should have markdown headings"

    print("\n✅ Content quality validation passed!")

    return response


async def run_all_tests():
    """Run all tests sequentially."""
    print("\n" + "🧪 " * 20)
    print("BLUES MUSE CRAWLING TEST SUITE")
    print("🧪 " * 20)

    tests = [
        ("Single Page Crawl", test_single_page_crawl),
        ("Specific Page Crawl", test_specific_page_crawl),
        ("Deep Crawl (Depth 2)", test_deep_crawl),
        ("Deep Crawl (Depth 3)", test_deep_crawl_with_depth),
        ("Content Quality", test_content_quality),
    ]

    results = {}
    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = {"status": "PASSED", "result": result}
            passed += 1
            print(f"\n✅ {test_name}: PASSED")
        except AssertionError as e:
            results[test_name] = {"status": "FAILED", "error": str(e)}
            failed += 1
            print(f"\n❌ {test_name}: FAILED - {e}")
        except Exception as e:
            results[test_name] = {"status": "ERROR", "error": str(e)}
            failed += 1
            print(f"\n❌ {test_name}: ERROR - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {len(tests)}")

    for test_name, result in results.items():
        status_emoji = "✅" if result["status"] == "PASSED" else "❌"
        print(f"{status_emoji} {test_name}: {result['status']}")

    return results


if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests())
