"""URL Ping Tool"""

import httpx
import asyncio
from typing import Optional


async def ping_url(url: str, timeout: Optional[int] = 10) -> dict:
    """
    Ping a URL and return the response status.

    Args:
        url: The URL to ping (must include protocol, e.g., https://example.com)
        timeout: Request timeout in seconds (default: 10)

    Returns:
        Dictionary containing status code, response time, and any error messages
    """
    import time

    # Validate URL has protocol
    if not url.startswith(("http://", "https://")):
        return {
            "success": False,
            "url": url,
            "error": "URL must start with http:// or https://",
        }

    start_time = time.time()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            response_time = time.time() - start_time

            return {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "status_text": response.reason_phrase,
                "response_time_seconds": round(response_time, 3),
                "headers": dict(response.headers),
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "url": url,
            "error": f"Request timed out after {timeout} seconds",
        }

    except httpx.HTTPError as e:
        return {"success": False, "url": url, "error": f"HTTP error: {str(e)}"}

    except Exception as e:
        return {"success": False, "url": url, "error": f"Unexpected error: {str(e)}"}


# Test - run with: python src/mcp_ce/url_ping/ping_url.py
if __name__ == "__main__":
    import asyncio
    import json

    async def test():
        print("Testing ping_url...")
        test_urls = [
            "https://www.google.com",
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404",
        ]

        for test_url in test_urls:
            print(f"\n--- Testing: {test_url} ---")
            try:
                result = await ping_url(test_url)
                print(f"✓ Result:\n{json.dumps(result, indent=2)}")
            except Exception as e:
                print(f"✗ Error: {e}")

    asyncio.run(test())
