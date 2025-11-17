"""Retrieve full details of a Notion page by its ID."""

from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import NotionPageContent
from ._client_helper import get_client


@register_command("notion", "get_notion_page")
@cache_tool(ttl=300, id_param="page_id")  # Cache for 5 minutes
async def get_notion_page(page_id: str, override_cache: bool = False) -> ToolResponse:
    """
    Retrieve full details of a Notion page by its ID.

    Args:
        page_id: The ID of the Notion page to retrieve (with or without dashes)
        override_cache: Whether to bypass cache and force fresh fetch (default: False)

    Returns:
        ToolResponse with NotionPageContent dataclass containing:
        - page_id: Page ID
        - url: Page URL
        - title: Page title
        - created_time: Creation time
        - last_edited_time: Last edit time
        - properties: Page properties dict
        - content: Page content blocks list
    """
    try:
        client = get_client()  # Returns notion_client.AsyncClient
        page = await client.pages.retrieve(page_id=page_id)

        # Extract and format page details
        properties = {}
        if "properties" in page:
            for prop_name, prop_value in page["properties"].items():
                properties[prop_name] = {
                    "type": prop_value.get("type", "unknown"),
                    "value": prop_value,
                }

        # Extract title from properties
        title = "Untitled"
        for prop_name, prop_data in properties.items():
            if prop_data["type"] == "title" and prop_data["value"].get("title"):
                title_blocks = prop_data["value"]["title"]
                if title_blocks:
                    title = title_blocks[0]["text"]["content"]
                    break

        result = NotionPageContent(
            page_id=page.get("id", ""),
            url=page.get("url", ""),
            title=title,
            created_time=page.get("created_time", ""),
            last_edited_time=page.get("last_edited_time", ""),
            properties=properties,
            content=[],  # Can be extended to fetch blocks if needed
        )

        return ToolResponse(is_success=True, result=result)
    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))

    except Exception as e:
        return ToolResponse(
            is_success=False, result=None, error=f"Error retrieving page: {str(e)}"
        )


# Test code
if __name__ == "__main__":
    import asyncio
    import sys

    async def test():
        if len(sys.argv) > 1:
            result = await get_notion_page(sys.argv[1])
            print(f"Success: {result['success']}")
            if result["success"]:
                page = result["page"]
                print(f"ID: {page['id']}")
                print(f"URL: {page['url']}")
                print(f"Created: {page['created_time']}")
                print(f"Last Edited: {page['last_edited_time']}")
                print(f"Properties: {len(page['properties'])}")
            else:
                print(f"Error: {result['error']}")
        else:
            print("Usage: python get_page.py <page_id>")

    asyncio.run(test())
