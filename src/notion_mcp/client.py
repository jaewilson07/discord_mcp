"""
Python client for interacting with the Notion MCP Server.

This client starts the Node.js-based Notion MCP server as a subprocess and
communicates with it via stdio transport.
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class NotionMCPClient:
    """Client for interacting with Notion MCP Server."""

    def __init__(self, notion_token: Optional[str] = None):
        """
        Initialize the Notion MCP Client.

        Args:
            notion_token: Notion integration token. If not provided, will look for
                         NOTION_TOKEN environment variable.
        """
        self.notion_token = notion_token
        self.process: Optional[subprocess.Popen] = None
        self.initialized = False
        self._request_id = 0

    async def start(self):
        """Start the Notion MCP server subprocess."""
        if self.process:
            return

        # Set up environment with Notion token
        env = {}
        if self.notion_token:
            env["NOTION_TOKEN"] = self.notion_token

        # Start the Node.js MCP server via npx
        self.process = subprocess.Popen(
            ["npx", "-y", "@notionhq/notion-mcp-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**subprocess.os.environ, **env},
            text=True,
            bufsize=1,
        )

        # Initialize the MCP connection
        await self._initialize()

    async def _initialize(self):
        """Initialize the MCP connection."""
        if self.initialized:
            return

        request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "notion-mcp-python-client", "version": "1.0.0"},
            },
        }

        response = await self._send_request(request)
        if "error" in response:
            raise Exception(f"Failed to initialize: {response['error']}")

        self.initialized = True
        logger.info("Notion MCP server initialized successfully")

    def _get_request_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise Exception("MCP server not started")

        # Send request
        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str)
        self.process.stdin.flush()

        # Read response
        response_str = self.process.stdout.readline()
        if not response_str:
            raise Exception("No response from MCP server")

        return json.loads(response_str)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available Notion API tools."""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/list",
            "params": {},
        }

        response = await self._send_request(request)
        if "error" in response:
            raise Exception(f"Failed to list tools: {response['error']}")

        return response.get("result", {}).get("tools", [])

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a Notion API tool.

        Args:
            tool_name: Name of the tool to call (e.g., "API-v1/search")
            arguments: Arguments to pass to the tool

        Returns:
            Tool response data
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        response = await self._send_request(request)
        if "error" in response:
            raise Exception(f"Tool call failed: {response['error']}")

        return response.get("result", {})

    async def search_pages(
        self, query: str, filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for Notion pages.

        Args:
            query: Search query string
            filter_type: Optional filter ("page" or "database")

        Returns:
            List of matching pages/databases
        """
        arguments = {"query": query}
        if filter_type:
            arguments["filter"] = {"property": "object", "value": filter_type}

        result = await self.call_tool("API-v1/search", arguments)
        return result.get("results", [])

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Get a Notion page by ID.

        Args:
            page_id: ID of the page to retrieve

        Returns:
            Page data
        """
        return await self.call_tool("API-v1/pages/{page_id}", {"page_id": page_id})

    async def create_page(
        self,
        parent_id: str,
        title: str,
        content: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Notion page.

        Args:
            parent_id: ID of the parent page or database
            title: Title of the new page
            content: Optional page content blocks

        Returns:
            Created page data
        """
        properties = {"title": {"title": [{"text": {"content": title}}]}}

        arguments = {
            "parent": {"page_id": parent_id},
            "properties": properties,
        }

        if content:
            arguments["children"] = content

        return await self.call_tool("API-v1/pages", arguments)

    async def update_page(
        self, page_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a Notion page.

        Args:
            page_id: ID of the page to update
            properties: Properties to update

        Returns:
            Updated page data
        """
        arguments = {"page_id": page_id, "properties": properties}
        return await self.call_tool("API-v1/pages/{page_id}", arguments)

    async def query_database(
        self, database_id: str, filter_obj: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query a Notion database.

        Args:
            database_id: ID of the database to query
            filter_obj: Optional filter object

        Returns:
            List of database pages
        """
        arguments = {"database_id": database_id}
        if filter_obj:
            arguments["filter"] = filter_obj

        result = await self.call_tool("API-v1/databases/{database_id}/query", arguments)
        return result.get("results", [])

    async def add_comment(self, page_id: str, comment_text: str) -> Dict[str, Any]:
        """
        Add a comment to a Notion page.

        Args:
            page_id: ID of the page to comment on
            comment_text: Comment text

        Returns:
            Created comment data
        """
        arguments = {
            "parent": {"page_id": page_id},
            "rich_text": [{"text": {"content": comment_text}}],
        }
        return await self.call_tool("API-v1/comments", arguments)

    async def stop(self):
        """Stop the MCP server subprocess."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            self.initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
