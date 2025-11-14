"""
Tool for searching Notion pages and databases.
"""

import asyncio
import os
from typing import Literal
from agency_swarm.tools import BaseTool
from pydantic import Field
from notion_mcp import NotionMCPClient


class SearchNotionTool(BaseTool):
    """
    Search for pages and databases in Notion workspace.

    This tool allows you to search through the Notion workspace to find
    pages and databases by query text. You can optionally filter results
    by type (page or database).
    """

    query: str = Field(
        ...,
        description="The search query to find pages/databases. Can be page title, database name, or content keywords.",
    )

    filter_type: Literal["page", "database", "all"] = Field(
        default="all",
        description="Filter results by type. Use 'page' for pages only, 'database' for databases only, or 'all' for both.",
    )

    def run(self):
        """Execute the search operation."""
        # Get Notion token from environment
        notion_token = os.getenv("NOTION_TOKEN")
        if not notion_token:
            return "Error: NOTION_TOKEN environment variable not set. Please configure your Notion integration token."

        # Run the async search
        return asyncio.run(self._async_search(notion_token))

    async def _async_search(self, token: str):
        """Async implementation of search."""
        try:
            async with NotionMCPClient(token) as client:
                # Perform search
                results = await client.search_pages(
                    query=self.query,
                    filter_type=None if self.filter_type == "all" else self.filter_type,
                )

                if not results:
                    return f"No results found for query: '{self.query}'"

                # Format results
                output = [f"Found {len(results)} result(s) for '{self.query}':\n"]

                for i, result in enumerate(results, 1):
                    obj_type = result.get("object", "unknown")
                    result_id = result.get("id", "unknown")

                    # Extract title
                    title = "Untitled"
                    if "properties" in result:
                        props = result["properties"]
                        # Try different title property locations
                        if "title" in props:
                            title_obj = props["title"]
                            if "title" in title_obj and title_obj["title"]:
                                title = title_obj["title"][0]["text"]["content"]
                        elif "Name" in props:
                            name_obj = props["Name"]
                            if "title" in name_obj and name_obj["title"]:
                                title = name_obj["title"][0]["text"]["content"]

                    # Get URL
                    url = result.get("url", "")

                    output.append(f"{i}. {title}")
                    output.append(f"   Type: {obj_type}")
                    output.append(f"   ID: {result_id}")
                    if url:
                        output.append(f"   URL: {url}")
                    output.append("")

                return "\n".join(output)

        except Exception as e:
            return f"Error searching Notion: {str(e)}\n\nPlease check:\n1. NOTION_TOKEN is valid\n2. Node.js 18+ is installed\n3. Integration has access to pages"


if __name__ == "__main__":
    # Test the tool
    tool = SearchNotionTool(query="Getting started", filter_type="page")
    print(tool.run())
