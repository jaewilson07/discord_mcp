"""
Runtime helpers for zero-context discovery pattern.

These helpers are injected into the Python sandbox and allow the LLM to:
1. Discover available MCP servers (without loading schemas)
2. Query tool documentation on-demand
3. Search for tools across servers
4. Execute tools via proxies

This follows elusznik's zero-context discovery pattern:
~200 tokens overhead regardless of server count.
"""

import json
from typing import Optional, List, Dict, Any


# Registry of available MCP servers
_SERVERS_REGISTRY = {
    "url_ping": {
        "name": "url_ping",
        "description": "MCP server for pinging URLs and checking their availability",
        "module": "src.mcp_ce.tools.url_ping.ping_url",
        "tools": ["ping_url"],
    }
}


def discovered_servers() -> List[Dict[str, str]]:
    """
    Discover available MCP servers without loading their schemas.

    Returns:
        List of server dictionaries with 'name' and 'description'.
        Does NOT include tool schemas - use query_tool_docs() for that.

    Example:
        >>> servers = discovered_servers()
        >>> for server in servers:
        ...     print(f"{server['name']}: {server['description']}")
    """
    return [
        {"name": name, "description": info["description"]}
        for name, info in _SERVERS_REGISTRY.items()
    ]


def list_servers() -> List[str]:
    """
    List names of all available MCP servers.

    Returns:
        List of server names as strings.

    Example:
        >>> servers = list_servers()
        >>> print(servers)
        ['url_ping']
    """
    return list(_SERVERS_REGISTRY.keys())


# Synchronous version (alias)
def list_servers_sync() -> List[str]:
    """Synchronous version of list_servers()"""
    return list_servers()


def query_tool_docs(
    server_name: str, tool: Optional[str] = None, detail: str = "summary"
) -> str:
    """
    Query documentation for tools in a specific server.
    Load schemas on-demand (zero-context discovery).

    Args:
        server_name: Name of the MCP server (from discovered_servers)
        tool: Specific tool name (None for all tools)
        detail: Level of detail - "summary" or "full"

    Returns:
        JSON string with tool documentation

    Example:
        >>> docs = query_tool_docs("url_ping")
        >>> print(docs)
        {"tools": [{"name": "ping_url", ...}]}

        >>> docs = query_tool_docs("url_ping", tool="ping_url", detail="full")
    """
    if server_name not in _SERVERS_REGISTRY:
        return json.dumps({"error": f"Server '{server_name}' not found"})

    server_info = _SERVERS_REGISTRY[server_name]

    # Load tool documentation on-demand
    if server_name == "url_ping":
        tools_docs = {
            "ping_url": {
                "name": "ping_url",
                "description": "Ping a URL and return the response status, timing, and headers",
                "parameters": {
                    "url": {
                        "type": "string",
                        "description": "The URL to ping (must include protocol, e.g., https://example.com)",
                        "required": True,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Request timeout in seconds (default: 10)",
                        "required": False,
                        "default": 10,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "status_code": "integer (HTTP status)",
                        "response_time_seconds": "float",
                        "headers": "dict",
                        "error": "string (if failed)",
                    },
                },
            }
        }

        # Filter by specific tool if requested
        if tool:
            if tool in tools_docs:
                result = tools_docs[tool]
                if detail == "summary":
                    # Return summary only
                    return json.dumps(
                        {"name": result["name"], "description": result["description"]},
                        indent=2,
                    )
                else:
                    # Return full documentation
                    return json.dumps(result, indent=2)
            else:
                return json.dumps(
                    {"error": f"Tool '{tool}' not found in server '{server_name}'"}
                )
        else:
            # Return all tools
            if detail == "summary":
                return json.dumps(
                    {
                        "server": server_name,
                        "tools": [
                            {"name": name, "description": info["description"]}
                            for name, info in tools_docs.items()
                        ],
                    },
                    indent=2,
                )
            else:
                return json.dumps(
                    {"server": server_name, "tools": list(tools_docs.values())},
                    indent=2,
                )

    return json.dumps(
        {"error": f"No documentation available for server '{server_name}'"}
    )


# Synchronous version
def query_tool_docs_sync(
    server_name: str, tool: Optional[str] = None, detail: str = "summary"
) -> str:
    """Synchronous version of query_tool_docs()"""
    return query_tool_docs(server_name, tool, detail)


