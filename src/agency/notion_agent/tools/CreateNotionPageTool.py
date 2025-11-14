"""
Tool for creating new Notion pages.
"""

import asyncio
import os
from typing import Optional
from agency_swarm.tools import BaseTool
from pydantic import Field
from notion_mcp import NotionMCPClient


class CreateNotionPageTool(BaseTool):
    """
    Create a new page in Notion workspace.

    This tool creates a new page with specified title and content.
    The page can be created as a child of another page or at the
    workspace root. Content is provided as simple text paragraphs.
    """

    title: str = Field(..., description="The title of the new page.")

    parent_page_id: Optional[str] = Field(
        default=None,
        description="The ID of the parent page (optional). If not provided, creates page at workspace root.",
    )

    content: Optional[str] = Field(
        default=None,
        description="The content to add to the page as text paragraphs. Multiple paragraphs should be separated by double newlines.",
    )

    def run(self):
        """Execute the create page operation."""
        # Get Notion token from environment
        notion_token = os.getenv("NOTION_TOKEN")
        if not notion_token:
            return "Error: NOTION_TOKEN environment variable not set."

        # Run the async operation
        return asyncio.run(self._async_create_page(notion_token))

    async def _async_create_page(self, token: str):
        """Async implementation of create page."""
        try:
            async with NotionMCPClient(token) as client:
                page = await client.create_page(
                    parent_id=self.parent_page_id,
                    title=self.title,
                    content=self.content,
                )

                page_id = page.get("id", "unknown")
                page_url = page.get("url", "")

                output = [
                    f"✅ Successfully created page: '{self.title}'",
                    f"Page ID: {page_id}",
                ]

                if page_url:
                    output.append(f"URL: {page_url}")

                return "\n".join(output)

        except Exception as e:
            error_msg = str(e)
            if "parent" in error_msg.lower() or "not found" in error_msg.lower():
                return f"Error creating page: {error_msg}\n\nTip: If specifying a parent page, ensure the integration has access to it."
            return f"Error creating page: {error_msg}"


if __name__ == "__main__":
    # Test the tool
    tool = CreateNotionPageTool(
        title="Test Page from Python",
        content="This is a test page created using the Notion MCP client.\n\nIt has multiple paragraphs.",
    )
    print(tool.run())
