"""
Base Agents Package.

Generalized, reusable agents that can be configured for different workflows.
All agents follow the BaseAgent pattern with proper Logfire integration.
"""

from .scraper.scraper_agent import (
    ScraperAgent,
    scraper_agent,
    create_scraper_agent,
    ScraperDeps,
    ScrapedContent,
    ScrapingFailed,
)
from .extraction.agent import (
    ExtractionAgent,
    extraction_agent,
    create_extraction_agent,
    ExtractionDeps,
    ExtractionResult,
    ExtractionFailed,
)
from .validation.validation_agent import (
    ValidationAgent,
    validation_agent,
    create_validation_agent,
    ValidationDeps,
    ValidationResult,
)
from .base_agent import BaseAgent, AgentDependencies

__all__ = [
    # Base Agent
    "BaseAgent",
    "AgentDependencies",
    # Scraper
    "ScraperAgent",
    "scraper_agent",
    "create_scraper_agent",
    "ScraperDeps",
    "ScrapedContent",
    "ScrapingFailed",
    # Extraction
    "ExtractionAgent",
    "extraction_agent",
    "create_extraction_agent",
    "ExtractionDeps",
    "ExtractionResult",
    "ExtractionFailed",
    # Validation
    "ValidationAgent",
    "validation_agent",
    "create_validation_agent",
    "ValidationDeps",
    "ValidationResult",
]
