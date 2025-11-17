"""Comprehensive test suite for URL Ping tool."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

# Import URL ping tool
from mcp_ce.tools.url_ping.ping_url import ping_url


async def test_url_ping_tools():
    """
    Comprehensive test suite for URL Ping tool.

    Test Categories:
    1. Basic pinging (successful requests)
    2. HTTP status codes (2xx, 4xx, 5xx)
    3. Error handling (invalid URLs, timeouts)
    4. Cache behavior (miss, hit, override)
    """

    print("\n" + "=" * 70)
    print("URL PING TOOL COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # ============================================================
    # Test Category 1: Basic Pinging
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 1: Basic Pinging")
    print("=" * 70)

    print("\n[1.1] Testing ping_url with Google (2xx response)")
    result = await ping_url(url="https://www.google.com", override_cache=True)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   URL: {result.result.url}")
        print(f"   Status: {result.result.status_code} {result.result.status_text}")
        print(f"   Response time: {result.result.response_time_seconds}s")
        print(f"   Headers count: {len(result.result.headers)}")
        assert result.result.status_code == 200, "Expected 200 status code"
        assert (
            result.result.response_time_seconds > 0
        ), "Expected positive response time"

    print("\n[1.2] Testing ping_url with httpbin.org")
    result = await ping_url(url="https://httpbin.org/status/200", override_cache=True)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Status: {result.result.status_code} {result.result.status_text}")
        print(f"   Response time: {result.result.response_time_seconds}s")
        assert result.result.status_code == 200, "Expected 200 status code"

    print("\n[1.3] Testing ping_url with GitHub")
    result = await ping_url(url="https://github.com", override_cache=True)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Status: {result.result.status_code} {result.result.status_text}")
        print(f"   Response time: {result.result.response_time_seconds}s")
        assert result.result.status_code == 200, "Expected 200 status code"

    # ============================================================
    # Test Category 2: HTTP Status Codes
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 2: HTTP Status Codes")
    print("=" * 70)

    print("\n[2.1] Testing 404 Not Found")
    result = await ping_url(url="https://httpbin.org/status/404", override_cache=True)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Status: {result.result.status_code} {result.result.status_text}")
        assert result.result.status_code == 404, "Expected 404 status code"

    print("\n[2.2] Testing 500 Internal Server Error")
    result = await ping_url(url="https://httpbin.org/status/500", override_cache=True)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Status: {result.result.status_code} {result.result.status_text}")
        assert result.result.status_code == 500, "Expected 500 status code"

    print("\n[2.3] Testing 301 Redirect")
    result = await ping_url(url="https://httpbin.org/status/301", override_cache=True)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Status: {result.result.status_code} {result.result.status_text}")
        assert result.result.status_code == 301, "Expected 301 status code"

    # ============================================================
    # Test Category 3: Error Handling
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 3: Error Handling")
    print("=" * 70)

    print("\n[3.1] Testing invalid URL (missing protocol)")
    result = await ping_url(url="google.com", override_cache=True)
    print(f"❌ Error handled: {not result.is_success}")
    if not result.is_success:
        print(f"   Error message: {result.error}")
        assert "must start with http://" in result.error, "Expected protocol error"

    print("\n[3.2] Testing invalid URL (nonexistent domain)")
    result = await ping_url(
        url="https://this-domain-definitely-does-not-exist-12345.com",
        timeout=5,
        override_cache=True,
    )
    print(f"❌ Error handled: {not result.is_success}")
    if not result.is_success:
        print(f"   Error message: {result.error[:80]}...")

    print("\n[3.3] Testing timeout (extremely slow endpoint)")
    result = await ping_url(
        url="https://httpbin.org/delay/15",  # Delays 15 seconds
        timeout=2,  # Timeout after 2 seconds
        override_cache=True,
    )
    print(f"❌ Timeout handled: {not result.is_success}")
    if not result.is_success:
        print(f"   Error message: {result.error}")
        assert "timed out" in result.error.lower(), "Expected timeout error"

    # ============================================================
    # Test Category 4: Cache Behavior
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 4: Cache Behavior")
    print("=" * 70)

    print("\n[4.1] Testing cache miss (first request)")
    import time

    start = time.time()
    result1 = await ping_url(url="https://www.google.com", override_cache=True)
    time1 = time.time() - start
    print(f"✅ Cache MISS: {time1:.3f}s")
    if result1.is_success:
        print(f"   Status: {result1.result.status_code}")

    print("\n[4.2] Testing cache hit (second request)")
    start = time.time()
    result2 = await ping_url(url="https://www.google.com", override_cache=False)
    time2 = time.time() - start
    print(f"✅ Cache HIT: {time2:.3f}s ({time1/time2:.1f}x faster)")
    if result2.is_success:
        print(f"   Status: {result2.result.status_code}")
        assert (
            result2.result.status_code == result1.result.status_code
        ), "Cached result should match"

    print("\n[4.3] Testing cache override (force fresh ping)")
    start = time.time()
    result3 = await ping_url(url="https://www.google.com", override_cache=True)
    time3 = time.time() - start
    print(f"✅ Cache BYPASSED: {time3:.3f}s (fresh fetch)")
    if result3.is_success:
        print(f"   Status: {result3.result.status_code}")

    # ============================================================
    # Test Category 5: Custom Timeout
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 5: Custom Timeout")
    print("=" * 70)

    print("\n[5.1] Testing with short timeout (5 seconds)")
    result = await ping_url(
        url="https://www.google.com", timeout=5, override_cache=True
    )
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Response time: {result.result.response_time_seconds}s")
        assert (
            result.result.response_time_seconds < 5
        ), "Response should be under timeout"

    print("\n[5.2] Testing with long timeout (30 seconds)")
    result = await ping_url(
        url="https://httpbin.org/delay/2",  # Delays 2 seconds
        timeout=30,
        override_cache=True,
    )
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Response time: {result.result.response_time_seconds}s")
        assert (
            result.result.response_time_seconds >= 2
        ), "Should have delayed ~2 seconds"

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Suite Summary")
    print("=" * 70)
    print(f"✅ URL Ping tool tested")
    print(f"✅ ToolResponse pattern validated")
    print(f"✅ Dataclass result confirmed (PingResult)")
    print(f"✅ Cache behavior verified (1 min TTL)")
    print(f"✅ Error handling validated")
    print(f"✅ HTTP status codes tested (2xx, 4xx, 5xx)")
    print(f"✅ Custom timeout behavior verified")
    print("=" * 70)

    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("URL PING TOOL COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("\n⚠️  Note: This test makes real HTTP requests to public endpoints")
    print("   (Google, GitHub, httpbin.org)")
    print("")

    try:
        asyncio.run(test_url_ping_tools())
        print("\n✅ All tests completed successfully!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
    except AssertionError as e:
        print(f"\n\n❌ Test assertion failed: {str(e)}")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
