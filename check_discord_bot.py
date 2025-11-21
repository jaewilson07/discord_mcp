"""Check Discord bot status."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from mcp_ce.tools.discord.list_servers import list_servers
from mcp_ce.tools.discord._bot_helper import is_bot_ready

async def main():
    print(f"Bot ready: {is_bot_ready()}")
    if is_bot_ready():
        result = await list_servers()
        print(f"List servers success: {result.is_success}")
        if result.is_success and result.result:
            servers = result.result.servers
            print(f"Found {len(servers)} servers:")
            for s in servers[:3]:
                print(f"  - {s['name']} (ID: {s['id']})")
            if servers:
                print(f"\nUsing first server: {servers[0]['name']}")
                print(f"Set DISCORD_SERVER_ID={servers[0]['id']}")

asyncio.run(main())

