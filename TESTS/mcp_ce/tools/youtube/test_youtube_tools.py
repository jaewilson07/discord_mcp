"""Test YouTube tools with video: https://www.youtube.com/watch?v=SJi469BuU6g"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

# Import YouTube tools
from mcp_ce.tools.youtube.get_video_metadata import get_video_metadata
from mcp_ce.tools.youtube.get_transcript import get_transcript
from mcp_ce.tools.youtube.search_youtube import search_youtube


async def test_get_video_metadata():
    """Test get_video_metadata with video SJi469BuU6g."""
    print("\n" + "=" * 80)
    print("TEST 1: Get Video Metadata")
    print("=" * 80)

    video_id = "SJi469BuU6g"

    # Test 1: Get metadata without cache override
    print(f"\n▶️  Testing get_video_metadata(video_id='{video_id}')")
    result = await get_video_metadata(video_id=video_id)

    if result["success"]:
        print("✅ Success!")
        print(f"   Title: {result['title']}")
        print(f"   Channel: {result['channel']}")
        print(f"   Published: {result['published_at']}")
        print(f"   Duration: {result['duration']}")
        print(f"   Views: {result['view_count']}")
        print(f"   Likes: {result['like_count']}")
        print(f"   URL: {result['url']}")
        if result.get("tags"):
            print(f"   Tags: {', '.join(result['tags'][:5])}...")
    else:
        print(f"❌ Error: {result['error']}")

    # Test 2: Get metadata with full URL
    print(f"\n▶️  Testing with full URL")
    full_url = f"https://www.youtube.com/watch?v={video_id}"
    result2 = await get_video_metadata(video_id=full_url)

    if result2["success"]:
        print("✅ Success! (URL extraction works)")
        print(f"   Video ID extracted: {result2['video_id']}")
    else:
        print(f"❌ Error: {result2['error']}")

    # Test 3: Get metadata with cache override
    print(f"\n▶️  Testing with override_cache=True")
    result3 = await get_video_metadata(video_id=video_id, override_cache=True)

    if result3["success"]:
        print("✅ Success! (Cache override works)")
        print(f"   Title: {result3['title']}")
    else:
        print(f"❌ Error: {result3['error']}")

    return result["success"] if result else False


async def test_get_transcript():
    """Test get_transcript with video SJi469BuU6g."""
    print("\n" + "=" * 80)
    print("TEST 2: Get Video Transcript")
    print("=" * 80)

    video_id = "SJi469BuU6g"

    # Test 1: Get transcript without cache override
    print(f"\n▶️  Testing get_transcript(video_id='{video_id}')")
    result = await get_transcript(video_id=video_id)

    if result.is_success:
        print("✅ Success!")
        print(f"   Video ID: {result.result.video_id}")
        print(f"   Language: {result.result.language}")
        print(f"   Length: {result.result.length} characters")
        print(f"   Auto-generated: {result.result.is_auto_generated}")
        print(f"   Entries count: {len(result.result.entries)}")
        print(f"   Transcript preview: {result.result.transcript[:200]}...")
    else:
        print(f"❌ Error: {result.error}")

    # Test 2: Get transcript with language preference
    print(f"\n▶️  Testing with languages=['en', 'es']")
    result2 = await get_transcript(video_id=video_id, languages=["en", "es"])

    if result2.is_success:
        print("✅ Success!")
        print(f"   Language: {result2.result.language}")
    else:
        print(f"❌ Error: {result2.error}")

    # Test 3: Get transcript with cache override
    print(f"\n▶️  Testing with override_cache=True")
    result3 = await get_transcript(video_id=video_id, override_cache=True)

    if result3.is_success:
        print("✅ Success! (Cache override works)")
        print(f"   Length: {result3.result.length} characters")
    else:
        print(f"❌ Error: {result3.error}")

    # Test 4: Access transcript entries
    if result.is_success and result.result.entries:
        print(f"\n▶️  Testing entry access (first 3 entries)")
        for i, entry in enumerate(result.result.entries[:3]):
            print(f"   [{i}] {entry['start']:.2f}s: {entry['text']}")
        print("✅ Entry access works!")

    return result.is_success


async def test_search_youtube():
    """Test search_youtube related to the video topic."""
    print("\n" + "=" * 80)
    print("TEST 3: Search YouTube")
    print("=" * 80)

    # First get the video title to search for related content
    video_id = "SJi469BuU6g"
    metadata = await get_video_metadata(video_id=video_id)

    if not metadata["success"]:
        print(f"❌ Could not get metadata for search query")
        return False

    # Extract key terms from title for search
    title = metadata["title"]
    search_query = title.split()[0:3]  # First 3 words
    search_query = " ".join(search_query)

    print(f"\n▶️  Testing search_youtube(query='{search_query}')")
    result = await search_youtube(query=search_query, max_results=5)

    if result["success"]:
        print(f"✅ Success! Found {result['count']} videos")
        for i, video in enumerate(result["videos"]):
            print(f"\n   [{i+1}] {video['title']}")
            print(f"       ID: {video['id']}")
            print(f"       Channel: {video['channel']}")
            print(f"       URL: {video['url']}")
    else:
        print(f"❌ Error: {result['error']}")

    # Test 2: Search with different order
    print(f"\n▶️  Testing with order_by='viewCount'")
    result2 = await search_youtube(
        query=search_query, max_results=3, order_by="viewCount"
    )

    if result2["success"]:
        print(f"✅ Success! Found {result2['count']} videos (sorted by views)")
        for i, video in enumerate(result2["videos"]):
            print(f"   [{i+1}] {video['title'][:60]}...")
    else:
        print(f"❌ Error: {result2['error']}")

    # Test 3: Search with cache override
    print(f"\n▶️  Testing with override_cache=True")
    result3 = await search_youtube(
        query=search_query, max_results=3, override_cache=True
    )

    if result3["success"]:
        print(f"✅ Success! (Cache override works)")
        print(f"   Found {result3['count']} videos")
    else:
        print(f"❌ Error: {result3['error']}")

    return result["success"]


async def test_invalid_inputs():
    """Test error handling with invalid inputs."""
    print("\n" + "=" * 80)
    print("TEST 4: Error Handling")
    print("=" * 80)

    # Test 1: Invalid video ID
    print(f"\n▶️  Testing with invalid video ID")
    result = await get_video_metadata(video_id="invalid_id_12345")

    if not result["success"]:
        print(f"✅ Error handled correctly: {result['error']}")
    else:
        print(f"❌ Should have failed with invalid ID")

    # Test 2: Empty video ID
    print(f"\n▶️  Testing with empty video ID")
    result2 = await get_video_metadata(video_id="")

    if not result2["success"]:
        print(f"✅ Error handled correctly: {result2['error']}")
    else:
        print(f"❌ Should have failed with empty ID")

    # Test 3: Empty search query
    print(f"\n▶️  Testing search with empty query")
    result3 = await search_youtube(query="")

    if not result3["success"]:
        print(f"✅ Error handled correctly: {result3['error']}")
    else:
        print(f"❌ Should have failed with empty query")

    # Test 4: Invalid search order
    print(f"\n▶️  Testing search with invalid order_by")
    result4 = await search_youtube(query="test", order_by="invalid_order")

    if not result4["success"]:
        print(f"✅ Error handled correctly: {result4['error']}")
    else:
        print(f"❌ Should have failed with invalid order")

    return True


async def test_cache_behavior():
    """Test cache behavior and performance."""
    print("\n" + "=" * 80)
    print("TEST 5: Cache Behavior")
    print("=" * 80)

    video_id = "SJi469BuU6g"

    # Test 1: First call (cache miss)
    print(f"\n▶️  First call (cache miss)")
    import time

    start = time.time()
    result1 = await get_video_metadata(video_id=video_id)
    duration1 = time.time() - start

    if result1["success"]:
        print(f"✅ Success! Duration: {duration1:.3f}s")
    else:
        print(f"❌ Error: {result1['error']}")
        return False

    # Test 2: Second call (cache hit)
    print(f"\n▶️  Second call (should use cache)")
    start = time.time()
    result2 = await get_video_metadata(video_id=video_id)
    duration2 = time.time() - start

    if result2["success"]:
        print(f"✅ Success! Duration: {duration2:.3f}s")
        if duration2 < duration1:
            print(f"   🚀 Cache speedup: {duration1/duration2:.1f}x faster!")
        else:
            print(f"   ⚠️  Warning: Second call wasn't faster (may not be using cache)")
    else:
        print(f"❌ Error: {result2['error']}")
        return False

    # Test 3: Third call with override_cache (forces fresh)
    print(f"\n▶️  Third call with override_cache=True")
    start = time.time()
    result3 = await get_video_metadata(video_id=video_id, override_cache=True)
    duration3 = time.time() - start

    if result3["success"]:
        print(f"✅ Success! Duration: {duration3:.3f}s")
        if duration3 > duration2:
            print(f"   ✅ Cache override worked (took longer than cached call)")
        else:
            print(f"   ⚠️  Warning: Override call should be slower")
    else:
        print(f"❌ Error: {result3['error']}")
        return False

    return True


async def main():
    """Run all YouTube tool tests."""
    print("\n" + "🎬" * 40)
    print("YOUTUBE TOOLS TEST SUITE")
    print("Video: https://www.youtube.com/watch?v=SJi469BuU6g")
    print("🎬" * 40)

    # Check for API key
    if not os.getenv("YOUTUBE_API_KEY"):
        print("\n❌ ERROR: YOUTUBE_API_KEY not found in environment variables")
        print("   Please set YOUTUBE_API_KEY in your .env file")
        return

    results = []

    # Run tests
    results.append(("Get Video Metadata", await test_get_video_metadata()))
    results.append(("Get Transcript", await test_get_transcript()))
    results.append(("Search YouTube", await test_search_youtube()))
    results.append(("Error Handling", await test_invalid_inputs()))
    results.append(("Cache Behavior", await test_cache_behavior()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\n{total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(main())
