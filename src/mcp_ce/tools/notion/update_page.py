"""Update properties of an existing Notion page."""

import json
from typing import Dict, Any, Union
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import NotionPageUpdateResult
from ._client_helper import get_client


@register_command("notion", "update_notion_page")
async def update_notion_page(
    page_id: str, properties: Union[str, Dict[str, Any]]
) -> ToolResponse:
    """
    Update properties of an existing Notion page.

    Args:
        page_id: The ID of the page to update
        properties: Page properties to update as JSON string or dict.
                   Example: {"Status": {"select": {"name": "Done"}},
                            "Priority": {"number": 1}}

    Returns:
        ToolResponse with NotionPageUpdateResult dataclass containing:
        - page_id: ID of updated page
        - url: Page URL
        - last_edited_time: Last edit time
        - properties: Updated properties dict
    """
    # Parse properties if string
    try:
        if isinstance(properties, str):
            props_dict = json.loads(properties)
        else:
            props_dict = properties
    except json.JSONDecodeError as e:
        return ToolResponse(
            is_success=False, result=None, error=f"Invalid JSON in properties: {str(e)}"
        )

    try:
        client = get_client()  # Returns notion_client.AsyncClient
        page = await client.pages.update(page_id=page_id, properties=props_dict)

        result = NotionPageUpdateResult(
            page_id=page.get("id", ""),
            url=page.get("url", ""),
            last_edited_time=page.get("last_edited_time", ""),
            properties=props_dict,
        )

        return ToolResponse(is_success=True, result=result)
    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))

    except Exception as e:
        error_msg = str(e)
        if "validation" in error_msg.lower() or "property" in error_msg.lower():
            error_msg += "\n\nTip: Ensure property names and types match the database schema. Use get_notion_page to check current properties."

        return ToolResponse(
            is_success=False, result=None, error=f"Error updating page: {error_msg}"
        )


# Test code
if __name__ == "__main__":
    import asyncio
    import sys

    async def test():
        if len(sys.argv) > 1:
            result = await update_notion_page(
                page_id=sys.argv[1],
                properties='{"Status": {"select": {"name": "In Progress"}}}',
            )

            print(f"Success: {result['success']}")
            if result["success"]:
                print(f"Page ID: {result['page_id']}")
                print(f"Updated: {', '.join(result['updated_properties'])}")
            else:
                print(f"Error: {result['error']}")
        else:
            print("Usage: python update_page.py <page_id>")

    asyncio.run(test())
