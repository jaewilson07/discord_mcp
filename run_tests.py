#!/usr/bin/env python
"""
Test runner for MCP Discord Server.

This script provides convenient commands to run tests for specific servers
or all tests at once.

Examples:
    # Run all Notion tests
    python run_tests.py notion

    # Run all Discord tests
    python run_tests.py discord

    # Run all tests
    python run_tests.py all

    # Run with coverage
    python run_tests.py notion --coverage

    # Run specific test file
    pytest tests/mcp_ce/tools/notion/test_search_notion.py -v
"""

import sys
import subprocess
from pathlib import Path


def run_tests(server: str, coverage: bool = False, verbose: bool = True):
    """
    Run tests for a specific server or all tests.

    Args:
        server: Server name (notion, discord, youtube, all)
        coverage: Whether to generate coverage report
        verbose: Whether to use verbose output
    """
    # Base pytest command
    cmd = ["pytest"]

    # Add path based on server
    if server == "all":
        cmd.append("test/")
    else:
        test_path = Path("test/mcp_ce/tools") / server
        if not test_path.exists():
            print(f"❌ Error: No tests found for server '{server}'")
            print(f"   Expected path: {test_path}")
            return 1
        cmd.append(str(test_path))

    # Add options
    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])

    # Add marker for specific server if not "all"
    if server != "all":
        cmd.extend(["-m", server])

    # Run pytest
    print(f"🧪 Running tests for: {server}")
    print(f"   Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)
    return result.returncode


def list_available_servers():
    """List available test servers."""
    tools_path = Path("test/mcp_ce/tools")
    if not tools_path.exists():
        print("❌ No test directory found")
        return

    servers = [
        d.name
        for d in tools_path.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ]

    print("📁 Available test servers:")
    for server in sorted(servers):
        test_files = list((tools_path / server).glob("test_*.py"))
        print(f"   - {server} ({len(test_files)} test files)")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("MCP Discord Server - Test Runner")
        print()
        print("Usage:")
        print("  python run_tests.py <server> [--coverage]")
        print()
        print("Arguments:")
        print("  server      Server name (notion, discord, youtube, all)")
        print("  --coverage  Generate coverage report (optional)")
        print()
        list_available_servers()
        print()
        print("Examples:")
        print("  python run_tests.py notion")
        print("  python run_tests.py all --coverage")
        return 1

    server = sys.argv[1].lower()
    coverage = "--coverage" in sys.argv or "-c" in sys.argv

    if server == "list":
        list_available_servers()
        return 0

    return run_tests(server, coverage=coverage)


if __name__ == "__main__":
    sys.exit(main())
