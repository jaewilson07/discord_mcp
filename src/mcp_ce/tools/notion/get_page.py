"""
Retrieve full details of a Notion page by its ID.
"""

import os
from typing import Dict, Any
from notion_mcp import NotionMCPClient


async def get_notion_page(page_id: str) -> Dict[str, Any]:
    """
    Retrieve full details of a Notion page by its ID.
    
    Args:
        page_id: The ID of the Notion page to retrieve (with or without dashes)
    
    Returns:
        Dict containing:
        - success: bool indicating if retrieval succeeded
        - page: dict with page details including id, created_time, last_edited_time,
                url, archived status, properties, and parent info
        - error: error message if retrieval failed
    """
    # Get Notion token from environment
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        return {
            "success": False,
            "page": None,
            "error": "NOTION_TOKEN environment variable not set."
        }
    
    try:
        async with NotionMCPClient(notion_token) as client:
            page = await client.get_page(page_id)
            
            # Extract and format page details
            properties = {}
            if "properties" in page:
                for prop_name, prop_value in page["properties"].items():
                    properties[prop_name] = {
                        "type": prop_value.get("type", "unknown"),
                        "value": prop_value
                    }
            
            # Format parent info
            parent_info = None
            if "parent" in page:
                parent = page["parent"]
                parent_info = {
                    "type": parent.get("type", "unknown"),
                    "database_id": parent.get("database_id"),
                    "page_id": parent.get("page_id")
                }
            
            return {
                "success": True,
                "page": {
                    "id": page.get("id"),
                    "created_time": page.get("created_time"),
                    "last_edited_time": page.get("last_edited_time"),
                    "url": page.get("url"),
                    "archived": page.get("archived", False),
                    "properties": properties,
                    "parent": parent_info
                },
                "error": None
            }
    
    except Exception as e:
        return {
            "success": False,
            "page": None,
            "error": f"Error retrieving page: {str(e)}"
        }


# Test code
if __name__ == "__main__":
    import asyncio
    import sys
    
    async def test():
        if len(sys.argv) > 1:
            result = await get_notion_page(sys.argv[1])
            print(f"Success: {result['success']}")
            if result['success']:
                page = result['page']
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
