"""
Generic Web Scraper Agent.

Reusable across any workflow that needs web content scraping.
Follows BaseAgent pattern with proper Logfire integration.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Union

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ..base_agent import BaseAgent, AgentDependencies
from .._model_helper import _get_model

logger = logging.getLogger(__name__)


# ===== Models =====


class ScrapedContent(BaseModel):
    """Output from web scraping."""

    url: str
    markdown: str = Field(description="Scraped content in markdown format")
    content_length: int
    success: bool = True
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class ScrapingFailed(BaseModel):
    """When web scraping fails."""

    url: str
    error: str = Field(description="Error message")
    retry_suggested: bool = Field(default=False)


# ===== Dependencies =====


@dataclass
class ScraperDeps:
    """Dependencies for web scraping agent."""
    
    # Required fields first
    url: str
    scrape_function: callable  # Inject scraping implementation
    
    # Optional fields
    additional_params: Optional[dict] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None


# ===== Agent Class =====


class ScraperAgent(BaseAgent[ScraperDeps, Union[ScrapedContent, ScrapingFailed]]):
    """
    Agent for web content scraping.

    Capabilities:
    - Coordinate web scraping operations
    - Handle scraping failures gracefully
    - Return structured scraped content or failure information
    """

    def __init__(self, model: Optional[str] = None, **kwargs):
        """Initialize the scraper agent."""
        super().__init__(
            model=model or _get_model("scraper"),
            name="ScraperAgent",
            **kwargs,
        )

    def _create_agent(self, **kwargs) -> Agent:
        """Create the Pydantic-AI agent with tools and prompts."""
        agent = Agent[ScraperDeps, Union[ScrapedContent, ScrapingFailed]](
            model=self.model,
            deps_type=ScraperDeps,
            system_prompt=self.get_system_prompt(),
            **kwargs,
        )

        @agent.tool
        async def scrape_url(ctx: RunContext[ScraperDeps]) -> str:
            """Scrape content from the URL using injected scraping function."""
            try:
                logfire.info("Scraping URL", url=ctx.deps.url)

                # Use injected scraping function (dependency injection pattern)
                result = await ctx.deps.scrape_function(
                    url=ctx.deps.url, **(ctx.deps.additional_params or {})
                )

                if not result.is_success:
                    logfire.warn("Scraping failed", url=ctx.deps.url, error=result.error)
                    return f"Failed to scrape {ctx.deps.url}: {result.error}"

                content = result.result.markdown
                logfire.info(
                    "Scraping successful",
                    url=ctx.deps.url,
                    content_length=len(content),
                )

                return f"Successfully scraped {len(content)} characters from {ctx.deps.url}"

            except Exception as e:
                logger.error(f"Scraping error: {e}", exc_info=True)
                logfire.error("Scraping error", url=ctx.deps.url, error=str(e))
                return f"Error scraping URL: {str(e)}"

        return agent

    def get_system_prompt(self) -> str:
        """Get the base system prompt for this agent."""
        return """You are a web scraping specialist.

Your job is to coordinate the scraping of web content.

**Your Approach:**
1. Call the scrape_url tool to fetch content from the provided URL
2. Analyze the scraped content to ensure it's complete
3. Return structured information about the scraped content

**Guidelines:**
- Always verify that scraping was successful
- Report any errors clearly
- Include metadata about the content when available"""


# ===== Factory Function (for backward compatibility) =====


def create_scraper_agent(
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> ScraperAgent:
    """
    Create a customized scraper agent.

    Args:
        model: LLM model to use (default: from env or "openai:gpt-4o")
        system_prompt: Custom system prompt (optional, overrides default)

    Returns:
        Configured scraper agent
    """
    agent = ScraperAgent(model=model)
    if system_prompt:
        # Create a new agent with custom prompt
        agent._agent = Agent[ScraperDeps, Union[ScrapedContent, ScrapingFailed]](
            model=agent.model,
            deps_type=ScraperDeps,
            system_prompt=system_prompt,
        )
    return agent


# ===== Default Instance =====

scraper_agent = ScraperAgent()
