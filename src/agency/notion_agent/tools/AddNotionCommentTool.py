"""
Tool for adding comments to Notion pages.
"""

import asyncio
import os
from agency_swarm.tools import BaseTool
from pydantic import Field
from notion_mcp import NotionMCPClient


class AddNotionCommentTool(BaseTool):
    """
    Add a comment to a Notion page.

    This tool adds a text comment to a specified page. Useful for
    leaving notes, feedback, or updates on pages without modifying
    the page content itself.
    """

    page_id: str = Field(..., description="The ID of the page to add a comment to.")

    comment_text: str = Field(
        ..., description="The text content of the comment to add."
    )

    def run(self):
        """Execute the add comment operation."""
        # Get Notion token from environment
        notion_token = os.getenv("NOTION_TOKEN")
        if not notion_token:
            return "Error: NOTION_TOKEN environment variable not set."

        # Run the async operation
        return asyncio.run(self._async_add_comment(notion_token))

    async def _async_add_comment(self, token: str):
        """Async implementation of add comment."""
        try:
            async with NotionMCPClient(token) as client:
                comment = await client.add_comment(
                    page_id=self.page_id, comment_text=self.comment_text
                )

                comment_id = comment.get("id", "unknown")

                return (
                    f"✅ Successfully added comment to page\nComment ID: {comment_id}"
                )

        except Exception as e:
            return f"Error adding comment: {str(e)}"


if __name__ == "__main__":
    # Test the tool
    import sys

    if len(sys.argv) > 2:
        tool = AddNotionCommentTool(page_id=sys.argv[1], comment_text=sys.argv[2])
        print(tool.run())
    else:
        print("Usage: python AddNotionCommentTool.py <page_id> <comment_text>")
