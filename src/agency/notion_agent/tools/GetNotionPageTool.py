"""
Tool for retrieving Notion page details.
"""

import asyncio
import os
from agency_swarm.tools import BaseTool
from pydantic import Field
from notion_mcp import NotionMCPClient


class GetNotionPageTool(BaseTool):
    """
    Retrieve full details of a Notion page by its ID.

    This tool fetches complete information about a page including its
    properties, content, and metadata. Use this to read page content
    before updating or to verify page details.
    """

    page_id: str = Field(
        ...,
        description="The ID of the Notion page to retrieve (with or without dashes).",
    )

    def run(self):
        """Execute the get page operation."""
        # Get Notion token from environment
        notion_token = os.getenv("NOTION_TOKEN")
        if not notion_token:
            return "Error: NOTION_TOKEN environment variable not set."

        # Run the async operation
        return asyncio.run(self._async_get_page(notion_token))

    async def _async_get_page(self, token: str):
        """Async implementation of get page."""
        try:
            async with NotionMCPClient(token) as client:
                page = await client.get_page(self.page_id)

                # Format page info
                output = ["=== Page Details ===\n"]

                # Basic info
                output.append(f"ID: {page.get('id', 'unknown')}")
                output.append(f"Created: {page.get('created_time', 'unknown')}")
                output.append(f"Last Edited: {page.get('last_edited_time', 'unknown')}")
                output.append(f"URL: {page.get('url', 'unknown')}")
                output.append(f"Archived: {page.get('archived', False)}")
                output.append("")

                # Properties
                if "properties" in page:
                    output.append("Properties:")
                    for prop_name, prop_value in page["properties"].items():
                        prop_type = prop_value.get("type", "unknown")
                        output.append(f"  - {prop_name} ({prop_type})")
                    output.append("")

                # Parent info
                if "parent" in page:
                    parent = page["parent"]
                    parent_type = parent.get("type", "unknown")
                    output.append(f"Parent: {parent_type}")
                    if "database_id" in parent:
                        output.append(f"  Database ID: {parent['database_id']}")
                    elif "page_id" in parent:
                        output.append(f"  Page ID: {parent['page_id']}")
                    output.append("")

                return "\n".join(output)

        except Exception as e:
            return f"Error retrieving page: {str(e)}"


if __name__ == "__main__":
    # Test the tool
    import sys

    if len(sys.argv) > 1:
        tool = GetNotionPageTool(page_id=sys.argv[1])
        print(tool.run())
    else:
        print("Usage: python GetNotionPageTool.py <page_id>")
