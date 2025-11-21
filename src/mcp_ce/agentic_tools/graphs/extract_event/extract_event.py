"""
Event Extraction Workflow.

Uses generic base agents configured specifically for event extraction.
This is a workflow implementation, not agent definitions.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional, Callable, List

import logfire
from pydantic_ai import Agent, RunContext, RunUsage, UsageLimits

from ...agents import (
    scraper_agent,
    ScraperDeps,
    extraction_agent,
    ExtractionDeps,
    validation_agent,
    ValidationDeps,
)
from ....models.events import EventDetails
from ...agents._models import EventExtractionWorkflowResult
from ..scrape_content.tools import (
    find_date_patterns,
    find_time_patterns,
    find_event_keywords,
    count_event_indicators,
    validate_event_completeness,
)
from ....tools.crawl4ai.crawl_website import crawl_website

logger = logging.getLogger(__name__)

# Configure logfire
logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()


# ===== Workflow Dependencies =====


@dataclass
class EventExtractionWorkflowDeps:
    """Dependencies for event extraction workflow."""

    url: str
    max_iterations: int = 2
    confidence_threshold: float = 0.85
    progress_callback: Optional[Callable] = None


# ===== Event-Specific Helper Functions =====


async def find_event_patterns(content: str) -> dict:
    """Find event-specific patterns in content."""
    return {
        "dates": find_date_patterns(content),
        "times": find_time_patterns(content),
        "keywords": find_event_keywords(content),
    }


async def check_event_completeness(
    content: str,
    extracted_items: List[EventDetails],
    iteration: int,
    max_iterations: int,
    context: dict,
) -> dict:
    """Check completeness of event extraction."""
    indicators = count_event_indicators(content)
    extracted_count = len(extracted_items)

    max_indicators = max(indicators["dates"], indicators["times"])
    completeness = extracted_count / max_indicators if max_indicators > 0 else 1.0

    # Check quality
    quality_scores = [
        validate_event_completeness(event.model_dump()) for event in extracted_items
    ]
    avg_quality = (
        sum(q["quality_score"] for q in quality_scores) / len(quality_scores)
        if quality_scores
        else 0.0
    )

    missing_indicators = []
    if extracted_count < max_indicators * 0.8:
        missing_indicators.append(
            f"Only extracted {extracted_count} events but found {max_indicators} date/time patterns"
        )

    return {
        "indicators": indicators,
        "extracted_count": extracted_count,
        "completeness": completeness,
        "quality": avg_quality,
        "missing_indicators": missing_indicators,
        "should_retry": completeness < 0.8 and iteration < max_iterations,
    }


async def check_event_quality(items: List[EventDetails], context: dict) -> dict:
    """Check quality of extracted events."""
    issues = []

    for i, event in enumerate(items, 1):
        validation = validate_event_completeness(event.model_dump())

        if validation["missing_required"]:
            issues.append(
                f"Event {i} '{event.title}' missing required fields: {validation['missing_required']}"
            )
        elif validation["quality_score"] < 0.7:
            issues.append(
                f"Event {i} '{event.title}' has low quality score: {validation['quality_score']:.1%}"
            )

    return {
        "issues": issues,
        "has_issues": len(issues) > 0,
    }


# ===== Workflow Orchestrator =====


def _get_workflow_model() -> str:
    """Get model for workflow agent from environment."""
    return (
        os.getenv("WORKFLOW_AGENT_MODEL")
        or os.getenv("DEFAULT_AGENT_MODEL")
        or "openai:gpt-4o"
    )


workflow_agent = Agent[EventExtractionWorkflowDeps, EventExtractionWorkflowResult](
    _get_workflow_model(),
    output_type=EventExtractionWorkflowResult,
    system_prompt="""You are the event extraction workflow orchestrator.

Your job is to coordinate the entire event extraction process:
1. Scrape the URL
2. Extract events from content
3. Validate extraction completeness
4. Retry if needed (up to max_iterations)

