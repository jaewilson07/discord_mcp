"""
Facebook Event Scraper MCP Agent

This agent scrapes Facebook event pages and extracts event details,
then optionally saves them to Notion. It uses existing MCP CE tools
for web scraping, content extraction, and Notion integration.
"""

import asyncio
import os
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import re

from mcp_agent.app import MCPApp

from dotenv import load_dotenv

load_dotenv()

from ....models.events import EventDetails

# Create the MCP app
app = MCPApp(name="facebook_event_scraper")


class EventScraperRequest(BaseModel):
    """Request for event scraping"""

    event_url: str = Field(description="Facebook event URL to scrape")
    save_to_notion: bool = Field(default=True, description="Whether to save to Notion")
    notion_database_id: Optional[str] = Field(
        default=None, description="Notion database ID"
    )


@app.tool
async def scrape_facebook_event(
    event_url: str,
    save_to_notion: bool = True,
    create_discord_event: bool = True,
    discord_server_id: Optional[str] = None,
    notion_database_id: Optional[str] = None,
    cookies: list = None,
    storage_state: str = None,
) -> str:
    """
    Scrape a Facebook event page and extract comprehensive event details.

    This tool extracts structured event information from a Facebook event URL,
    including date, time, location, description, and metadata. It can optionally
    save the event to Notion and create a Discord scheduled event.

    Args:
        event_url: Facebook event URL (e.g., https://www.facebook.com/events/123456789/)
        save_to_notion: Whether to save extracted details to Notion (default: True)
        create_discord_event: Whether to create a Discord scheduled event (default: True)
        discord_server_id: Discord server ID for event creation (uses first available server if not provided)
        notion_database_id: Notion database ID to save to (uses NOTION_DATABASE_ID env var if not provided)
        cookies: List of cookie dicts for authentication (e.g., from browser export)
        storage_state: Path to browser storage state JSON file (alternative to cookies)

    Returns:
        Event details in markdown format, with Notion page link and Discord event ID if created
    """
    async with app.run() as running_app:
        logger = running_app.logger

        logger.info(f"Scraping Facebook event", data={"url": event_url})

        try:
            # Step 1: Try to scrape the event page
            logger.info("Step 1: Attempting to scrape event page...")
            scraped_content = await _scrape_event_page(
                event_url, cookies, storage_state
            )

            if not scraped_content or len(scraped_content) < 100:
                logger.warning("Failed to scrape content (likely requires login)")
                return _generate_manual_instructions(
                    event_url, save_to_notion, notion_database_id
                )

            # Step 2: Extract structured event details using AI
            logger.info("Step 2: Extracting event details with AI...")
            event_details = await _extract_event_details(scraped_content, event_url)

            # Step 3: Generate markdown report
            logger.info("Step 3: Generating event report...")
            report = _generate_event_report(event_details)

            # Step 4: Optionally save to Notion
            notion_link = None
            if save_to_notion:
                logger.info("Step 4: Saving to Notion...")
                notion_link = await _save_to_notion(event_details, notion_database_id)

                if notion_link:
                    report += f"\n\n---\n\n✅ **Saved to Notion**: {notion_link}"
                else:
                    report += f"\n\n---\n\n⚠️ **Note**: Could not save to Notion (check NOTION_TOKEN and NOTION_DATABASE_ID)"

            # Step 5: Optionally create Discord event
            discord_event_id = None
            if create_discord_event:
                logger.info("Step 5: Creating Discord scheduled event...")
                discord_event_id = await _create_discord_event(
                    event_details, discord_server_id
                )

                if discord_event_id:
                    report += f"\n\n✅ **Discord Event Created**: ID {discord_event_id}"
                else:
                    report += f"\n\n⚠️ **Note**: Could not create Discord event (check DISCORD_TOKEN and server access)"

            return report

        except Exception as e:
            logger.error(f"Error scraping event", error=str(e))
            return f"Error: {str(e)}\n\n" + _generate_manual_instructions(
                event_url, save_to_notion, notion_database_id
            )


