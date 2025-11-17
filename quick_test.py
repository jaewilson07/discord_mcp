#!/usr/bin/env python
"""
Quick test helper - Run a single test function quickly.

Examples:
    # Run a single test
    python quick_test.py test_search_pages

    # Run test from specific file
    python quick_test.py test_create_page_at_workspace_root

    # Run with verbose output
    python quick_test.py test_search_pages -v
"""

import sys
import subprocess


def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py <test_name> [pytest_args...]")
        print()
        print("Examples:")
        print("  python quick_test.py test_search_pages")
        print("  python quick_test.py test_create_page -v")
        return 1

    test_name = sys.argv[1]
    extra_args = sys.argv[2:]

    # Build pytest command
    cmd = ["pytest", "-k", test_name] + extra_args

    print(f"🔍 Running test: {test_name}")
    print(f"   Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
