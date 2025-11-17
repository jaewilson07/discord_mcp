"""Test tool registration and discovery."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import pytest

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

# Trigger tool imports at module level
import mcp_ce.tools.discord
import mcp_ce.tools.notion
import mcp_ce.tools.youtube
import mcp_ce.tools.url_ping
import mcp_ce.tools.crawl4ai

from registry import get_registry


def test_registry_imports():
    """Test that registry module imports correctly."""
    assert get_registry is not None


def test_tool_discovery():
    """Test that tools are auto-discovered and registered."""
    registry = get_registry()

    registry = get_registry()

    # Verify registry is not empty
    assert len(registry) > 0, "Registry should contain at least one server"

    # Verify expected servers are registered
    expected_servers = {"discord", "url_ping", "youtube", "notion", "crawl4ai"}
    registered_servers = set(registry.keys())

    # Check that at least some expected servers are present
    assert (
        len(expected_servers & registered_servers) > 0
    ), f"Expected servers {expected_servers}, got {registered_servers}"

    # Verify each server has tools
    for server, tools in registry.items():
        assert len(tools) > 0, f"Server {server} should have at least one tool"


def test_discord_tools_registered():
    """Test that Discord tools are properly registered."""
    registry = get_registry()

    # Discord should be registered
    assert "discord" in registry, "Discord server should be registered"

    discord_tools = registry["discord"]

    # Should have multiple tools
    assert (
        len(discord_tools) >= 10
    ), f"Discord should have at least 10 tools, got {len(discord_tools)}"

    # Check for some known tools
    expected_tools = {"send_message", "get_channels", "get_server_info"}
    registered_tool_names = set(discord_tools.keys())

    for tool in expected_tools:
        assert (
            tool in registered_tool_names
        ), f"Discord tool '{tool}' should be registered"


def test_tool_counts():
    """Test that expected number of tools are registered."""
    registry = get_registry()

    # Expected tool counts (approximate, may change as tools are added)
    expected_counts = {
        "discord": 19,
        "url_ping": 1,
        "youtube": 3,
        "notion": 6,
        "crawl4ai": 3,
    }

    for server, expected_count in expected_counts.items():
        if server in registry:
            actual_count = len(registry[server])
            assert (
                actual_count >= expected_count
            ), f"Server '{server}' should have at least {expected_count} tools, got {actual_count}"


def print_registry_info():
    """Helper function to print registry info (not a test)."""
    registry = get_registry()

    print(f"\nRegistered servers: {list(registry.keys())}")

    total_tools = sum(len(tools) for tools in registry.values())
    print(f"Total tools registered: {total_tools}\n")

    for server, tools in sorted(registry.items()):
        print(f"{server} ({len(tools)} tools):")
        for tool in sorted(tools.keys()):
            print(f"  - {tool}")
        print()


if __name__ == "__main__":
    if HAS_PYTEST:
        # Run tests with pytest
        pytest.main([__file__, "-v", "-s"])

        # Print registry info
        print("\n" + "=" * 60)
        print("REGISTRY INFORMATION")
        print("=" * 60)
        print_registry_info()
    else:
        # Run tests manually without pytest
        print("Running tests without pytest...\n")

        try:
            test_registry_imports()
            print("✅ test_registry_imports passed")
        except AssertionError as e:
            print(f"❌ test_registry_imports failed: {e}")

        try:
            test_tool_discovery()
            print("✅ test_tool_discovery passed")
        except AssertionError as e:
            print(f"❌ test_tool_discovery failed: {e}")

        try:
            test_discord_tools_registered()
            print("✅ test_discord_tools_registered passed")
        except AssertionError as e:
            print(f"❌ test_discord_tools_registered failed: {e}")

        try:
            test_tool_counts()
            print("✅ test_tool_counts passed")
        except AssertionError as e:
            print(f"❌ test_tool_counts failed: {e}")

        # Print registry info
        print("\n" + "=" * 60)
        print("REGISTRY INFORMATION")
        print("=" * 60)
        print_registry_info()