@app.tool
async def save_event_text_to_notion(
    event_text: str,
    event_url: Optional[str] = None,
    create_discord_event: bool = True,
    discord_server_id: Optional[str] = None,
    notion_database_id: Optional[str] = None,
) -> str:
    """
    Extract event details from manually copied text and save to Notion and/or Discord.

    Use this tool when automatic scraping fails due to Facebook login requirements.
    Copy the event details from Facebook, paste them here, and the tool will
    extract structured information and save it to Notion and create a Discord event.

    Args:
        event_text: Full text copied from Facebook event page
        event_url: Optional Facebook event URL for reference
        create_discord_event: Whether to create a Discord scheduled event (default: True)
        discord_server_id: Discord server ID for event creation (uses first available server if not provided)
        notion_database_id: Notion database ID to save to (uses NOTION_DATABASE_ID env var if not provided)

    Returns:
        Event details in markdown format with Notion page link and Discord event ID
    """
    async with app.run() as running_app:
        logger = running_app.logger

        logger.info("Processing manually copied event text")

        try:
            # Extract structured event details using AI
            logger.info("Extracting event details from text...")
            event_details = await _extract_event_details(
                event_text, event_url or "Manual entry"
            )

            # Generate markdown report
            report = _generate_event_report(event_details)

            # Save to Notion
            logger.info("Saving to Notion...")
            notion_link = await _save_to_notion(event_details, notion_database_id)

            if notion_link:
                report += f"\n\n---\n\n✅ **Saved to Notion**: {notion_link}"
            else:
                report += f"\n\n---\n\n⚠️ **Note**: Could not save to Notion (check NOTION_TOKEN and NOTION_DATABASE_ID)"

            # Create Discord event
            if create_discord_event:
                logger.info("Creating Discord scheduled event...")
                discord_event_id = await _create_discord_event(
                    event_details, discord_server_id
                )

                if discord_event_id:
                    report += f"\n\n✅ **Discord Event Created**: ID {discord_event_id}"
                else:
                    report += f"\n\n⚠️ **Note**: Could not create Discord event (check DISCORD_TOKEN and server access)"

            return report

        except Exception as e:
            logger.error(f"Error processing event text", error=str(e))
            return f"Error: {str(e)}"


# Helper functions using decoupled tools


async def _scrape_event_page(
    url: str, cookies: list = None, storage_state: str = None
) -> str:
    """Scrape event page using crawl4ai tool with optional authentication"""
    from ....tools.crawl4ai.crawl_website import crawl_website

    result = await crawl_website(
        url=url,
        extract_images=False,
        extract_links=False,
        word_count_threshold=5,
        headless=True,
        cookies=cookies,
        storage_state=storage_state,
        wait_for_selector=".x1n2onr6",  # Facebook content container
        js_code="window.scrollTo(0, document.body.scrollHeight);",  # Scroll to load lazy content
        save_to_notion=False,  # Don't save the raw page, just get content
    )

    if result.get("success"):
        content = result.get("content", {}).get("markdown", "")
        return content

    return ""


async def _extract_event_details(content: str, url: str) -> EventDetails:
    """Extract structured event details using generic AI extraction tool"""
    from ..extract_strucured_data.extract_structured_data import extract_event_details

    return await extract_event_details(text=content, url=url)


