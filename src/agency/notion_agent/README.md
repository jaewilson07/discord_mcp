# Notion Agent

A specialized Agency Swarm agent for interacting with Notion workspaces through the Model Context Protocol (MCP).

## Overview

The Notion Agent provides a complete interface to the Notion API, allowing you to:
- Search for pages and databases
- Retrieve page details and content
- Create new pages with structured content
- Update page properties
- Query databases with filters
- Add comments to pages

## Setup

### 1. Prerequisites

- Node.js 18+ installed
- Notion integration token

### 2. Create Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Give it a name (e.g., "My Agency Integration")
4. Select the workspace
5. Copy the "Internal Integration Token"

### 3. Connect Pages to Integration

For each page/database you want to access:
1. Open the page in Notion
2. Click "..." menu → "Connections" → "Connect to"
3. Select your integration

### 4. Set Environment Variable

Set the `NOTION_TOKEN` environment variable:

**Windows (PowerShell):**
```powershell
$env:NOTION_TOKEN = "secret_..."
```

**Linux/Mac:**
```bash
export NOTION_TOKEN="secret_..."
```

Or add to `.env` file in project root:
```
NOTION_TOKEN=secret_...
```

## Available Tools

### SearchNotionTool
Search for pages and databases by query text.

```python
from agency.notion_agent.tools.SearchNotionTool import SearchNotionTool

tool = SearchNotionTool(
    query="Project Planning",
    filter_type="page"  # "page", "database", or "all"
)
result = tool.run()
```

### GetNotionPageTool
Retrieve complete page details including properties and metadata.

```python
from agency.notion_agent.tools.GetNotionPageTool import GetNotionPageTool

tool = GetNotionPageTool(page_id="abc123...")
result = tool.run()
```

### CreateNotionPageTool
Create a new page with title and content.

```python
from agency.notion_agent.tools.CreateNotionPageTool import CreateNotionPageTool

tool = CreateNotionPageTool(
    title="New Project",
    parent_page_id="parent123...",  # Optional
    content="Project description here.\n\nMultiple paragraphs supported."
)
result = tool.run()
```

### UpdateNotionPageTool
Update page properties (for database pages).

```python
from agency.notion_agent.tools.UpdateNotionPageTool import UpdateNotionPageTool

tool = UpdateNotionPageTool(
    page_id="page123...",
    properties='{"Status": {"select": {"name": "In Progress"}}, "Priority": {"number": 1}}'
)
result = tool.run()
```

### QueryNotionDatabaseTool
Query a database with filters and sorting.

```python
from agency.notion_agent.tools.QueryNotionDatabaseTool import QueryNotionDatabaseTool

tool = QueryNotionDatabaseTool(
    database_id="db123...",
    filter_json='{"property": "Status", "select": {"equals": "Active"}}',
    sorts_json='[{"property": "Created", "direction": "descending"}]'
)
result = tool.run()
```

### AddNotionCommentTool
Add a comment to a page.

```python
from agency.notion_agent.tools.AddNotionCommentTool import AddNotionCommentTool

tool = AddNotionCommentTool(
    page_id="page123...",
    comment_text="Great work on this!"
)
result = tool.run()
```

## Using in Agency

Import and use the agent in your agency:

```python
from agency_swarm import Agency
from agency.notion_agent import notion_agent
from agency.other_agent import other_agent

agency = Agency([
    other_agent,  # Can communicate with Notion agent
    [other_agent, notion_agent],  # Direct communication line
])

# Run the agency
agency.run_demo()
```

## Example Workflows

### Workflow 1: Create and Track Project
```
User: "Create a new project page called 'Q1 Marketing Campaign'"

Agent Actions:
1. SearchNotionTool - Find "Projects" parent page
2. CreateNotionPageTool - Create page under Projects
3. AddNotionCommentTool - Add initial status comment
```

### Workflow 2: Update Task Status
```
User: "Mark all tasks assigned to John as complete"

Agent Actions:
1. QueryNotionDatabaseTool - Find tasks where Assignee = John
2. UpdateNotionPageTool - Update Status to "Complete" for each
3. AddNotionCommentTool - Add completion notes
```

### Workflow 3: Generate Report
```
User: "Show me all high-priority tasks due this week"

Agent Actions:
1. QueryNotionDatabaseTool - Filter by Priority=High and Due Date=This Week
2. Format and present results with details
```

## Architecture

```
Notion Agent (Python)
    ↓
Agent Tools (BaseTool)
    ↓
NotionMCPClient (Python)
    ↓
MCP Server (Node.js via npx)
    ↓
Notion API
```

The agent uses the Notion MCP client which manages a Node.js subprocess running the official `@notionhq/notion-mcp-server`. All communication happens through JSON-RPC over stdio.

## Troubleshooting

### "NOTION_TOKEN environment variable not set"
- Ensure `NOTION_TOKEN` is exported in your shell
- For persistent setup, add to `.env` file or system environment

### "Page not found" or "Object not found"
- Integration doesn't have access to the page
- Go to page → "..." → "Connections" → Connect your integration

### "Node.js not found"
- Install Node.js 18+ from https://nodejs.org/
- Verify: `node --version`

### "Validation error" on property updates
- Property name or type doesn't match database schema
- Use `GetNotionPageTool` to check current properties
- Ensure property values match expected types (select, number, date, etc.)

### MCP Server Issues
- First run downloads `@notionhq/notion-mcp-server` via npx (may take a moment)
- Check internet connection if download fails
- Server logs available in Python script output

## Security Notes

- Never commit `NOTION_TOKEN` to version control
- Use `.env` file (add to `.gitignore`)
- Integration tokens have workspace-level permissions
- Limit integration access to only needed pages

## Additional Resources

- [Notion API Documentation](https://developers.notion.com/)
- [Notion Integrations Guide](https://www.notion.so/help/create-integrations-with-the-notion-api)
- [MCP Protocol Spec](https://modelcontextprotocol.io/)
- [Agency Swarm Documentation](https://github.com/VRSEN/agency-swarm)

## License

This agent is part of the mcp-discord project and follows the same license.
