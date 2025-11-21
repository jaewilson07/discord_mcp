"""
Graph workflow: Scrape website → Extract event → Create Discord event.

This workflow:
1. Scrapes a website URL to extract content
2. Extracts structured event details from the content
3. Creates a Discord scheduled event from the extracted details
"""

from .create_discord_event_from_url import create_discord_event_from_url

__all__ = ["create_discord_event_from_url"]