def _generate_event_report(event: EventDetails) -> str:
    """Generate comprehensive markdown report for event"""
    report = f"""# {event.title}

**Event URL**: {event.url}

## 📅 Date & Time

"""

    if event.date:
        report += f"**Date**: {event.date}\n\n"

    if event.start_time:
        time_str = f"**Start**: {event.start_time}"
        if event.end_time:
            time_str += f" - **End**: {event.end_time}"
        if event.timezone:
            time_str += f" ({event.timezone})"
        report += f"{time_str}\n\n"

    # Location section
    full_location = event.get_full_location()
    if full_location or event.is_online:
        report += "## 📍 Location\n\n"

        if event.is_online:
            report += "🌐 **Online Event**\n\n"
            if event.online_link:
                report += f"**Link**: {event.online_link}\n\n"
        elif full_location:
            report += f"{full_location}\n\n"

    # Organizer
    if event.organizer:
        report += "## 👤 Organizer\n\n"
        report += f"**{event.organizer}**"
        if event.organizer_profile:
            report += f" - [Profile]({event.organizer_profile})"
        report += "\n\n"

    # Category & Pricing
    if event.category or event.price:
        report += "## 🎫 Event Info\n\n"
        if event.category:
            report += f"**Category**: {event.category}\n\n"
        if event.price:
            report += f"**Price**: {event.price}\n\n"
        if event.ticket_url:
            report += f"**Tickets**: {event.ticket_url}\n\n"

    # Engagement
    if event.going_count or event.interested_count or event.capacity:
        report += "## 📊 Attendance\n\n"
        if event.going_count:
            report += f"✅ **Going**: {event.going_count} people\n\n"
        if event.interested_count:
            report += f"⭐ **Interested**: {event.interested_count} people\n\n"
        if event.capacity:
            report += f"**Capacity**: {event.capacity}\n\n"

    # Description
    if event.description:
        report += f"## 📝 Description\n\n{event.description}\n\n"

    # Cover image
    if event.cover_image_url:
        report += f"## 🖼️ Cover Image\n\n![Event Cover]({event.cover_image_url})\n\n"

    report += f"---\n\n*Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

    return report


async def _save_to_notion(
    event: EventDetails, database_id: Optional[str] = None
) -> Optional[str]:
    """Save comprehensive event details to Notion using create_notion_page tool"""
    from ....runtime import _execute_tool

    # Get database ID from parameter or environment
    db_id = database_id or os.getenv("NOTION_DATABASE_ID")
    if not db_id:
        return None

    # Format content for Notion using the same comprehensive format
    content = ""

    # Date & Time
    if event.date or event.start_time:
        content += "## 📅 Date & Time\n\n"
        if event.date:
            content += f"**Date**: {event.date}\n\n"
        if event.start_time:
            time_str = f"**Start**: {event.start_time}"
            if event.end_time:
                time_str += f" - **End**: {event.end_time}"
            if event.timezone:
                time_str += f" ({event.timezone})"
            content += f"{time_str}\n\n"

    # Location
    full_location = event.get_full_location()
    if full_location or event.is_online:
        content += "## 📍 Location\n\n"
        if event.is_online:
            content += "🌐 **Online Event**\n\n"
            if event.online_link:
                content += f"**Link**: {event.online_link}\n\n"
        elif full_location:
            content += f"{full_location}\n\n"

    # Organizer
    if event.organizer:
        content += "## 👤 Organizer\n\n"
        content += f"**{event.organizer}**"
        if event.organizer_profile:
            content += f" - [Profile]({event.organizer_profile})"
        content += "\n\n"

    # Event Info
    if event.category or event.price:
        content += "## 🎫 Event Info\n\n"
        if event.category:
            content += f"**Category**: {event.category}\n\n"
        if event.price:
            content += f"**Price**: {event.price}\n\n"
        if event.ticket_url:
            content += f"**Tickets**: {event.ticket_url}\n\n"

    # Attendance
    if event.going_count or event.interested_count or event.capacity:
        content += "## 📊 Attendance\n\n"
        if event.going_count:
            content += f"✅ **Going**: {event.going_count} people\n\n"
        if event.interested_count:
            content += f"⭐ **Interested**: {event.interested_count} people\n\n"
        if event.capacity:
            content += f"**Capacity**: {event.capacity}\n\n"

    # Description
    if event.description:
        content += f"## 📝 Description\n\n{event.description}\n\n"

    # Cover image
    if event.cover_image_url:
        content += f"## 🖼️ Cover Image\n\n![Event Cover]({event.cover_image_url})\n\n"

    content += f"**Event URL**: {event.url}"

    try:
        result = await _execute_tool(
            "notion",
            "create_notion_page",
            title=event.title,
            content=content,
            parent_type="database",
            parent_id=db_id,
        )

        if result.get("success"):
            page_data = result.get("data", {})
            return page_data.get("url")

        return None

    except Exception as e:
        print(f"Error saving to Notion: {e}")
        return None


