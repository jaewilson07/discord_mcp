"""
Event Extraction Workflow - High-level wrapper using EventExtractionAgent.

This module provides the main workflow function for extracting events from URLs,
integrating with Discord and Notion services.
"""

import logging
from typing import Any, Dict, List, Optional

from ....tools.crawl4ai.crawl_website import crawl_website
from ....tools.discord.create_scheduled_event import create_scheduled_event
from ...tools.notion.create_notion_page import create_notion_page
from ....models.events import EventDetails
from ..event_extraction_agent import EventExtractionAgent, EventExtractionDependencies

logger = logging.getLogger(__name__)


async def extract_events_from_url(
    url: str,
    discord_server_id: Optional[str] = None,
    save_to_notion: bool = True,
    notion_database_id: Optional[str] = None,
    max_iterations: int = 5,
    confidence_threshold: float = 0.85,
    progress_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Extract all events from URL using EventExtractionAgent.

    This is the main workflow function that:
    1. Scrapes the URL using Crawl4AI
    2. Runs EventExtractionAgent with self-verification loop
    3. Creates Discord scheduled events for each extracted event
    4. Saves each event to Notion (if enabled)

    Args:
        url: URL to scrape for events
        discord_server_id: Optional Discord server ID for event creation
        save_to_notion: Whether to save events to Notion
        notion_database_id: Optional Notion database ID
        max_iterations: Maximum self-verification loops (default: 5)
        confidence_threshold: Minimum confidence to stop iterating (default: 0.85)
        progress_callback: Optional callback for progress updates

    Returns:
        Dictionary with:
        - success: bool
        - events: List[EventDetails]
        - discord_event_urls: List[str] (if discord_server_id provided)
        - notion_page_ids: List[str] (if save_to_notion=True)
        - overall_confidence: float
        - iterations_used: int
        - error: str (if failed)

    Example:
        result = await extract_events_from_url(
            url="https://seattlebluesdance.com/",
            discord_server_id="123456789",
            save_to_notion=True,
            notion_database_id="abc123",
        )

        if result['success']:
            print(f"Found {len(result['events'])} events")
            for event in result['events']:
                print(f"  - {event.title} on {event.date}")
    """
    try:
        # Progress update
        if progress_callback:
            await progress_callback(
                {
                    "step": "scraping",
                    "url": url,
                }
            )

        # Step 1: Scrape the URL
        logger.info(f"Scraping URL: {url}")
        scrape_result = await crawl_website(url=url)

        if not scrape_result.is_success:
            return {
                "success": False,
                "error": f"Failed to scrape URL: {scrape_result.error}",
            }

        scraped_content = scrape_result.result.markdown
        logger.info(f"Scraped {len(scraped_content)} characters from {url}")

        # Progress update
        if progress_callback:
            await progress_callback(
                {
                    "step": "extracting",
                    "content_length": len(scraped_content),
                }
            )

        # Step 2: Run EventExtractionAgent
        logger.info("Running EventExtractionAgent with self-verification loop")
        agent = EventExtractionAgent()

        deps = EventExtractionDependencies(
            url=url,
            scraped_content=scraped_content,
            max_iterations=max_iterations,
            confidence_threshold=confidence_threshold,
            progress_callback=progress_callback,
            discord_server_id=discord_server_id,
            save_to_notion=save_to_notion,
            notion_database_id=notion_database_id,
        )

        extraction_result = await agent.run(
            user_prompt=f"Extract all events from this URL: {url}",
            deps=deps,
        )

        events = extraction_result.events
        logger.info(
            f"Agent extracted {len(events)} events "
            f"(confidence: {extraction_result.overall_confidence:.2%}, "
            f"iterations: {extraction_result.iterations_used})"
        )

        # Progress update
        if progress_callback:
            await progress_callback(
                {
                    "step": "processing",
                    "events_found": len(events),
                }
            )

        # Step 3: Create Discord events (if server ID provided)
        discord_event_urls = []
        if discord_server_id and events:
            logger.info(f"Creating {len(events)} Discord scheduled events")

            for event in events:
                try:
                    # Convert EventDetails to Discord event format
                    discord_result = await create_scheduled_event(
                        server_id=discord_server_id,
                        event_name=event.title,
                        event_description=event.description or "",
                        start_time=event.convert_datetime_for_discord(),
                        location=event.get_full_location(),
                        end_time=None,  # TODO: Add end_time support
                    )

                    if discord_result.is_success:
                        discord_event_urls.append(discord_result.result.event_url)
                        logger.info(f"Created Discord event: {event.title}")
                    else:
                        logger.error(
                            f"Failed to create Discord event for {event.title}: {discord_result.error}"
                        )

                except Exception as e:
                    logger.error(f"Error creating Discord event for {event.title}: {e}")

        # Step 4: Save to Notion (if enabled)
        notion_page_ids = []
        if save_to_notion and notion_database_id and events:
            logger.info(f"Saving {len(events)} events to Notion")

            for event in events:
                try:
                    # Convert EventDetails to Notion properties
                    notion_properties = {
                        "Title": {"title": [{"text": {"content": event.title}}]},
                        "Date": {
                            "date": {
                                "start": event.date,
                            }
                        },
                        "Location": {
                            "rich_text": [
                                {"text": {"content": event.get_full_location()}}
                            ]
                        },
                        "URL": {"url": event.registration_url or url},
                    }

                    # Add description as page content
                    notion_children = []
                    if event.description:
                        notion_children.append(
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {"text": {"content": event.description}}
                                    ]
                                },
                            }
                        )

                    notion_result = await create_notion_page(
                        database_id=notion_database_id,
                        properties=notion_properties,
                        children=notion_children if notion_children else None,
                    )

                    if notion_result.is_success:
                        notion_page_ids.append(notion_result.result.page_id)
                        logger.info(f"Saved event to Notion: {event.title}")
                    else:
                        logger.error(
                            f"Failed to save {event.title} to Notion: {notion_result.error}"
                        )

                except Exception as e:
                    logger.error(f"Error saving {event.title} to Notion: {e}")

        # Progress update
        if progress_callback:
            await progress_callback(
                {
                    "step": "complete",
                    "events_found": len(events),
                    "discord_events_created": len(discord_event_urls),
                    "notion_pages_saved": len(notion_page_ids),
                }
            )

        # Return results
        return {
            "success": True,
            "events": events,
            "discord_event_urls": discord_event_urls,
            "notion_page_ids": notion_page_ids,
            "overall_confidence": extraction_result.overall_confidence,
            "iterations_used": extraction_result.iterations_used,
            "extraction_complete": extraction_result.extraction_complete,
            "missed_indicators": extraction_result.missed_indicators,
        }

    except Exception as e:
        logger.error(f"Error extracting events from {url}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }
