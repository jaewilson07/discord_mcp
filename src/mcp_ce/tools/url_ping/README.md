# URL Ping MCP Server

A FastMCP-based MCP (Model Context Protocol) server that provides URL ping functionality following the Code Execution Pattern for progressive disclosure.

## Overview

This MCP server implements a simple tool that can ping URLs and return detailed response information including status codes, response times, and headers. Built with [FastMCP](https://github.com/jlowin/fastmcp), it provides both traditional MCP server functionality and supports the code execution pattern.

## Pattern

This implementation follows the [Code Execution Pattern](https://www.anthropic.com/engineering/code-execution-with-mcp) which enables:
- **Progressive disclosure** - Load only the tools you need
- **Token efficiency** - Reduces token usage by 98% compared to loading all tools upfront
- **Filesystem-based tools** - Tools organized as importable Python modules
- **Autonomous discovery** - Agents can discover and combine tools as needed
- **FastMCP integration** - Production-ready server with enterprise features

## Project Structure

```
src/mcp_ce/
├── server.py                    # FastMCP server with tool registration
└── tools/
    └── url_ping/
        ├── ping_url.py          # URL ping tool implementation (with test)
        ├── __init__.py          # Package exports
        └── README.md            # This file
```

## Available Tools

### ping_url

Ping a URL and return the response status.

**Parameters:**
- `url` (str, required): The URL to ping (must include protocol, e.g., https://example.com)
- `timeout` (int, optional): Request timeout in seconds (default: 10)

**Returns:**
JSON string containing:
- `success`: Boolean indicating if the request was successful
- `url`: The URL that was pinged
- `status_code`: HTTP status code (if successful)
- `status_text`: HTTP status text (if successful)
- `response_time_seconds`: Time taken for the request in seconds
- `headers`: Response headers dictionary
- `error`: Error message (if unsuccessful)

**Example Usage:**

```python
from src.mcp_ce.tools.url_ping.ping_url import ping_url

# Ping a URL
result = await ping_url("https://www.google.com")
print(result)
```

## Running the Server

### As a FastMCP Server (Traditional MCP):
```bash
# Run with stdio transport (default)
python src/mcp_ce/server.py

# Run with HTTP transport
fastmcp run src/mcp_ce/server.py --transport http --port 8000
```

### Discover available tools:
```bash
python src/mcp_ce/server.py --discover
```

### Test individual tools directly:
```bash
python src/mcp_ce/tools/url_ping/ping_url.py
```

## Dependencies

- `fastmcp` - FastMCP framework for building MCP servers
- `httpx` - For async HTTP requests
- `asyncio` - For async operations

Make sure these are included in your `requirements.txt`:
```
fastmcp
httpx
```

## Integration with Agents

This MCP server can be used in two ways:

### 1. Traditional MCP Client (via FastMCP)
Connect using any MCP client:
```python
from fastmcp import Client

async with Client("src/mcp_ce/server.py") as client:
    result = await client.call_tool("ping_url", {"url": "https://example.com"})
    print(result.content[0].text)
```

### 2. Code Execution Pattern (Progressive Disclosure)
Agents can directly import and use tool functions:
```python
# Agent discovers and reads the tool file
from src.mcp_ce.tools.url_ping.ping_url import ping_url

# Agent uses the tool directly
result = await ping_url("https://example.com")

# Agent can process the result programmatically
import json
data = json.loads(result)
if data['success']:
    print(f"✓ {data['url']} is up! (Status: {data['status_code']})")
else:
    print(f"✗ {data['url']} is down: {data['error']}")
```

This dual approach provides:
- **Standard MCP compatibility** for clients that expect traditional MCP servers
- **Token efficiency** for agents that support the code execution pattern
- **Flexibility** to use whichever approach fits your use case

## Notes

- Built on FastMCP for production-ready MCP server functionality
- Supports both stdio and HTTP transports
- The server uses a singleton pattern for backward compatibility
- All tools are async to support non-blocking operations
- Individual tool files can be tested independently
