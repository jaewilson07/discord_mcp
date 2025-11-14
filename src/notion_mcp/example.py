"""
Example usage of the Notion MCP Client.

This script demonstrates how to use the NotionMCPClient to interact with Notion.
"""

import asyncio
import os
from notion_mcp import NotionMCPClient


async def main():
    """Main example function."""
    # Get token from environment
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        print("Please set NOTION_TOKEN environment variable")
        return

    # Initialize client
    async with NotionMCPClient(notion_token) as client:
        print("=== Connected to Notion MCP Server ===\n")

        # List available tools
        print("Available tools:")
        tools = await client.list_tools()
        for tool in tools[:5]:  # Show first 5
            print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
        print(f"  ... and {len(tools) - 5} more\n")

        # Search for pages
        print("=== Searching for pages ===")
        results = await client.search_pages("Getting started")
        print(f"Found {len(results)} results")
        for result in results[:3]:  # Show first 3
            title = "Untitled"
            if "properties" in result and "title" in result["properties"]:
                title_obj = result["properties"]["title"]
                if "title" in title_obj and title_obj["title"]:
                    title = title_obj["title"][0]["text"]["content"]
            print(f"  - {title} (ID: {result['id']})")
        print()

        # Get page details (if we found any)
        if results:
            print("=== Getting page details ===")
            page_id = results[0]["id"]
            page = await client.get_page(page_id)
            print(f"Page ID: {page['id']}")
            print(f"Created: {page['created_time']}")
            print(f"Last edited: {page['last_edited_time']}")
            print()

            # Add a comment (optional - uncomment to test)
            # print("=== Adding comment ===")
            # comment = await client.add_comment(
            #     page_id=page_id,
            #     comment_text="Hello from Python MCP Client!"
            # )
            # print(f"Comment added: {comment['id']}\n")

        # Query a database (you'll need to replace with your database ID)
        # print("=== Querying database ===")
        # db_results = await client.query_database(
        #     database_id="your_database_id_here",
        #     filter_obj={
        #         "property": "Status",
        #         "select": {"equals": "In Progress"}
        #     }
        # )
        # print(f"Found {len(db_results)} matching entries")

        print("=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
