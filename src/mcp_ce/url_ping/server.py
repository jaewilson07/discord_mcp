"""URL Ping MCP Server Configuration"""
from typing import Optional
import os

# For a simple local MCP server, we'll create a minimal implementation
# This will act as both the server and tool host
_server = None
_connected: bool = False


class SimpleMCPServer:
    """Simple MCP server for URL ping functionality"""
    
    def __init__(self):
        self.name = "url_ping"
        self.tools = {
            "ping_url": {
                "description": "Ping a URL and return the response status",
                "parameters": {
                    "url": {
                        "type": "string",
                        "description": "The URL to ping",
                        "required": True
                    }
                }
            }
        }
    
    async def connect(self):
        """Connect to the server (no-op for local server)"""
        print(f"Connected to {self.name} MCP server")
    
    async def call_tool(self, name: str, arguments: dict):
        """Call a tool with the given arguments"""
        if name == "ping_url":
            from .ping_url import ping_url
            return await ping_url(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")


def get_server() -> SimpleMCPServer:
    """Get the URL Ping MCP server instance (singleton)"""
    global _server
    if _server is None:
        _server = SimpleMCPServer()
    return _server


async def ensure_connected() -> SimpleMCPServer:
    """Ensure the server is connected, connect if not"""
    global _connected
    server = get_server()
    
    if not _connected:
        await server.connect()
        _connected = True
    
    return server


async def call_tool(tool_name: str, arguments: dict):
    """Call a tool on the MCP server with the given arguments"""
    server = await ensure_connected()
    return await server.call_tool(tool_name, arguments)


# Tool discovery - run with: python src/mcp_ce/url_ping/server.py
if __name__ == "__main__":
    import asyncio
    
    async def discover_tools():
        print("Discovering tools from MCP server...")
        server = await ensure_connected()
        
        print(f"\nFound {len(server.tools)} tool(s):\n")
        for tool_name, tool_info in server.tools.items():
            print(f"Tool: {tool_name}")
            print(f"  Description: {tool_info['description']}")
            print(f"  Parameters:")
            for param_name, param_info in tool_info['parameters'].items():
                param_type = param_info.get('type', 'any')
                param_desc = param_info.get('description', '')
                required = param_info.get('required', False)
                print(f"    - {param_name}: {param_type} {'(required)' if required else '(optional)'}")
                if param_desc:
                    print(f"      {param_desc}")
            print()
    
    asyncio.run(discover_tools())
