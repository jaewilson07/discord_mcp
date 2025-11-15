"""
Create a new page in Notion workspace.
"""

import os
from typing import Dict, Any, Optional
from notion_mcp import NotionMCPClient


async def create_notion_page(
    title: str,
    parent_page_id: Optional[str] = None,
    content: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new page in Notion workspace.
    
    Args:
        title: The title of the new page
        parent_page_id: The ID of the parent page (optional). If not provided,
                       creates page at workspace root.
        content: The content to add to the page as text paragraphs. Multiple
                paragraphs should be separated by double newlines.
    
    Returns:
        Dict containing:
        - success: bool indicating if creation succeeded
        - page_id: the ID of the newly created page
        - url: the URL of the newly created page
        - error: error message if creation failed
    """
    # Get Notion token from environment
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        return {
            "success": False,
            "page_id": None,
            "url": None,
            "error": "NOTION_TOKEN environment variable not set."
        }
    
    try:
        async with NotionMCPClient(notion_token) as client:
            page = await client.create_page(
                parent_id=parent_page_id,
                title=title,
                content=content,
            )
            
            return {
                "success": True,
                "page_id": page.get("id"),
                "url": page.get("url"),
                "title": title,
                "error": None
            }
    
    except Exception as e:
        error_msg = str(e)
        if "parent" in error_msg.lower() or "not found" in error_msg.lower():
            error_msg += "\n\nTip: If specifying a parent page, ensure the integration has access to it."
        
        return {
            "success": False,
            "page_id": None,
            "url": None,
            "error": f"Error creating page: {error_msg}"
        }


# Test code
if __name__ == "__main__":
    import asyncio
    
    async def test():
        result = await create_notion_page(
            title="Test Page from MCP",
            content="This is a test page created using the Notion MCP client.\n\nIt has multiple paragraphs."
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Page ID: {result['page_id']}")
            print(f"URL: {result['url']}")
        else:
            print(f"Error: {result['error']}")
    
    asyncio.run(test())
