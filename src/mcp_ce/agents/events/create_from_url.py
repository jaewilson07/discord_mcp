"""
Scrape website for event information and create Discord event.
"""

import asyncio
from typing import Optional, Dict, Any


async def create_event_from_url(
    url: str,
    discord_server_id: Optional[str] = None,
    save_to_notion: bool = True,
    notion_database_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Scrape a website for event information and create a Discord scheduled event.

    This workflow:
    1. Scrapes the URL to extract content
    2. Uses AI to extract structured event details (EventDetails model)
    3. Creates a Discord scheduled event
    4. Optionally saves event details to Notion

    Args:
        url: Website URL to scrape for event information
        discord_server_id: Discord server ID to create event in (uses first available if not provided)
        save_to_notion: Whether to save event details to Notion (default: True)
        notion_database_id: Notion database ID (uses NOTION_DATABASE_ID env var if not provided)

    Returns:
        Dict containing:
        - success: bool indicating if workflow succeeded
        - event: EventDetails object
        - discord_event_id: Discord event ID (if created)
        - discord_event_url: Discord event URL (if created)
        - notion_page_id: Notion page ID (if saved)
        - errors: list of any errors encountered

    Example:
        result = await create_event_from_url(
            url="https://www.bluesmuse.dance/",
            save_to_notion=True
        )

        if result['success']:
            print(f"Created event: {result['event'].title}")
            print(f"Discord: {result['discord_event_url']}")
    """
    import os
    from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
    from mcp_ce.agents.extract_structured_data import extract_event_details
    from mcp_ce.tools.discord._bot_helper import get_bot, is_bot_ready
    from datetime import datetime

    errors = []
    result = {
        "success": False,
        "event": None,
        "discord_event_id": None,
        "discord_event_url": None,
        "notion_page_id": None,
        "errors": errors,
    }

    try:
        # Step 1: Scrape the website
        print(f"📡 Scraping {url}...")
        scrape_result = await crawl_website(
            url=url,
            extract_images=False,
            extract_links=False,
            word_count_threshold=5,
            headless=True,
            save_to_notion=False,  # We'll handle Notion saving separately
        )

        if not scrape_result.get("success"):
            errors.append(f"Scraping failed: {scrape_result.get('error')}")
            return result

        content = scrape_result.get("content", {}).get("markdown", "")
        print(f"✅ Scraped {len(content)} characters")

        # Step 2: Extract event details with quality control (evaluator-optimizer)
        print(f"\n🤖 Step 2: Extracting event details with quality control...")
        from mcp_ce.tools.events.evaluator_optimizer import (
            extract_event_with_quality_control,
        )

        event, quality_score = await extract_event_with_quality_control(
            url=url, content=content, quality_threshold=0.7, max_iterations=3
        )

        result["event"] = event
        result["quality_score"] = {
            "overall": quality_score.overall_score,
            "completeness": quality_score.completeness,
            "accuracy": quality_score.accuracy,
            "confidence": quality_score.confidence,
            "issues": quality_score.issues,
            "is_acceptable": quality_score.is_acceptable(),
        }

        print(f"\n✅ Final extraction quality: {quality_score.overall_score:.2f}")
        print(f"   Event: {event.title}")
        if event.date:
            print(f"   Date: {event.date}")
        if event.start_time:
            print(f"   Time: {event.start_time}")

        # Step 3: Create Discord event
        if is_bot_ready():
            print(f"📅 Creating Discord event...")
            try:
                bot = get_bot()

                # Get server
                if discord_server_id:
                    guild = bot.get_guild(int(discord_server_id))
                    if not guild:
                        errors.append(
                            f"Could not find server with ID: {discord_server_id}"
                        )
                        guild = None
                else:
                    guild = bot.guilds[0] if bot.guilds else None

                if guild:
                    # Parse datetime
                    start_dt, end_dt = event.get_datetime_for_discord()

                    if start_dt:
                        # Prepare event details
                        location = event.get_full_location() or "See event details"
                        if len(location) > 100:
                            location = location[:97] + "..."

                        description_parts = []
                        if event.organizer:
                            description_parts.append(f"Host: {event.organizer}")
                        if event.price:
                            description_parts.append(f"Price: {event.price}")
                        if event.description:
                            desc = (
                                event.description[:900]
                                if len(event.description) > 900
                                else event.description
                            )
                            description_parts.append(desc)

                        description = (
                            "\n\n".join(description_parts)
                            if description_parts
                            else None
                        )

                        # Create event
                        import discord

                        scheduled_event = await guild.create_scheduled_event(
                            name=event.title[:100],
                            start_time=start_dt,
                            end_time=end_dt,
                            description=description,
                            entity_type=discord.EntityType.external,
                            location=location,
                        )

                        result["discord_event_id"] = str(scheduled_event.id)
                        result["discord_event_url"] = scheduled_event.url
                        print(f"✅ Discord event created: {scheduled_event.url}")
                    else:
                        errors.append("Could not parse event date/time for Discord")
                else:
                    errors.append("No Discord server available")

            except Exception as e:
                errors.append(f"Discord event creation failed: {str(e)}")
        else:
            errors.append("Discord bot not ready")

        # Step 4: Save to Notion
        if save_to_notion:
            print(f"💾 Saving to Notion...")
            try:
                from mcp_ce.tools.notion._client_helper import (
                    get_data_source_id_from_database,
                    query_data_source,
                    create_page,
                    update_page,
                    delete_all_blocks,
                    append_blocks,
                )
                from notion_blockify import Blockizer

                db_id = notion_database_id or os.getenv("NOTION_DATABASE_ID")
                if not db_id:
                    errors.append("NOTION_DATABASE_ID not configured")
                else:
                    # Get data source
                    data_source_id = await get_data_source_id_from_database(db_id)

                    # Check for existing
                    existing = await query_data_source(
                        data_source_id,
                        filter_obj={"property": "URL", "url": {"equals": url}},
                    )

                    # Prepare content
                    blockizer = Blockizer()

                    content_md = f"""## 📅 Event Details

**Date**: {event.date or 'TBD'}
**Time**: {event.start_time or 'TBD'} - {event.end_time or 'TBD'}
**Location**: {event.get_full_location() or 'TBD'}

## 📝 Description

{event.description or 'No description available'}

## 🎫 Event Info

**Organizer**: {event.organizer or 'N/A'}
**Price**: {event.price or 'N/A'}
**Category**: {event.category or 'N/A'}
"""

                    blocks = blockizer.convert(content_md)

                    # Properties
                    properties = {
                        "Name": {"title": [{"text": {"content": event.title[:100]}}]},
                        "URL": {"url": url},
                        "Status": {"select": {"name": "Event"}},
                        "Scrape Date": {"date": {"start": datetime.now().isoformat()}},
                    }

                    existing_pages = existing.get("results", [])

                    if existing_pages:
                        existing_page = existing_pages[0]
                        page_id = existing_page["id"]
                        lock_status = (
                            existing_page.get("properties", {})
                            .get("Lock", {})
                            .get("checkbox", False)
                        )

                        if not lock_status:
                            # Update
                            await update_page(page_id, properties)
                            await delete_all_blocks(page_id)
                            for i in range(0, len(blocks), 100):
                                chunk = blocks[i : i + 100]
                                await append_blocks(page_id, chunk)
                            result["notion_page_id"] = page_id
                            print(f"✅ Updated Notion page")
                        else:
                            errors.append("Notion page is locked - creating new one")
                            # Create new
                            initial_blocks = blocks[:100]
                            remaining = blocks[100:]
                            created = await create_page(
                                db_id, properties, initial_blocks
                            )
                            page_id = created["id"]
                            for i in range(0, len(remaining), 100):
                                await append_blocks(page_id, remaining[i : i + 100])
                            result["notion_page_id"] = page_id
                            print(f"✅ Created new Notion page")
                    else:
                        # Create new
                        initial_blocks = blocks[:100]
                        remaining = blocks[100:]
                        created = await create_page(db_id, properties, initial_blocks)
                        page_id = created["id"]
                        for i in range(0, len(remaining), 100):
                            await append_blocks(page_id, remaining[i : i + 100])
                        result["notion_page_id"] = page_id
                        print(f"✅ Created Notion page")

            except Exception as e:
                errors.append(f"Notion save failed: {str(e)}")

        result["success"] = len(errors) == 0 or (result["event"] is not None)
        return result

    except Exception as e:
        errors.append(f"Workflow failed: {str(e)}")
        return result


# Test
if __name__ == "__main__":

    async def test():
        result = await create_event_from_url(
            url="https://www.bluesmuse.dance/", save_to_notion=True
        )

        print(f"\n📊 Result:")
        print(f"  Success: {result['success']}")
        if result["event"]:
            print(f"  Event: {result['event'].title}")
            print(f"  Date: {result['event'].date}")
        if result["discord_event_url"]:
            print(f"  Discord: {result['discord_event_url']}")
        if result["notion_page_id"]:
            print(f"  Notion: {result['notion_page_id']}")
        if result["errors"]:
            print(f"  Errors: {result['errors']}")

    asyncio.run(test())
