"""
Test zero-context discovery workflow
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_ce.runtime import (
    discovered_servers,
    list_servers,
    query_tool_docs,
    search_tool_docs,
    capability_summary,
)
from mcp_ce.sandbox import execute_python


async def test_discovery_workflow():
    """Test the zero-context discovery workflow"""

    print("=" * 80)
    print("TEST 1: Capability Summary")
    print("=" * 80)
    print(capability_summary())
    print()

    print("=" * 80)
    print("TEST 2: Discover Servers (Zero-Context)")
    print("=" * 80)
    servers = discovered_servers()
    print(f"Found {len(servers)} server(s):")
    for server in servers:
        print(f"  - {server['name']}: {server['description']}")
    print()

    print("=" * 80)
    print("TEST 3: List Server Names")
    print("=" * 80)
    server_names = list_servers()
    print(f"Server names: {server_names}")
    print()

    print("=" * 80)
    print("TEST 4: Query Tool Docs (On-Demand Schema Loading)")
    print("=" * 80)
    print("Summary for 'url_ping' server:")
    summary = query_tool_docs("url_ping", detail="summary")
    print(summary)
    print()

    print("Full docs for 'ping_url' tool:")
    full_docs = query_tool_docs("url_ping", tool="ping_url", detail="full")
    print(full_docs)
    print()

    print("=" * 80)
    print("TEST 5: Search Tool Docs")
    print("=" * 80)
    results = search_tool_docs("ping")
    print(f"Search results for 'ping':")
    print(results)
    print()

    print("=" * 80)
    print("TEST 6: Execute Python in Sandbox (Discovery Workflow)")
    print("=" * 80)

    code = """
import json

# Step 1: Discover available servers
print("Step 1: Discovering servers...")
servers = discovered_servers()
print(f"Available servers: {json.dumps(servers, indent=2)}")

# Step 2: Query tool docs for url_ping
print("\\nStep 2: Querying tool docs...")
docs = query_tool_docs("url_ping", tool="ping_url", detail="summary")
print(f"Tool docs: {docs}")

# Step 3: Create tool proxy and call it
print("\\nStep 3: Creating tool proxy and calling...")

async def main():
    from mcp_ce.runtime import create_tool_proxy
    
    # Create proxy
    ping = create_tool_proxy("url_ping", "ping_url")
    
    # Call tool
    result = await ping(url="https://www.google.com", timeout=10)
    
    print(f"\\nPing result: {json.dumps(result, indent=2)}")
    return result

# main() will be automatically awaited
"""

    print("Executing code in sandbox:")
    print("-" * 80)
    print(code)
    print("-" * 80)
    print()

    result = await execute_python(code, timeout=30)

    print("Execution result:")
    print(f"Success: {result['success']}")
    print(f"\nStdout:\n{result['stdout']}")

    if result["stderr"]:
        print(f"\nStderr:\n{result['stderr']}")

    if result["error"]:
        print(f"\nError: {result['error']}")

    if result["result"]:
        print(f"\nReturn value: {result['result']}")

    print()


if __name__ == "__main__":
    asyncio.run(test_discovery_workflow())
