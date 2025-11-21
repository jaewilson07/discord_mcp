"""
Scrape website for event information, save to Supabase, and create Discord event.

This workflow extends the base graph workflow (create_discord_event_from_url) by adding
Supabase storage functionality.

Workflow:
1. Scrapes the URL to extract content
2. Saves scraped content to Supabase (optional)
3. Uses AI to extract structured event details (EventDetails model)
4. Creates a Discord scheduled event

For a simpler workflow without Supabase, see:
    mcp_ce.agentic_tools.graphs.create_discord_event_from_url.create_discord_event_from_url
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
import logfire

from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
from mcp_ce.tools.supabase.add_document import add_document
from mcp_ce.tools.discord.create_scheduled_event import create_scheduled_event
from mcp_ce.tools.discord.list_servers import list_servers
from mcp_ce.tools.discord._bot_helper import is_bot_ready
from mcp_ce.tools.events.evaluator_optimizer import extract_event_with_quality_control
from mcp_ce.models.events import EventDetails


@logfire.instrument()
async def create_event_from_url_with_supabase(
    url: str,
    discord_server_id: Optional[str] = None,
    save_to_supabase: bool = True,
    supabase_table_name: str = "documents",
    quality_threshold: float = 0.7,
    max_iterations: int = 3,
) -> Dict[str, Any]:
    """
    Scrape a website for event information, save to Supabase, and create a Discord scheduled event.

    This workflow:
    1. Scrapes the URL to extract content
    2. Saves scraped content to Supabase (if enabled)
    3. Uses AI to extract structured event details (EventDetails model) with quality control
    4. Creates a Discord scheduled event

    Args:
        url: Website URL to scrape for event information
        discord_server_id: Discord server ID to create event in (uses first available if not provided)
        save_to_supabase: Whether to save scraped content to Supabase (default: True)
        supabase_table_name: Supabase table name for storing documents (default: "documents")
        quality_threshold: Minimum quality score for event extraction (default: 0.7)
        max_iterations: Maximum optimization iterations for extraction (default: 3)

    Returns:
        Dict containing:
        - success: bool indicating if workflow succeeded
        - event: EventDetails object
        - quality_score: dict with quality metrics
        - discord_event_id: Discord event ID (if created)
        - discord_event_url: Discord event URL (if created)
        - supabase_document_id: Supabase document ID (if saved)
        - errors: list of any errors encountered

    Example:
        result = await create_event_from_url_with_supabase(
            url="https://www.bluesmuse.dance/",
            save_to_supabase=True
        )

        if result['success']:
            print(f"Created event: {result['event'].title}")
            print(f"Discord: {result['discord_event_url']}")
            print(f"Supabase: {result['supabase_document_id']}")
    """
    errors = []
    result = {
        "success": False,
        "event": None,
        "quality_score": None,
        "discord_event_id": None,
        "discord_event_url": None,
        "supabase_document_id": None,
        "errors": errors,
    }

    try:
        # Step 1: Scrape the website
        logfire.info("Scraping website", url=url)
        print(f"📡 Step 1: Scraping {url}...")

        scrape_result = await crawl_website(
            url=url,
            extract_images=False,
            extract_links=False,
            word_count_threshold=5,
            headless=True,
        )

        if not scrape_result.get("success"):
            error_msg = (
                f"Scraping failed: {scrape_result.get('error', 'Unknown error')}"
            )
            errors.append(error_msg)
            logfire.error("Scraping failed", url=url, error=error_msg)
            return result

        content_data = scrape_result.get("content", {})
        content_markdown = content_data.get("markdown", "")
        title = content_data.get("title", url)
        description = content_data.get("description", "")

        print(f"✅ Scraped {len(content_markdown)} characters")
        logfire.info(
            "Scraping successful", url=url, content_length=len(content_markdown)
        )

        # Step 2: Save to Supabase
        supabase_doc_id = None
        if save_to_supabase:
            logfire.info("Saving to Supabase", url=url, table=supabase_table_name)
            print(f"\n💾 Step 2: Saving scraped content to Supabase...")
            try:
                supabase_result = await add_document(
                    url=url,
                    title=title,
                    content=content_markdown,
                    description=description,
                    metadata={
                        "source": "event_scraper",
                        "scraped_at": datetime.now().isoformat(),
                        "content_length": len(content_markdown),
                    },
                    table_name=supabase_table_name,
                )

                if supabase_result.is_success and supabase_result.result:
                    supabase_doc_id = supabase_result.result.id
                    result["supabase_document_id"] = supabase_doc_id
                    print(f"✅ Saved to Supabase (ID: {supabase_doc_id})")
                    logfire.info(
                        "Supabase save successful", document_id=supabase_doc_id
                    )
                else:
                    error_msg = f"Supabase save failed: {supabase_result.error or 'Unknown error'}"
                    errors.append(error_msg)
                    logfire.warn("Supabase save failed", url=url, error=error_msg)
            except Exception as e:
                error_msg = f"Supabase save error: {str(e)}"
                errors.append(error_msg)
                logfire.error("Supabase save exception", url=url, error=str(e))

        # Step 3: Extract event details with quality control
        logfire.info("Extracting event details", url=url)
        print(f"\n🤖 Step 3: Extracting event details with quality control...")

        event, quality_score = await extract_event_with_quality_control(
            url=url,
            content=content_markdown,
            quality_threshold=quality_threshold,
            max_iterations=max_iterations,
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

        logfire.info(
            "Event extraction complete",
            event_title=event.title,
            quality_score=quality_score.overall_score,
            is_acceptable=quality_score.is_acceptable(),
        )

        # Step 4: Create Discord event
        if is_bot_ready():
            logfire.info("Creating Discord event", event_title=event.title)
            print(f"\n📅 Step 4: Creating Discord event...")
            try:
                # Get server ID
                if not discord_server_id:
                    # Try environment variable
                    discord_server_id = os.getenv("DISCORD_SERVER_ID")

                    # If still not set, get first available server
                    if not discord_server_id:
                        servers_result = await list_servers()
                        if servers_result.is_success and servers_result.result:
                            servers = servers_result.result.servers
                            if servers:
                                discord_server_id = servers[0]["id"]
                                print(
                                    f"   Using first available server: {servers[0]['name']}"
                                )

                if not discord_server_id:
                    errors.append("No Discord server ID available")
                    logfire.warn("No Discord server available")
                else:
                    # Parse datetime for Discord
                    start_dt, end_dt = event.convert_datetime_for_discord()

                    if not start_dt:
                        errors.append("Could not parse event date/time for Discord")
                        logfire.warn(
                            "Could not parse event datetime",
                            event_date=event.date,
                            event_time=event.start_time,
                        )
                    else:
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
                        if event.url:
                            description_parts.append(f"More info: {event.url}")

                        description = (
                            "\n\n".join(description_parts)
                            if description_parts
                            else None
                        )

                        # Format datetime for Discord API (ISO 8601)
                        start_time_iso = start_dt.isoformat()
                        end_time_iso = end_dt.isoformat() if end_dt else None

                        # Create Discord event
                        discord_result = await create_scheduled_event(
                            server_id=discord_server_id,
                            name=event.title[:100],  # Discord limit is 100 chars
                            start_time=start_time_iso,
                            end_time=end_time_iso,
                            description=description,
                            entity_type="external",
                            location=location,
                        )

                        if discord_result.is_success and discord_result.result:
                            result["discord_event_id"] = discord_result.result.event_id
                            result["discord_event_url"] = discord_result.result.url
                            print(
                                f"✅ Discord event created: {discord_result.result.url}"
                            )
                            logfire.info(
                                "Discord event created",
                                event_id=discord_result.result.event_id,
                                event_url=discord_result.result.url,
                            )
                        else:
                            error_msg = f"Discord event creation failed: {discord_result.error or 'Unknown error'}"
                            errors.append(error_msg)
                            logfire.error(
                                "Discord event creation failed", error=error_msg
                            )

            except Exception as e:
                error_msg = f"Discord event creation error: {str(e)}"
                errors.append(error_msg)
                logfire.error("Discord event creation exception", error=str(e))
        else:
            errors.append("Discord bot not ready")
            logfire.warn("Discord bot not ready")

        # Determine overall success
        # Success if we have an event and either Discord or Supabase succeeded
        result["success"] = (
            result["event"] is not None
            and (
                result["discord_event_id"] is not None
                or result["supabase_document_id"] is not None
            )
            and len([e for e in errors if "critical" in e.lower()]) == 0
        )

        logfire.info(
            "Workflow complete",
            success=result["success"],
            has_event=result["event"] is not None,
            has_discord_event=result["discord_event_id"] is not None,
            has_supabase_doc=result["supabase_document_id"] is not None,
            error_count=len(errors),
        )

        return result

    except Exception as e:
        error_msg = f"Workflow failed: {str(e)}"
        errors.append(error_msg)
        logfire.error("Workflow exception", url=url, error=str(e), exc_info=True)
        return result


# Test function
if __name__ == "__main__":
    import asyncio

    async def test():
        result = await create_event_from_url_with_supabase(
            url="https://www.bluesmuse.dance/",
            save_to_supabase=True,
        )

        print(f"\n📊 Result:")
        print(f"  Success: {result['success']}")
        if result["event"]:
            print(f"  Event: {result['event'].title}")
            print(f"  Date: {result['event'].date}")
        if result["discord_event_url"]:
            print(f"  Discord: {result['discord_event_url']}")
        if result["supabase_document_id"]:
            print(f"  Supabase: {result['supabase_document_id']}")
        if result["errors"]:
            print(f"  Errors: {result['errors']}")

    asyncio.run(test())
