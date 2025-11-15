"""Main entry point for mcp_ce package when run as module."""

import sys
import os

# Add src to path for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from src.mcp_ce import main

if __name__ == "__main__":
    main()
