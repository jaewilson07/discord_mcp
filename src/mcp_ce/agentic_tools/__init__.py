"""
AI Agents for MCP Discord Server.

Architecture:
- base_agents/ - Generic, reusable agents (scraper, extraction, validation)
- workflows/ - Specific workflow implementations using base agents
- event_extraction_graph/ - Event-specific models and tools

Following Pydantic-AI patterns with dependency injection and logfire instrumentation.
"""

# Base agents (generic, reusable)
from .agents import (
    scraper_agent,
    extraction_agent,
    validation_agent,
    ScraperDeps,
    ExtractionDeps,
    ValidationDeps,
)

# Workflows (specific implementations)
from .graphs.extract_event.extract_event import extract_events_from_url

# Domain models
from mcp_ce.models.events import EventDetails
from .agents._models import EventExtractionWorkflowResult

__all__ = [
    # Base Agents
    "scraper_agent",
    "extraction_agent",
    "validation_agent",
    "ScraperDeps",
    "ExtractionDeps",
    "ValidationDeps",
    # Workflows
    "extract_events_from_url",
    # Models
    "EventDetails",
    "EventExtractionWorkflowResult",
]
