"""URL Ping Tool"""
import aiohttp
import asyncio
from typing import Optional
from .server import call_tool


async def ping_url(url: str, timeout: Optional[int] = 10) -> str:
    """
    Ping a URL and return the response status.
    
    Args:
        url: The URL to ping (must include protocol, e.g., https://example.com)
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        JSON string containing status code, response time, and any error messages
    """
    import time
    import json
    
    # Validate URL has protocol
    if not url.startswith(('http://', 'https://')):
        return json.dumps({
            "success": False,
            "url": url,
            "error": "URL must start with http:// or https://"
        })
    
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                response_time = time.time() - start_time
                
                result = {
                    "success": True,
                    "url": url,
                    "status_code": response.status,
                    "status_text": response.reason,
                    "response_time_seconds": round(response_time, 3),
                    "headers": dict(response.headers)
                }
                
                return json.dumps(result, indent=2)
    
    except asyncio.TimeoutError:
        return json.dumps({
            "success": False,
            "url": url,
            "error": f"Request timed out after {timeout} seconds"
        })
    
    except aiohttp.ClientError as e:
        return json.dumps({
            "success": False,
            "url": url,
            "error": f"Client error: {str(e)}"
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "url": url,
            "error": f"Unexpected error: {str(e)}"
        })


# Test - run with: python src/mcp_ce/url_ping/ping_url.py
if __name__ == "__main__":
    import asyncio
    
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
                print(f"✓ Result:\n{result}")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    asyncio.run(test())
