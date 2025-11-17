"""URL Ping Tool"""

import httpx
import asyncio
from typing import Optional
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import PingResult


@register_command("url_ping", "ping_url")
@cache_tool(ttl=60, id_param="url")  # Cache for 1 minute
async def ping_url(
    url: str, timeout: Optional[int] = 10, override_cache: bool = False
) -> ToolResponse:
    """
    Ping a URL and return the response status.

    Args:
        url: The URL to ping (must include protocol, e.g., https://example.com)
        timeout: Request timeout in seconds (default: 10)
        override_cache: Whether to bypass cache and force fresh ping (default: False)

    Returns:
        ToolResponse with PingResult dataclass containing:
        - url: The URL that was pinged
        - status_code: HTTP status code
        - status_text: HTTP status text
        - response_time_seconds: Time taken for the request
        - headers: Dictionary of response headers
    """
    import time

    # Validate URL has protocol
    if not url.startswith(("http://", "https://")):
        return ToolResponse(
            is_success=False,
            result=None,
            error="URL must start with http:// or https://",
        )

    start_time = time.time()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            response_time = time.time() - start_time

            result = PingResult(
                url=url,
                status_code=response.status_code,
                status_text=response.reason_phrase,
                response_time_seconds=round(response_time, 3),
                headers=dict(response.headers),
            )

            return ToolResponse(is_success=True, result=result)

    except httpx.TimeoutException:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Request timed out after {timeout} seconds",
        )

    except httpx.HTTPError as e:
        return ToolResponse(
            is_success=False, result=None, error=f"HTTP error: {str(e)}"
        )

    except Exception as e:
        return ToolResponse(
            is_success=False, result=None, error=f"Unexpected error: {str(e)}"
        )


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
