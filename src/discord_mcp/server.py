import sys
import asyncio
import logging
from typing import Any, List
from functools import wraps
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .bot import create_bot, get_discord_token
from .tools import get_tool_definitions
from .handlers import handle_tool_call


def _configure_windows_stdout_encoding():
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


_configure_windows_stdout_encoding()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-mcp-server")

# Get Discord token
DISCORD_TOKEN = get_discord_token()

# Initialize Discord bot
bot = create_bot()

# Initialize MCP server
app = Server("discord-server")

# Store Discord client reference
discord_client = None


@bot.event
async def on_ready():
    global discord_client
    discord_client = bot
    logger.info(f"Logged in as {bot.user.name}")


# Helper function to ensure Discord client is ready
def require_discord_client(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not discord_client:
            raise RuntimeError("Discord client not ready")
        return await func(*args, **kwargs)

    return wrapper


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available Discord tools."""
    return get_tool_definitions()


@app.call_tool()
@require_discord_client
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle Discord tool calls."""
    return await handle_tool_call(discord_client, name, arguments)


async def main():

    # Start Discord bot in the background
    asyncio.create_task(bot.start(DISCORD_TOKEN))

    # Run MCP server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
