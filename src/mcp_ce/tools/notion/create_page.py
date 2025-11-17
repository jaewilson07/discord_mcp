"""Create a new page in Notion workspace."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import NotionPage
from ._client_helper import get_client


@register_command("notion", "create_notion_page")
async def create_notion_page(
    title: str, parent_page_id: Optional[str] = None, content: Optional[str] = None
) -> ToolResponse:
    """
    Create a new page in Notion workspace.

    Args:
        title: The title of the new page
        parent_page_id: The ID of the parent page (optional). If not provided,
                       creates page at workspace root.
        content: The content to add to the page as text paragraphs. Multiple
                paragraphs should be separated by double newlines.

    Returns:
        ToolResponse with NotionPage dataclass containing:
        - page_id: ID of created page
        - url: Page URL
        - title: Page title
        - created_time: Creation time
        - last_edited_time: Last edit time
        - parent_type: Parent type
        - parent_id: Parent ID
    """
    try:
        client = get_client()  # Returns notion_client.AsyncClient

        # Build parent structure
        parent = (
            {"page_id": parent_page_id}
            if parent_page_id
            else {"type": "workspace", "workspace": True}
        )

        # Build properties
        properties = {"title": {"title": [{"text": {"content": title}}]}}

        # Build children blocks if content provided
        children = []
        if content:
            paragraphs = content.split("\n\n")
            for paragraph in paragraphs:
                if paragraph.strip():
                    children.append(
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"type": "text", "text": {"content": paragraph}}
                                ]
                            },
                        }
                    )

        page = await client.pages.create(
            parent=parent,
            properties=properties,
            children=children if children else None,
        )

        # Extract parent info
        parent_obj = page.get("parent", {})
        parent_type = parent_obj.get("type", "")
        parent_id = parent_obj.get("page_id", "") or parent_obj.get("database_id", "")

        result = NotionPage(
            page_id=page.get("id", ""),
            url=page.get("url", ""),
            title=title,
            created_time=page.get("created_time", ""),
            last_edited_time=page.get("last_edited_time", ""),
            parent_type=parent_type,
            parent_id=parent_id,
        )

        return ToolResponse(is_success=True, result=result)
    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))

    except Exception as e:
        error_msg = str(e)
        if "parent" in error_msg.lower() or "not found" in error_msg.lower():
            error_msg += "\n\nTip: If specifying a parent page, ensure the integration has access to it."

        return ToolResponse(
            is_success=False, result=None, error=f"Error creating page: {error_msg}"
        )


# Test code
if __name__ == "__main__":
    import asyncio

    async def test():
        result = await create_notion_page(
            title="Test Page from MCP",
            content="This is a test page created using the Notion MCP client.\n\nIt has multiple paragraphs.",
        )

        print(f"Success: {result['success']}")
        if result["success"]:
            print(f"Page ID: {result['page_id']}")
            print(f"URL: {result['url']}")
        else:
            print(f"Error: {result['error']}")

    asyncio.run(test())
