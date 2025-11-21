#!/usr/bin/env python3
"""
Daily Tumblr sync cron job script.

This script can be run via:
- Cron: `0 9 * * * /path/to/python /path/to/run_daily_tumblr_sync.py`
- GitHub Actions (scheduled workflow)
- Systemd timer
- Any other scheduler

Environment variables:
- DISCORD_DEV_MODE: Set to "true" to use DEV channels (default: false/PROD)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from mcp_ce.agentic_tools.graphs.tumblr_feed.daily_sync_tumblr_to_discord import (
    daily_sync_tumblr_to_discord,
)


async def main():
    """Run the daily Tumblr sync."""
    # Check if dev mode
    dev_mode = os.getenv("DISCORD_DEV_MODE", "false").lower() == "true"
    
    print("=" * 70)
    print("Daily Tumblr Sync Job")
    print("=" * 70)
    print(f"Mode: {'DEV' if dev_mode else 'PROD'}")
    print()
    
    result = await daily_sync_tumblr_to_discord(
        dev_mode=dev_mode,
        max_posts_per_blog=20,
    )
    
    # Exit with error code if failed
    if not result["success"]:
        print("❌ Sync failed!")
        sys.exit(1)
    else:
        print("✅ Sync completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