async def _create_discord_event(
    event: EventDetails, server_id: Optional[str] = None
) -> Optional[str]:
    """Create Discord scheduled event from event details"""
    from ....runtime import _execute_tool

    # Get server ID from parameter or use first available server
    if not server_id:
        # Try to get server ID from environment or use default
        server_id = os.getenv("DISCORD_SERVER_ID")
        if not server_id:
            # Get first available server from Discord bot
            try:
                servers_result = await _execute_tool("discord", "list_servers")
                if servers_result.get("success"):
                    servers = servers_result.get("servers", [])
                    if servers:
                        server_id = servers[0].get("id")
            except Exception as e:
                print(f"Error getting Discord servers: {e}")
                return None

    if not server_id:
        print("No Discord server ID available")
        return None

    # Parse datetime for Discord
    start_dt, end_dt = event.get_datetime_for_discord()
    if not start_dt:
        print("Could not parse event date/time for Discord")
        return None

    # Build description
    description_parts = []
    if event.organizer:
        description_parts.append(f"Host: {event.organizer}")
    if event.price:
        description_parts.append(f"Price: {event.price}")
    if event.description:
        # Truncate description to Discord's limit (1000 characters)
        desc = event.description[:950]
        if len(event.description) > 950:
            desc += "..."
        description_parts.append(desc)

    description = "\n\n".join(description_parts) if description_parts else None

    # Determine entity type and location
    entity_type = "external"
    location = None

    if event.is_online:
        location = event.online_link or "Online Event"
    else:
        full_loc = event.get_full_location()
        if full_loc:
            # Truncate location to Discord's limit (100 characters)
            location = full_loc[:97] + "..." if len(full_loc) > 100 else full_loc
        else:
            location = "See event details"

    try:
        result = await _execute_tool(
            "discord",
            "create_scheduled_event",
            server_id=server_id,
            name=event.title[:100],  # Discord max 100 characters
            start_time=start_dt.isoformat(),
            end_time=end_dt.isoformat() if end_dt else None,
            description=description,
            entity_type=entity_type,
            location=location,
        )

        if result.get("success"):
            return result.get("event_id")
        else:
            print(f"Discord event creation failed: {result.get('error')}")
            return None

    except Exception as e:
        print(f"Error creating Discord event: {e}")
        return None


def _generate_manual_instructions(
    url: str, save_to_notion: bool, notion_database_id: Optional[str]
) -> str:
    """Generate instructions for manual event extraction"""
    return f"""# Facebook Event Scraping Failed

Facebook pages require authentication and cannot be automatically scraped.

## Manual Extraction Instructions

1. **Open the event in your browser**: {url}

2. **Copy all the event text**:
   - Press Ctrl+A (Select All)
   - Press Ctrl+C (Copy)

3. **Use the manual extraction tool**:
   - Call the `save_event_text_to_notion` tool
   - Paste the copied text
   - The tool will extract details and save to Notion

## Example Usage

```python
# After copying event details from Facebook
result = await save_event_text_to_notion(
    event_text="[paste your copied text here]",
    event_url="{url}",
    notion_database_id="{notion_database_id or 'your-database-id'}"
)
```

---

💡 **Tip**: Facebook's anti-scraping protections prevent automated access. 
Manual copying is the most reliable method for extracting event details.
"""


# Main entry point for testing
if __name__ == "__main__":
    import sys

    async def test():
        if len(sys.argv) < 2:
            print("Usage: python facebook_event_agent.py <facebook_event_url>")
            sys.exit(1)

        event_url = sys.argv[1]

        result = await scrape_facebook_event(event_url=event_url, save_to_notion=True)

        print(result)

    asyncio.run(test())
