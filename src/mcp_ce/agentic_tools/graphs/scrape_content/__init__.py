"""
Event Extraction Models and Tools.

Domain-specific models and helper functions for event extraction.
Workflow implementation is in workflows/event_extraction_workflow.py
"""

from pydantic import BaseModel

# Import models from their actual locations
from mcp_ce.models.events import EventDetails
from mcp_ce.agentic_tools.agents._models import EventExtractionWorkflowResult, ExtractionResult, ExtractionFailed
from mcp_ce.agentic_tools.agents.scraper.scraper_agent import ScrapedContent, ScrapingFailed
from mcp_ce.agentic_tools.agents.validation.validation_agent import ValidationResult

# Create placeholder for NoEventsFound
class NoEventsFound(BaseModel):
    """No events found in content."""
    message: str = "No events found"

from .tools import (
    find_date_patterns,
    find_time_patterns,
    find_event_keywords,
    count_event_indicators,
    validate_event_completeness,
    compare_extraction_iterations,
)

__all__ = [
    # Models
    "EventDetails",
    "EventExtractionWorkflowResult",
    "NoEventsFound",
    "ScrapedContent",
    "ScrapingFailed",
    "ExtractionResult",
    "ExtractionFailed",
    "ValidationResult",
    # Tools
    "find_date_patterns",
    "find_time_patterns",
    "find_event_keywords",
    "count_event_indicators",
    "validate_event_completeness",
    "compare_extraction_iterations",
]
