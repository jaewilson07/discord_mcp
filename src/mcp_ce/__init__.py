"""MCP Code Execution Server Package

Zero-context discovery pattern implementation with FastMCP.
"""

from . import server
import asyncio
import tracemalloc

__version__ = "0.1.0"


def main():
    """Main entry point for the package."""
    import sys

    # Enable tracemalloc for better debugging
    tracemalloc.start()

    # Check for --info or --discover flag
    if "--info" in sys.argv or "--discover" in sys.argv:
        server.show_sandbox_helpers()
        return

    try:
        # Run the FastMCP server
        server.mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down MCP Code Execution server...")
    except Exception as e:
        print(f"Error running MCP Code Execution server: {e}")
        raise


# Expose important items at package level
from .server import mcp, run_python
from .runtime import (
    discovered_servers,
    list_servers,
    query_tool_docs,
    search_tool_docs,
    capability_summary,
    SANDBOX_HELPERS_SUMMARY,
)

__all__ = [
    "main",
    "server",
    "mcp",
    "run_python",
    "discovered_servers",
    "list_servers",
    "query_tool_docs",
    "search_tool_docs",
    "capability_summary",
    "SANDBOX_HELPERS_SUMMARY",
]
