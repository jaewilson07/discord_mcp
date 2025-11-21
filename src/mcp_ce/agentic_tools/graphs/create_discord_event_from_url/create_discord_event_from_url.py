"""
Graph workflow: Scrape website → Extract event → Create Discord event.

This workflow:
1. Scrapes a website URL to extract content
2. Extracts structured event details from the content using quality-controlled extraction
3. Creates a Discord scheduled event from the extracted details

Follows the atomic tool pattern - uses tools directly, not agents.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
import logfire

from mcp_ce.tools.crawl4ai.crawl_website import crawl_website
from mcp_ce.tools.crawl4ai.deep_crawl import deep_crawl_website
from mcp_ce.tools.discord.create_scheduled_event import create_scheduled_event
from mcp_ce.tools.discord.list_servers import list_servers
from mcp_ce.tools.discord._bot_helper import is_bot_ready
from mcp_ce.agentic_tools.events.evaluator_optimizer import extract_event_with_quality_control
from mcp_ce.models.events import EventDetails


@logfire.instrument()
async def create_discord_event_from_url(
    url: str,
    discord_server_id: Optional[str] = None,
    quality_threshold: float = 0.7,
    max_iterations: int = 3,
) -> Dict[str, Any]:
    """
    Scrape a website for event information and create a Discord scheduled event.

    This workflow:
    1. Scrapes the URL to extract content
    2. Uses AI to extract structured event details (EventDetails model) with quality control
    3. Creates a Discord scheduled event

    Args:
        url: Website URL to scrape for event information
        discord_server_id: Discord server ID to create event in (uses first available if not provided)
        quality_threshold: Minimum quality score for event extraction (default: 0.7)
        max_iterations: Maximum optimization iterations for extraction (default: 3)

    Returns:
        Dict containing:
        - success: bool indicating if workflow succeeded
        - event: EventDetails object
        - quality_score: dict with quality metrics
        - discord_event_id: Discord event ID (if created)
        - discord_event_url: Discord event URL (if created)
        - errors: list of any errors encountered

    Example:
        result = await create_discord_event_from_url(
            url="https://www.bluesmuse.dance/",
        )

        if result['success']:
            print(f"Created event: {result['event'].title}")
            print(f"Discord: {result['discord_event_url']}")
    """
    errors = []
    result = {
        "success": False,
        "event": None,
        "quality_score": None,
        "discord_event_id": None,
        "discord_event_url": None,
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

        # Handle ToolResponse
        if hasattr(scrape_result, "is_success"):
            is_success = scrape_result.is_success
            if not is_success:
                error_msg = scrape_result.error or "Unknown error"
                errors.append(f"Scraping failed: {error_msg}")
                logfire.error("Scraping failed", url=url, error=error_msg)
                return result
            scrape_data = scrape_result.result if scrape_result.result else {}
        else:
            # Handle dict response (backward compatibility)
            is_success = scrape_result.get("success", False)
            if not is_success:
                error_msg = scrape_result.get("error", "Unknown error")
                errors.append(f"Scraping failed: {error_msg}")
                logfire.error("Scraping failed", url=url, error=error_msg)
                return result
            scrape_data = scrape_result.get("result", {})

        content_data = scrape_data if isinstance(scrape_data, dict) else {}
        content_markdown = (
            content_data.get("content_markdown", "")
            or content_data.get("markdown", "")
            or ""
        )

        print(f"✅ Scraped {len(content_markdown)} characters")
        logfire.info(
            "Scraping successful", url=url, content_length=len(content_markdown)
        )

        # Step 2: Extract event details with quality control
        logfire.info("Extracting event details", url=url)
        print(f"\n🤖 Step 2: Extracting event details with quality control...")

        event, quality_score = await extract_event_with_quality_control(
            url=url,
            content=content_markdown,
            quality_threshold=quality_threshold,
            max_iterations=max_iterations,
        )

        # Step 2.5: Evaluator - Check if we need more information
        needs_deep_crawl = False
        deep_crawl_reason = None
        
        # Check if quality is insufficient or critical fields are missing
        if quality_score.overall_score < quality_threshold:
            needs_deep_crawl = True
            deep_crawl_reason = f"Quality score {quality_score.overall_score:.2f} below threshold {quality_threshold}"
        elif not quality_score.is_acceptable():
            needs_deep_crawl = True
            deep_crawl_reason = "Quality not acceptable - missing critical information"
        elif not event.date or not event.title or (not event.location_name and not event.is_online):
            needs_deep_crawl = True
            deep_crawl_reason = "Missing critical event fields (date, title, or location)"

        # Step 2.6: Deep crawl if needed
        if needs_deep_crawl:
            logfire.info("Insufficient information detected, triggering deep crawl", reason=deep_crawl_reason)
            print(f"\n🔍 Step 2.5: Evaluator detected insufficient information")
            print(f"   Reason: {deep_crawl_reason}")
            print(f"   Quality: {quality_score.overall_score:.2f}")
            print(f"   Triggering multi-page crawl...")

            try:
                deep_crawl_result = await deep_crawl_website(
                    url=url,
                    max_depth=2,
                    max_pages=10,
                    include_external=False,
                    word_count_threshold=5,
                    headless=True,
                )

                if deep_crawl_result.is_success and deep_crawl_result.result:
                    deep_data = deep_crawl_result.result
                    
                    # Handle both dict and dataclass responses
                    if isinstance(deep_data, dict):
                        pages_crawled = deep_data.get("pages_crawled", 0)
                        pages = deep_data.get("pages", [])
                    else:
                        # Dataclass response
                        pages_crawled = getattr(deep_data, "pages_crawled", 0)
                        pages = getattr(deep_data, "pages", [])

                    print(f"✅ Deep crawl complete: {pages_crawled} pages")

                    # Combine content from all pages
                    all_content = content_markdown  # Start with main page
                    for page in pages:
                        # Handle both dict and dataclass page objects
                        if isinstance(page, dict):
                            page_url = page.get("url", "")
                            page_content = page.get("content_markdown", "")
                        else:
                            page_url = getattr(page, "url", "")
                            page_content = getattr(page, "content_markdown", "")
                        
                        if page_url != url and page_content:  # Don't duplicate main page
                            # Add page content with context
                            all_content += f"\n\n--- Page: {page_url} ---\n\n{page_content[:3000]}"

                    print(f"   Combined content: {len(all_content)} characters from {pages_crawled + 1} pages")

                    # Re-extract with combined content
                    logfire.info("Re-extracting with combined content", total_pages=pages_crawled + 1)
                    print(f"\n🔄 Re-extracting event with combined content...")

                    improved_event, improved_quality = await extract_event_with_quality_control(
                        url=url,
                        content=all_content,
                        quality_threshold=quality_threshold,
                        max_iterations=max_iterations,
                    )

                    # Use improved extraction if it's better
                    if improved_quality.overall_score > quality_score.overall_score:
                        print(f"   🎉 Quality improved: {quality_score.overall_score:.2f} → {improved_quality.overall_score:.2f}")
                        event = improved_event
                        quality_score = improved_quality
                        logfire.info(
                            "Quality improved after deep crawl",
                            before=quality_score.overall_score,
                            after=improved_quality.overall_score,
                        )
                    else:
                        print(f"   ℹ️ Quality: {improved_quality.overall_score:.2f} (no significant improvement)")
                else:
                    error_msg = deep_crawl_result.error or "Unknown deep crawl error"
                    print(f"   ⚠️ Deep crawl failed: {error_msg}")
                    logfire.warn("Deep crawl failed", error=error_msg)
                    # Continue with original extraction

            except Exception as e:
                error_msg = f"Deep crawl error: {str(e)}"
                print(f"   ⚠️ {error_msg}")
                logfire.error("Deep crawl exception", error=str(e))
                # Continue with original extraction

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

        # Step 3: Create Discord event
        if is_bot_ready():
            logfire.info("Creating Discord event", event_title=event.title)
            print(f"\n📅 Step 3: Creating Discord event...")
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
        # Success if we have an event and Discord event was created
        result["success"] = (
            result["event"] is not None
            and result["discord_event_id"] is not None
            and len([e for e in errors if "critical" in e.lower()]) == 0
        )

        logfire.info(
            "Workflow complete",
            success=result["success"],
            has_event=result["event"] is not None,
            has_discord_event=result["discord_event_id"] is not None,
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
        result = await create_discord_event_from_url(
            url="https://www.bluesmuse.dance/",
        )

        print(f"\n📊 Result:")
        print(f"  Success: {result['success']}")
        if result["event"]:
            print(f"  Event: {result['event'].title}")
            print(f"  Date: {result['event'].date}")
        if result["discord_event_url"]:
            print(f"  Discord: {result['discord_event_url']}")
        if result["errors"]:
            print(f"  Errors: {result['errors']}")

    asyncio.run(test())

