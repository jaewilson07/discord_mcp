"""
Scraper Agent Tool.

Exposes the ScraperAgent as an MCP tool.
Uses crawl_website internally for scraping.
"""

from typing import Dict, Any, Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse, ToolResult
from dataclasses import dataclass

from ...agentic_tools.agents import ScraperAgent, ScraperDeps
from ...agentic_tools.logfire_config import configure_logfire

# Ensure Logfire is configured
configure_logfire()

# Create agent instance
_agent = ScraperAgent()


@dataclass
class ScraperAgentResult(ToolResult):
    """Result from scraper agent tool."""

    url: str
    markdown: str
    content_length: int
    success: bool
    metadata: Optional[dict] = None


@register_command("agents", "scraper_agent")
async def scraper_agent_tool(
    url: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> ToolResponse:
    """
    Run the scraper agent to scrape web content.

    Uses the crawl_website tool internally for scraping.

    Args:
        url: URL to scrape
        request_id: Optional request ID for tracking
        user_id: Optional user ID for tracking

    Returns:
        ToolResponse with ScraperAgentResult containing scraped content
    """
    try:
        # Import here to avoid circular imports
        from ...tools.crawl4ai.crawl_website import crawl_website

        # Create scrape function wrapper
        async def scrape_function(url: str, **kwargs):
            """Wrapper to use crawl_website tool."""
            result = await crawl_website(url=url, **kwargs)
            return result

        deps = ScraperDeps(
            url=url,
            scrape_function=scrape_function,
            request_id=request_id,
            user_id=user_id,
        )

        result = await _agent.run(
            f"Scrape content from {url} and return structured information",
            deps=deps,
        )

        # Convert agent output to tool result
        tool_result = ScraperAgentResult(
            url=result.url,
            markdown=result.markdown,
            content_length=result.content_length,
            success=result.success,
            metadata=result.metadata,
        )

        return ToolResponse(is_success=True, result=tool_result)

    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Scraper agent failed: {str(e)}",
        )
