"""
Update properties of an existing Notion page.
"""

import os
import json
from typing import Dict, Any, Union
from notion_mcp import NotionMCPClient


async def update_notion_page(
    page_id: str,
    properties: Union[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Update properties of an existing Notion page.
    
    Args:
        page_id: The ID of the page to update
        properties: Page properties to update as JSON string or dict.
                   Example: {"Status": {"select": {"name": "Done"}}, 
                            "Priority": {"number": 1}}
    
    Returns:
        Dict containing:
        - success: bool indicating if update succeeded
        - page_id: the ID of the updated page
        - updated_properties: list of property names that were updated
        - error: error message if update failed
    """
    # Get Notion token from environment
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        return {
            "success": False,
            "page_id": None,
            "updated_properties": [],
            "error": "NOTION_TOKEN environment variable not set."
        }
    
    # Parse properties if string
    try:
        if isinstance(properties, str):
            props_dict = json.loads(properties)
        else:
            props_dict = properties
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "page_id": None,
            "updated_properties": [],
            "error": f"Invalid JSON in properties: {str(e)}"
        }
    
    try:
        async with NotionMCPClient(notion_token) as client:
            page = await client.update_page(
                page_id=page_id,
                properties=props_dict
            )
            
            updated_props = list(props_dict.keys())
            
            return {
                "success": True,
                "page_id": page.get("id"),
                "updated_properties": updated_props,
                "error": None
            }
    
    except Exception as e:
        error_msg = str(e)
        if "validation" in error_msg.lower() or "property" in error_msg.lower():
            error_msg += "\n\nTip: Ensure property names and types match the database schema. Use get_notion_page to check current properties."
        
        return {
            "success": False,
            "page_id": None,
            "updated_properties": [],
            "error": f"Error updating page: {error_msg}"
        }


# Test code
if __name__ == "__main__":
    import asyncio
    import sys
    
    async def test():
        if len(sys.argv) > 1:
            result = await update_notion_page(
                page_id=sys.argv[1],
                properties='{"Status": {"select": {"name": "In Progress"}}}'
            )
            
            print(f"Success: {result['success']}")
            if result['success']:
                print(f"Page ID: {result['page_id']}")
                print(f"Updated: {', '.join(result['updated_properties'])}")
            else:
                print(f"Error: {result['error']}")
        else:
            print("Usage: python update_page.py <page_id>")
    
    asyncio.run(test())
