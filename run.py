#!/usr/bin/env python3
"""
Simple runner script for the Discord MCP server.
Usage: python run.py
"""

import asyncio
import sys
from src.discord_mcp import main

if __name__ == "__main__":
    try:
        print("🚀 Starting Discord MCP Server...")
        print("📝 Loading configuration from .env file...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down Discord MCP server...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
