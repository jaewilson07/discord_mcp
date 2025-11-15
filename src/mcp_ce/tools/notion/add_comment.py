"""
Add a comment to a Notion page.
"""

import os
from typing import Dict, Any
from notion_mcp import NotionMCPClient


async def add_notion_comment(
    page_id: str,
    comment_text: str
) -> Dict[str, Any]:
    """
    Add a comment to a Notion page.
    
    Args:
        page_id: The ID of the page to add a comment to
        comment_text: The text content of the comment to add
    
    Returns:
        Dict containing:
        - success: bool indicating if comment was added
        - comment_id: the ID of the newly created comment
        - error: error message if operation failed
    """
    # Get Notion token from environment
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        return {
            "success": False,
            "comment_id": None,
            "error": "NOTION_TOKEN environment variable not set."
        }
    
    try:
        async with NotionMCPClient(notion_token) as client:
            comment = await client.add_comment(
                page_id=page_id,
                comment_text=comment_text
            )
            
            return {
                "success": True,
                "comment_id": comment.get("id"),
                "page_id": page_id,
                "error": None
            }
    
    except Exception as e:
        return {
            "success": False,
            "comment_id": None,
            "error": f"Error adding comment: {str(e)}"
        }


# Test code
if __name__ == "__main__":
    import asyncio
    import sys
    
    async def test():
        if len(sys.argv) > 2:
            result = await add_notion_comment(sys.argv[1], sys.argv[2])
            
            print(f"Success: {result['success']}")
            if result['success']:
                print(f"Comment ID: {result['comment_id']}")
            else:
                print(f"Error: {result['error']}")
        else:
            print("Usage: python add_comment.py <page_id> <comment_text>")
    
    asyncio.run(test())
