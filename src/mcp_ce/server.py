"""MCP Code Execution Server with Zero-Context Discovery

FastMCP-based server following elusznik's zero-context discovery pattern.
Provides a single `run_python` tool that executes code in a sandbox with runtime helpers.

Zero-Context Discovery (~200 tokens):
- LLM calls discovered_servers() to see available servers (no schemas loaded)
- LLM calls query_tool_docs(server) to hydrate specific tool schemas on-demand
- LLM writes Python code using create_tool_proxy() to call tools
- Code executes in sandbox with ~200 token overhead regardless of server count

Traditional MCP (~30K tokens):
- All tool schemas preloaded into context
- Direct tool invocation by LLM
- Context grows linearly with number of tools
"""

from fastmcp import FastMCP
from typing import Optional
import json

# Create FastMCP server instance
mcp = FastMCP("MCP Code Execution Sandbox")

# Import runtime and sandbox
from .runtime import SANDBOX_HELPERS_SUMMARY
from .sandbox import execute_python


@mcp.tool()
async def run_python(code: str, timeout: Optional[int] = 30) -> str:
    """
    Execute Python code in a sandboxed environment with MCP runtime helpers.

    The sandbox provides discovery helpers for zero-context MCP access:

    **Discovery Helpers:**
    - `discovered_servers()` - List available MCP servers (no schemas loaded)
    - `list_servers()` - Get server names only
    - `query_tool_docs(server, tool=None, detail="summary")` - Load tool schemas on-demand
    - `search_tool_docs(query, limit=None)` - Fuzzy search for tools
    - `create_tool_proxy(server, tool)` - Create callable for tool execution

    **Workflow:**
    1. Discover servers: `servers = discovered_servers()`
    2. Query tools: `docs = query_tool_docs("url_ping")`
    3. Create proxy: `ping = create_tool_proxy("url_ping", "ping_url")`
    4. Execute: `result = await ping(url="https://example.com")`

    **Example:**
    ```python
    # Discover available servers
    import json
    servers = discovered_servers()
    print(f"Available servers: {json.dumps(servers, indent=2)}")

    # Query tool docs for url_ping server
    docs = query_tool_docs("url_ping", detail="full")
    print(f"Tool docs: {docs}")

    # Create tool proxy and call it
    async def main():
        ping = create_tool_proxy("url_ping", "ping_url")
        result = await ping(url="https://www.google.com", timeout=10)
        return result

    # main() will be automatically awaited if defined
    ```

    Args:
        code: Python code to execute (can define async main() function)
        timeout: Execution timeout in seconds (default: 30)

    Returns:
        JSON string with execution results:
        - success: bool
        - stdout: captured output
        - stderr: captured errors
        - result: return value from main() if defined
        - error: error message if failed
    """
    result = await execute_python(code, timeout)
    return json.dumps(result, indent=2, default=str)


# Discovery helper for CLI
def show_sandbox_helpers():
    """Display sandbox helpers summary (zero-context discovery info)"""
    print("=" * 80)
    print("MCP CODE EXECUTION SANDBOX - ZERO-CONTEXT DISCOVERY")
    print("=" * 80)
    print()
    print(SANDBOX_HELPERS_SUMMARY["description"])
    print()
    print("Available Runtime Helpers:")
    print("-" * 80)

    for helper in SANDBOX_HELPERS_SUMMARY["helpers"]:
        print(f"\n{helper['name']}{helper['signature']}")
        print(f"  {helper['description']}")

    print()
    print("=" * 80)
    print("Context Overhead: ~200 tokens (constant, regardless of server count)")
    print("Traditional MCP: ~30K tokens (grows with tool count)")
    print("=" * 80)


if __name__ == "__main__":
    import sys

    # Show sandbox helpers info
    if "--info" in sys.argv or "--discover" in sys.argv:
        show_sandbox_helpers()
    else:
        # Run the FastMCP server
        mcp.run()
