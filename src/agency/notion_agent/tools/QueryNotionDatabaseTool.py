"""
Tool for querying Notion databases.
"""

import asyncio
import os
import json
from typing import Optional
from agency_swarm.tools import BaseTool
from pydantic import Field
from notion_mcp import NotionMCPClient


class QueryNotionDatabaseTool(BaseTool):
    """
    Query a Notion database with optional filters and sorting.

    This tool queries a database and returns entries matching the filter
    criteria. Useful for finding specific database entries based on
    properties like status, date, tags, etc.
    """

    database_id: str = Field(..., description="The ID of the database to query.")

    filter_json: Optional[str] = Field(
        default=None,
        description='Filter criteria as JSON string. Example: \'{"property": "Status", "select": {"equals": "In Progress"}}\'',
    )

    sorts_json: Optional[str] = Field(
        default=None,
        description='Sort criteria as JSON string. Example: \'[{"property": "Created", "direction": "descending"}]\'',
    )

    def run(self):
        """Execute the query database operation."""
        # Get Notion token from environment
        notion_token = os.getenv("NOTION_TOKEN")
        if not notion_token:
            return "Error: NOTION_TOKEN environment variable not set."

        # Parse JSON parameters
        filter_obj = None
        sorts_obj = None

        try:
            if self.filter_json:
                filter_obj = json.loads(self.filter_json)
            if self.sorts_json:
                sorts_obj = json.loads(self.sorts_json)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON: {str(e)}"

        # Run the async operation
        return asyncio.run(
            self._async_query_database(notion_token, filter_obj, sorts_obj)
        )

    async def _async_query_database(self, token: str, filter_obj, sorts_obj):
        """Async implementation of query database."""
        try:
            async with NotionMCPClient(token) as client:
                results = await client.query_database(
                    database_id=self.database_id, filter_obj=filter_obj, sorts=sorts_obj
                )

                if not results:
                    return "No results found matching the query criteria."

                # Format results
                output = [f"Found {len(results)} result(s):\n"]

                for i, entry in enumerate(results, 1):
                    entry_id = entry.get("id", "unknown")

                    # Extract title/name
                    title = "Untitled"
                    if "properties" in entry:
                        props = entry["properties"]
                        for prop_name in ["Name", "Title", "title"]:
                            if prop_name in props:
                                prop_obj = props[prop_name]
                                if "title" in prop_obj and prop_obj["title"]:
                                    title = prop_obj["title"][0]["text"]["content"]
                                    break

                    output.append(f"{i}. {title}")
                    output.append(f"   ID: {entry_id}")

                    # Show key properties
                    if "properties" in entry:
                        for prop_name, prop_value in list(entry["properties"].items())[
                            :3
                        ]:
                            prop_type = prop_value.get("type", "")
                            if prop_type in ["select", "status"]:
                                value = prop_value.get(prop_type, {}).get("name", "")
                                if value:
                                    output.append(f"   {prop_name}: {value}")
                            elif prop_type == "number":
                                value = prop_value.get("number", "")
                                if value is not None:
                                    output.append(f"   {prop_name}: {value}")

                    output.append("")

                return "\n".join(output)

        except Exception as e:
            return f"Error querying database: {str(e)}"


if __name__ == "__main__":
    # Test the tool
    import sys

    if len(sys.argv) > 1:
        tool = QueryNotionDatabaseTool(database_id=sys.argv[1])
        print(tool.run())
    else:
        print("Usage: python QueryNotionDatabaseTool.py <database_id>")
