"""
Tool for updating Notion page properties.
"""

import asyncio
import os
import json
from typing import Dict, Any
from agency_swarm.tools import BaseTool
from pydantic import Field
from notion_mcp import NotionMCPClient


class UpdateNotionPageTool(BaseTool):
    """
    Update properties of an existing Notion page.

    This tool updates page properties such as title, status, tags, etc.
    Properties must match the database schema if the page is in a database.
    Provide properties as a JSON string or dictionary.
    """

    page_id: str = Field(..., description="The ID of the page to update.")

    properties: str = Field(
        ...,
        description='Page properties to update as JSON string. Example: \'{"Status": {"select": {"name": "Done"}}, "Priority": {"number": 1}}\'',
    )

    def run(self):
        """Execute the update page operation."""
        # Get Notion token from environment
        notion_token = os.getenv("NOTION_TOKEN")
        if not notion_token:
            return "Error: NOTION_TOKEN environment variable not set."

        # Parse properties JSON
        try:
            props_dict = json.loads(self.properties)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in properties: {str(e)}"

        # Run the async operation
        return asyncio.run(self._async_update_page(notion_token, props_dict))

    async def _async_update_page(self, token: str, properties: Dict[str, Any]):
        """Async implementation of update page."""
        try:
            async with NotionMCPClient(token) as client:
                page = await client.update_page(
                    page_id=self.page_id, properties=properties
                )

                updated_props = list(properties.keys())

                return f"✅ Successfully updated page properties: {', '.join(updated_props)}\nPage ID: {page.get('id', 'unknown')}"

        except Exception as e:
            error_msg = str(e)
            if "validation" in error_msg.lower() or "property" in error_msg.lower():
                return f"Error updating page: {error_msg}\n\nTip: Ensure property names and types match the database schema. Use GetNotionPageTool to check current properties."
            return f"Error updating page: {error_msg}"


if __name__ == "__main__":
    # Test the tool
    import sys

    if len(sys.argv) > 1:
        tool = UpdateNotionPageTool(
            page_id=sys.argv[1],
            properties='{"Status": {"select": {"name": "In Progress"}}}',
        )
        print(tool.run())
    else:
        print("Usage: python UpdateNotionPageTool.py <page_id>")
