# Notion MCP Integration

This package provides Python integration with the Notion MCP Server, allowing you to interact with Notion's API using the Model Context Protocol (MCP).

## Overview

The Notion MCP Server is a TypeScript/Node.js based implementation that converts the Notion API OpenAPI specification into MCP tools. This Python client wrapper starts the MCP server as a subprocess and communicates with it via stdio transport.

## Prerequisites

- Node.js 18+ installed on your system
- A Notion integration token (see setup instructions below)

## Setup Instructions

### 1. Create a Notion Integration

1. Go to [https://www.notion.so/profile/integrations](https://www.notion.so/profile/integrations)
2. Click "New integration"
3. Give it a name (e.g., "My Agency Bot")
4. Select the capabilities you need (Read content, Update content, Insert content, etc.)
5. Copy the "Internal Integration Token" (starts with `ntn_`)

### 2. Connect Pages to Your Integration

You need to grant your integration access to specific pages:

**Option A: From Integration Settings**
1. Go to your integration's "Access" tab
2. Click "Edit access"
3. Select the pages you want to access

**Option B: From Individual Pages**
1. Open the page you want to connect
2. Click the "..." menu in the top right
3. Select "Connect to" and choose your integration

### 3. Set Environment Variable

Set your Notion token as an environment variable:

**Windows (PowerShell):**
```powershell
$env:NOTION_TOKEN = "ntn_your_token_here"
```

**Linux/Mac:**
```bash
export NOTION_TOKEN="ntn_your_token_here"
```

Or add it to your `.env` file:
```
NOTION_TOKEN=ntn_your_token_here
```

## Usage

### Basic Example

```python
import asyncio
from notion_mcp import NotionMCPClient

async def main():
    # Initialize client (will use NOTION_TOKEN from environment)
    async with NotionMCPClient() as client:
        # Search for pages
        results = await client.search_pages("My Project")
        print(f"Found {len(results)} pages")
        
        # Get a specific page
        if results:
            page = await client.get_page(results[0]["id"])
            print(f"Page title: {page['properties']['title']['title'][0]['text']['content']}")

asyncio.run(main())
```

### Creating a Page

```python
async with NotionMCPClient() as client:
    # Find parent page
    parents = await client.search_pages("Projects", filter_type="page")
    
    if parents:
        # Create new page
        new_page = await client.create_page(
            parent_id=parents[0]["id"],
            title="New Task",
            content=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Task description here"}}]
                    }
                }
            ]
        )
        print(f"Created page: {new_page['id']}")
```

### Querying a Database

```python
async with NotionMCPClient() as client:
    # Query database with filter
    results = await client.query_database(
        database_id="your_database_id",
        filter_obj={
            "property": "Status",
            "select": {"equals": "In Progress"}
        }
    )
    
    for page in results:
        print(f"Page: {page['properties']['Name']['title'][0]['text']['content']}")
```

### Adding Comments

```python
async with NotionMCPClient() as client:
    # Add comment to a page
    comment = await client.add_comment(
        page_id="your_page_id",
        comment_text="Great work on this!"
    )
    print(f"Added comment: {comment['id']}")
```

### Using with Agency Swarm

You can integrate this with Agency Swarm by creating tools:

```python
from agency_swarm.tools import BaseTool
from pydantic import Field
from notion_mcp import NotionMCPClient

class SearchNotionTool(BaseTool):
    """Tool to search Notion pages."""
    
    query: str = Field(..., description="Search query")
    
    def run(self):
        import asyncio
        
        async def search():
            async with NotionMCPClient() as client:
                results = await client.search_pages(self.query)
                return [
                    {
                        "id": r["id"],
                        "title": r["properties"]["title"]["title"][0]["text"]["content"]
                        if "title" in r["properties"]
                        else "Untitled"
                    }
                    for r in results
                ]
        
        return asyncio.run(search())
```

## Available Methods

- `search_pages(query, filter_type=None)` - Search for pages/databases
- `get_page(page_id)` - Get page details
- `create_page(parent_id, title, content=None)` - Create new page
- `update_page(page_id, properties)` - Update page properties
- `query_database(database_id, filter_obj=None)` - Query database
- `add_comment(page_id, comment_text)` - Add comment to page
- `list_tools()` - List all available API tools
- `call_tool(tool_name, arguments)` - Call any API tool directly

## Architecture

```
┌─────────────────────┐
│   Python Client     │
│  (NotionMCPClient)  │
└──────────┬──────────┘
           │ stdio
           │
┌──────────▼──────────┐
│  Node.js MCP Server │
│ (@notionhq/notion-  │
│    mcp-server)      │
└──────────┬──────────┘
           │ HTTPS
           │
┌──────────▼──────────┐
│    Notion API       │
└─────────────────────┘
```

The Python client:
1. Starts the Node.js MCP server via `npx`
2. Communicates using JSON-RPC over stdio
3. Translates Python method calls to MCP tool calls
4. Automatically manages the subprocess lifecycle

## Troubleshooting

### Node.js not found
Install Node.js 18 or later from [nodejs.org](https://nodejs.org)

### Permission denied errors
Make sure your Notion integration has access to the pages you're trying to access

### Connection timeout
The first time you run the client, `npx` will download the MCP server package. This may take a minute.

## Resources

- [Notion API Documentation](https://developers.notion.com)
- [Notion MCP Server GitHub](https://github.com/makenotion/notion-mcp-server)
- [Model Context Protocol](https://spec.modelcontextprotocol.io/)
