#!/usr/bin/env python
"""
MCP Code Execution Server Entry Point

Standalone entry point for running the MCP server from VS Code or command line.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the server
from src.mcp_ce.server import mcp

if __name__ == "__main__":
    # Show info if requested
    if "--info" in sys.argv or "--discover" in sys.argv:
        from src.mcp_ce.server import show_sandbox_helpers

        show_sandbox_helpers()
    else:
        # Run the FastMCP server
        mcp.run()
