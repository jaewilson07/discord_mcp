"""
Notion-specific cache utilities.

Provides Notion database querying for cached scraped content to avoid re-scraping.
This is separate from the general tool result caching (cache.py).
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List


async def check_url_in_notion(
    url: str, max_age_hours: int = 24, include_content: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Check if a URL has been scraped recently and exists in Notion database.

    This is NOT general tool caching - it's checking if scraped content
    exists in a Notion database to avoid re-scraping the same URLs.

    Args:
        url: URL to check
        max_age_hours: Maximum age in hours before considering cached data stale
        include_content: If True, also fetch the full page content

    Returns:
        Dict with cached data if found and fresh, None otherwise.
        Dict contains:
        - page_id: Notion page ID
        - title: Page title
        - last_edited: Last edit timestamp
        - scrape_date: When the page was scraped
        - is_locked: Whether page is locked
        - age_hours: Age in hours since scrape
        - url: Original URL
        - content: Full markdown content (if include_content=True)
    """
    try:
        from mcp_ce.tools.notion._client_helper import (
            get_data_source_id_from_database,
            query_data_source,
        )

        notion_database_id = os.getenv("NOTION_DATABASE_ID")
        if not notion_database_id:
            return None

        # Get data source ID
        data_source_id = await get_data_source_id_from_database(notion_database_id)

        # Query for existing page with this URL
        result = await query_data_source(
            data_source_id, filter_obj={"property": "URL", "url": {"equals": url}}
        )

        pages = result.get("results", [])

        if not pages:
            return None

        # Get the most recent page
        page = pages[0]

        # Check scrape date first, fallback to last_edited_time
        properties = page.get("properties", {})
        scrape_date_str = None

        if "Scrape Date" in properties:
            scrape_date_prop = properties["Scrape Date"].get("date")
            if scrape_date_prop:
                scrape_date_str = scrape_date_prop.get("start")

        # Fallback to last_edited_time if no scrape date
        if not scrape_date_str:
            scrape_date_str = page.get("last_edited_time")

        if not scrape_date_str:
            return None

        # Parse and check age
        scrape_date = datetime.fromisoformat(scrape_date_str.replace("Z", "+00:00"))
        now = datetime.now(scrape_date.tzinfo)
        age = now - scrape_date
        age_hours = age.total_seconds() / 3600

        # Check if fresh enough
        if age_hours > max_age_hours:
            print(f"   ⏰ Cached data is {age_hours:.1f} hours old (stale)")
            return None

        # Extract data
        title = ""
        if "Name" in properties:
            title_prop = properties["Name"].get("title", [])
            if title_prop:
                title = title_prop[0].get("text", {}).get("content", "")

        is_locked = properties.get("Lock", {}).get("checkbox", False)

        result_dict = {
            "page_id": page["id"],
            "title": title,
            "last_edited": page.get("last_edited_time"),
            "scrape_date": scrape_date_str,
            "is_locked": is_locked,
            "age_hours": age_hours,
            "url": url,
        }

        # Optionally fetch full content
        if include_content:
            from mcp_ce.tools.notion._client_helper import get_page_content

            content = await get_page_content(page["id"])
            result_dict["content"] = content

        return result_dict

    except Exception as e:
        print(f"   ⚠️ Error checking Notion cache: {e}")
        return None


async def check_multiple_urls_in_notion(
    urls: List[str], max_age_hours: int = 24
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Check multiple URLs for cached data in Notion.

    Args:
        urls: List of URLs to check
        max_age_hours: Maximum age in hours

    Returns:
        Dict mapping URL to cached data (or None if not cached/stale)
    """
    import asyncio

    tasks = [check_url_in_notion(url, max_age_hours) for url in urls]
    results = await asyncio.gather(*tasks)

    return dict(zip(urls, results))
