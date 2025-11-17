"""Search for pages and databases in Notion workspace."""

from typing import Literal
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import NotionSearchResult
from ._client_helper import get_client


@register_command("notion", "search_notion")
@cache_tool(ttl=180, id_param="query")  # Cache for 3 minutes
async def search_notion(
    query: str,
    filter_type: Literal["page", "database", "all"] = "all",
    override_cache: bool = False,
) -> ToolResponse:
    """
    Search for pages and databases in Notion workspace.

    Args:
        query: The search query to find pages/databases. Can be page title,
               database name, or content keywords.
        filter_type: Filter results by type. Use 'page' for pages only,
                    'database' for databases only, or 'all' for both.
        override_cache: Whether to bypass cache and force fresh search (default: False)

    Returns:
        ToolResponse with NotionSearchResult dataclass containing:
        - results: List of search results (pages, databases)
        - total_count: Total number of results
        - has_more: Whether there are more results
        - next_cursor: Cursor for pagination
    """
    try:
        client = get_client()  # Returns notion_client.AsyncClient

        # Build filter based on filter_type
        # Note: API 2025-09-03 changed "database" to "data_source" in responses,
        # but the filter still uses "database" for backward compatibility
        filter_param = None
        if filter_type != "all":
            # Use "data_source" for database filtering (API 2025-09-03)
            filter_value = "data_source" if filter_type == "database" else filter_type
            filter_param = {"property": "object", "value": filter_value}

        # Perform search
        response = await client.search(query=query, filter=filter_param)
        results = response.get("results", [])
        has_more = response.get("has_more", False)
        next_cursor = response.get("next_cursor")

        if not results:
            result = NotionSearchResult(
                results=[], total_count=0, has_more=False, next_cursor=None
            )
            return ToolResponse(is_success=True, result=result)

        # Format results
        formatted_results = []
        for result in results:
            obj_type = result.get("object", "unknown")
            result_id = result.get("id", "unknown")

            # Extract title
            title = "Untitled"
            if "properties" in result:
                props = result["properties"]
                # Try different title property locations
                if "title" in props:
                    title_obj = props["title"]
                    if "title" in title_obj and title_obj["title"]:
                        title = title_obj["title"][0]["text"]["content"]
                elif "Name" in props:
                    name_obj = props["Name"]
                    if "title" in name_obj and name_obj["title"]:
                        title = name_obj["title"][0]["text"]["content"]

            formatted_results.append(
                {
                    "id": result_id,
                    "title": title,
                    "type": obj_type,
                    "url": result.get("url", ""),
                }
            )

        result = NotionSearchResult(
            results=formatted_results,
            total_count=len(formatted_results),
            has_more=has_more,
            next_cursor=next_cursor,
        )

        return ToolResponse(is_success=True, result=result)
    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Error searching Notion: {str(e)}. Please check: 1) NOTION_TOKEN is valid, 2) Node.js 18+ is installed, 3) Integration has access to pages",
        )


# Test code
if __name__ == "__main__":
    import asyncio

    async def test():
        result = await search_notion("Getting started", filter_type="page")
        print(f"Success: {result['success']}")
        print(f"Count: {result['count']}")
        for item in result.get("results", []):
            print(f"  - {item['title']} ({item['type']}): {item['url']}")
        if result.get("error"):
            print(f"Error: {result['error']}")

    asyncio.run(test())