Use the delegation tools to call specialized agents.""",
)


@workflow_agent.tool
async def run_scraper(ctx: RunContext[EventExtractionWorkflowDeps]) -> str:
    """Delegate to scraper agent to get web content."""
    logfire.info("Running scraper agent", url=ctx.deps.url)

    scraper_deps = ScraperDeps(
        url=ctx.deps.url,
        scrape_function=crawl_website,  # Inject Crawl4AI function
    )

    # Delegate to generic scraper agent
    result = await scraper_agent.run(
        f"Scrape content from {ctx.deps.url}",
        deps=scraper_deps,
        usage=ctx.usage,
    )

    if hasattr(result.output, "error"):
        return f"Scraping failed: {result.output.error}"

    content = result.output.markdown
    logfire.info("Scraper agent completed", content_length=len(content))

    return f"Successfully scraped {len(content)} characters from {ctx.deps.url}"


@workflow_agent.tool
async def run_extraction(
    ctx: RunContext[EventExtractionWorkflowDeps],
    scraped_content: str,
    previous_events: Optional[List[dict]] = None,
    feedback: Optional[str] = None,
) -> str:
    """Delegate to extraction agent to find events."""
    logfire.info("Running extraction agent")

    # Configure extraction agent for events
    extraction_deps = ExtractionDeps(
        content=scraped_content,
        extraction_schema=EventDetails,
        previous_items=previous_events,
        feedback=feedback,
        pattern_finder=find_event_patterns,  # Inject event pattern finder
        context={"url": ctx.deps.url},
    )

    # Delegate to generic extraction agent
    result = await extraction_agent.run(
        "Extract all events from the content",
        deps=extraction_deps,
        usage=ctx.usage,
    )

    events = result.output.items
    logfire.info("Extraction agent completed", events_found=len(events))

    return f"Found {len(events)} events with {result.output.confidence:.1%} confidence"


@workflow_agent.tool
async def run_validation(
    ctx: RunContext[EventExtractionWorkflowDeps],
    scraped_content: str,
    extracted_events: List[dict],
    iteration: int,
) -> str:
    """Delegate to validation agent to check completeness."""
    logfire.info("Running validation agent", iteration=iteration)

    # Convert dict to EventDetails
    events_models = [EventDetails(**e) for e in extracted_events]

    # Configure validation agent for events
    validation_deps = ValidationDeps(
        content=scraped_content,
        extracted_items=events_models,
        iteration=iteration,
        max_iterations=ctx.deps.max_iterations,
        completeness_checker=check_event_completeness,  # Inject event completeness checker
        quality_checker=check_event_quality,  # Inject event quality checker
        context={"url": ctx.deps.url},
    )

    # Delegate to generic validation agent
    result = await validation_agent.run(
        "Validate extraction completeness",
        deps=validation_deps,
        usage=ctx.usage,
    )

    validation = result.output
    logfire.info(
        "Validation agent completed",
        is_complete=validation.is_complete,
        should_retry=validation.should_retry,
    )

    return f"Validation: {'Complete' if validation.is_complete else 'Incomplete'} (confidence: {validation.confidence:.1%}, retry: {validation.should_retry})"


# ===== Main Entry Point =====


async def extract_events_from_url(
    url: str,
    max_iterations: int = 2,
    confidence_threshold: float = 0.85,
    progress_callback: Optional[Callable] = None,
) -> EventExtractionWorkflowResult:
    """
    Extract events from URL using multi-agent workflow.

    This workflow uses generic base agents configured for event extraction.

    Args:
        url: URL to extract events from
        max_iterations: Maximum extraction/validation cycles
        confidence_threshold: Minimum confidence to stop iterating
        progress_callback: Optional callback for progress updates

    Returns:
        EventExtractionWorkflowResult with all extracted events

    Example:
        result = await extract_events_from_url(
            url="https://seattlebluesdance.com/",
            max_iterations=2,
            confidence_threshold=0.85,
        )

        print(f"Found {len(result.events)} events")
        for event in result.events:
            print(f"  - {event.title} on {event.date}")
    """
    logfire.info("Starting event extraction workflow", url=url)

    deps = EventExtractionWorkflowDeps(
        url=url,
        max_iterations=max_iterations,
        confidence_threshold=confidence_threshold,
        progress_callback=progress_callback,
    )

    # Set usage limits
    usage_limits = UsageLimits(request_limit=50)
    usage = RunUsage()

    # Run the workflow orchestrator
    result = await workflow_agent.run(
        f"Extract all events from {url}",
        deps=deps,
        usage=usage,
        usage_limits=usage_limits,
    )

    logfire.info(
        "Event extraction workflow complete",
        events_found=len(result.output.events),
        iterations=result.output.iterations_used,
        confidence=result.output.overall_confidence,
    )

    return result.output
