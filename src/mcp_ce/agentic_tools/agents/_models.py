"""
Data models for event extraction agent graph.

Following Pydantic-AI patterns from flight booking example.
"""

import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


# ===== Output Models (Pydantic BaseModel for LLM-generated data) =====


class EventDetails(BaseModel):
    """
    Details of a single extracted event.

    This is LLM-generated output, validated by Pydantic.
    """

    title: str = Field(description="Event title or name")
    date: str = Field(description="Event date in YYYY-MM-DD format")
    start_time: str = Field(description="Start time in HH:MM format (24-hour)")
    location_name: str = Field(description="Venue or location name")
    location_address: Optional[str] = Field(
        default=None, description="Street address of venue"
    )
    description: Optional[str] = Field(default=None, description="Event description")
    organizer: Optional[str] = Field(
        default=None, description="Event organizer or host"
    )
    registration_url: Optional[str] = Field(
        default=None, description="Registration or ticket URL"
    )
    price: Optional[str] = Field(default=None, description="Ticket price or cost")
    image_url: Optional[str] = Field(default=None, description="Event image URL")
    end_time: Optional[str] = Field(
        default=None, description="End time in HH:MM format (optional)"
    )

    def get_full_location(self) -> str:
        """Get complete location string."""
        if self.location_address:
            return f"{self.location_name}, {self.location_address}"
        return self.location_name

    def convert_datetime_for_discord(self) -> str:
        """Convert date and time to Discord ISO 8601 format."""
        try:
            dt_str = f"{self.date} {self.start_time}"
            dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            return dt.isoformat()
        except Exception:
            return f"{self.date}T{self.start_time}:00"


class ScrapedContent(BaseModel):
    """Output from web scraping agent."""

    url: str
    markdown: str = Field(description="Scraped content in markdown format")
    content_length: int
    success: bool = True


class NoEventsFound(BaseModel):
    """When no valid events are found on the page."""

    reason: str = Field(description="Why no events were found")
    suggestions: Optional[List[str]] = Field(
        default=None, description="Suggestions for finding events"
    )


class ExtractionResult(BaseModel):
    """Result from event extraction agent."""

    events: List[EventDetails] = Field(
        description="List of extracted events", default_factory=list
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in extraction completeness"
    )
    indicators_found: List[str] = Field(
        description="Event indicators found in content", default_factory=list
    )


class EventExtractionWorkflowResult(BaseModel):
    """Final output from complete event extraction workflow."""

    events: List[EventDetails] = Field(description="All extracted events")
    overall_confidence: float = Field(
        ge=0.0, le=1.0, description="Overall confidence score"
    )
    iterations_used: int = Field(description="Number of extraction iterations")
    extraction_complete: bool = Field(description="Whether extraction is complete")
    missed_indicators: List[str] = Field(
        description="Potential missed event indicators", default_factory=list
    )
    url: str = Field(description="Source URL")
    content_length: int = Field(description="Length of scraped content")


# ===== Error/Failure Models =====


class ScrapingFailed(BaseModel):
    """When web scraping fails."""

    url: str
    error: str = Field(description="Error message")
    retry_suggested: bool = Field(default=False)


class ExtractionFailed(BaseModel):
    """When event extraction fails."""

    error: str = Field(description="Error message")
    partial_events: List[EventDetails] = Field(
        default_factory=list, description="Partially extracted events"
    )