def search_tool_docs(query: str, limit: Optional[int] = None) -> str:
    """
    Search for tools across all servers using fuzzy matching.

    Args:
        query: Search query (matches against tool names and descriptions)
        limit: Maximum number of results (None for all matches)

    Returns:
        JSON string with matching tools

    Example:
        >>> results = search_tool_docs("ping")
        >>> print(results)
        {"matches": [{"server": "url_ping", "tool": "ping_url", ...}]}
    """
    query_lower = query.lower()
    matches = []

    for server_name in _SERVERS_REGISTRY.keys():
        # Get full docs for this server
        docs_json = query_tool_docs(server_name, detail="full")
        docs = json.loads(docs_json)

        if "tools" in docs:
            for tool_info in docs["tools"]:
                # Check if query matches tool name or description
                if (
                    query_lower in tool_info["name"].lower()
                    or query_lower in tool_info["description"].lower()
                ):
                    matches.append(
                        {
                            "server": server_name,
                            "tool": tool_info["name"],
                            "description": tool_info["description"],
                        }
                    )

    # Apply limit if specified
    if limit:
        matches = matches[:limit]

    return json.dumps({"matches": matches}, indent=2)


# Synchronous version
def search_tool_docs_sync(query: str, limit: Optional[int] = None) -> str:
    """Synchronous version of search_tool_docs()"""
    return search_tool_docs(query, limit)


def capability_summary() -> str:
    """
    Return a one-paragraph summary of available capabilities.

    This is advertised in SANDBOX_HELPERS_SUMMARY.

    Returns:
        Human-readable summary string
    """
    server_count = len(_SERVERS_REGISTRY)
    tool_count = sum(len(info["tools"]) for info in _SERVERS_REGISTRY.values())

    return (
        f"MCP Code Execution Sandbox with {server_count} server(s) providing {tool_count} tool(s). "
        f"Available helpers: discovered_servers() to list servers, query_tool_docs(server, tool) "
        f"to load schemas on-demand, search_tool_docs(query) for fuzzy search. "
        f"Zero-context discovery: ~200 token overhead regardless of server count."
    )


# Tool execution proxies
async def _execute_tool(server_name: str, tool_name: str, **kwargs) -> Any:
    """
    Execute a tool via proxy (called by sandbox code).

    Args:
        server_name: Server name from discovered_servers()
        tool_name: Tool name from query_tool_docs()
        **kwargs: Tool arguments

    Returns:
        Tool execution result
    """
    if server_name not in _SERVERS_REGISTRY:
        raise ValueError(f"Server '{server_name}' not found")

    server_info = _SERVERS_REGISTRY[server_name]

    if tool_name not in server_info["tools"]:
        raise ValueError(f"Tool '{tool_name}' not found in server '{server_name}'")

    # Import and execute tool dynamically
    if server_name == "url_ping" and tool_name == "ping_url":
        from .tools.url_ping.ping_url import ping_url

        return await ping_url(**kwargs)

    raise NotImplementedError(f"Tool '{tool_name}' not implemented")


# Synchronous wrapper for tools that don't need async
def _execute_tool_sync(server_name: str, tool_name: str, **kwargs) -> Any:
    """Synchronous version of _execute_tool (for non-async tools)"""
    import asyncio

    return asyncio.run(_execute_tool(server_name, tool_name, **kwargs))


# Helper to create tool proxy (used in sandbox)
def create_tool_proxy(server_name: str, tool_name: str):
    """
    Create a callable proxy for a tool.

    This allows sandbox code to call tools naturally:
        ping = create_tool_proxy("url_ping", "ping_url")
        result = await ping(url="https://example.com")
    """

    async def proxy(**kwargs):
        return await _execute_tool(server_name, tool_name, **kwargs)

    proxy.__name__ = tool_name
    proxy.__doc__ = f"Proxy for {server_name}.{tool_name}"

    return proxy


# SANDBOX_HELPERS_SUMMARY - advertised to LLM
SANDBOX_HELPERS_SUMMARY = {
    "description": capability_summary(),
    "helpers": [
        {
            "name": "discovered_servers",
            "description": "List available MCP servers without loading schemas",
            "signature": "() -> List[Dict[str, str]]",
        },
        {
            "name": "list_servers",
            "description": "Get names of all available servers",
            "signature": "() -> List[str]",
        },
        {
            "name": "query_tool_docs",
            "description": "Load tool documentation on-demand for a specific server",
            "signature": "(server_name: str, tool: Optional[str] = None, detail: str = 'summary') -> str",
        },
        {
            "name": "search_tool_docs",
            "description": "Search for tools across all servers",
            "signature": "(query: str, limit: Optional[int] = None) -> str",
        },
        {
            "name": "create_tool_proxy",
            "description": "Create a callable proxy for executing a tool",
            "signature": "(server_name: str, tool_name: str) -> Callable",
        },
    ],
}
