"""
Generic Content Extraction Agent.

Reusable for extracting structured data from unstructured content.
Can be configured for different extraction tasks (events, products, articles, etc.).
Follows BaseAgent pattern with proper Logfire integration.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Type, Any

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ..base_agent import BaseAgent, AgentDependencies
from .._model_helper import _get_model

logger = logging.getLogger(__name__)


# ===== Models =====


class ExtractionResult(BaseModel):
    """Generic result from content extraction."""

    items: List[Any] = Field(
        description="List of extracted items", default_factory=list
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in extraction completeness"
    )
    indicators_found: List[str] = Field(
        description="Indicators found in content", default_factory=list
    )
    metadata: Optional[dict] = Field(
        default=None, description="Additional extraction metadata"
    )


class ExtractionFailed(BaseModel):
    """When content extraction fails."""

    error: str = Field(description="Error message")
    partial_items: List[Any] = Field(
        default_factory=list, description="Partially extracted items"
    )


# ===== Dependencies =====


@dataclass
class ExtractionDeps(AgentDependencies):
    """Dependencies for extraction agent."""

    # Required fields using Ellipsis to allow ordering after default fields
    content: str = field(default=...)  # Required field
    extraction_schema: Type[BaseModel] = field(default=...)  # Required field
    # Optional fields with defaults
    previous_items: Optional[List[Any]] = None
    feedback: Optional[str] = None
    pattern_finder: Optional[callable] = None  # Optional pattern recognition function
    context: Optional[dict] = None  # Additional context for extraction


# ===== Agent Class =====


class ExtractionAgent(BaseAgent[ExtractionDeps, ExtractionResult]):
    """
    Agent for extracting structured data from unstructured content.

    Capabilities:
    - Extract structured data from text content
    - Use pattern recognition for efficiency
    - Handle extraction failures gracefully
    - Support iterative extraction with feedback
    """

    def __init__(self, model: Optional[str] = None, **kwargs):
        """Initialize the extraction agent."""
        super().__init__(
            model=model or _get_model("extraction"),
            name="ExtractionAgent",
            **kwargs,
        )

    def _create_agent(self, **kwargs) -> Agent:
        """Create the Pydantic-AI agent with tools and prompts."""
        agent = Agent[ExtractionDeps, ExtractionResult](
            model=self.model,
            deps_type=ExtractionDeps,
            system_prompt=self.get_system_prompt(),
            **kwargs,
        )

        @agent.tool
        async def search_for_patterns(ctx: RunContext[ExtractionDeps]) -> str:
            """Search content for relevant patterns using injected pattern finder."""
            if not ctx.deps.pattern_finder:
                return "No pattern finder provided. Proceeding with manual extraction."

            try:
                logfire.info("Searching for patterns")

                # Use injected pattern finder
                patterns = await ctx.deps.pattern_finder(ctx.deps.content)

                result = f"Patterns Found:\n"
                for key, values in patterns.items():
                    result += f"- {key}: {len(values)} matches\n"
                    if values:
                        result += f"  Examples: {values[:3]}\n"

                logfire.info("Pattern search complete", patterns=patterns)
                return result

            except Exception as e:
                logger.error(f"Pattern search error: {e}", exc_info=True)
                logfire.error("Pattern search error", error=str(e))
                return f"Error searching patterns: {str(e)}"

        @agent.tool
        async def get_content_section(
            ctx: RunContext[ExtractionDeps],
            start_keyword: str,
            end_keyword: Optional[str] = None,
            max_length: int = 2000,
        ) -> str:
            """Get a specific section of content between keywords."""
            content = ctx.deps.content

            try:
                start_idx = content.lower().find(start_keyword.lower())
                if start_idx == -1:
                    return f"Keyword '{start_keyword}' not found in content"

                if end_keyword:
                    end_idx = content.lower().find(end_keyword.lower(), start_idx + 1)
                    if end_idx == -1:
                        section = content[start_idx : start_idx + max_length]
                    else:
                        section = content[start_idx:end_idx]
                else:
                    section = content[start_idx : start_idx + max_length]

                logfire.info(
                    "Content section extracted",
                    start_keyword=start_keyword,
                    section_length=len(section),
                )

                return f"Section starting with '{start_keyword}':\n\n{section}"

            except Exception as e:
                logger.error(f"Error extracting section: {e}", exc_info=True)
                logfire.error("Section extraction error", error=str(e))
                return f"Error extracting section: {str(e)}"

        return agent

    def get_system_prompt(self) -> str:
        """Get the base system prompt for this agent."""
        return """You are an expert content extraction specialist.

Your job is to extract ALL structured data from the provided content with high accuracy.

**Extraction Guidelines:**
1. Search systematically for all matching patterns
2. Extract complete information for each item
3. Use exact field names from the schema
4. If previous_items provided, find DIFFERENT items
5. Pay attention to feedback about missed items
6. Be thorough but accurate - don't hallucinate data

**Your Approach:**
1. Use search_for_patterns tool if available to identify relevant sections
2. Use get_content_section tool to focus on specific areas
3. Extract all items matching the extraction schema
4. Provide confidence scores based on completeness
5. List all indicators found in the content"""


# ===== Factory Function (for backward compatibility) =====


def create_extraction_agent(
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    extraction_type: str = "generic",
) -> ExtractionAgent:
    """
    Create a customized extraction agent.

    Args:
        model: LLM model to use (default: from env or "openai:gpt-4o")
        system_prompt: Custom system prompt (optional, overrides default)
        extraction_type: Type of extraction (for logging/debugging)

    Returns:
        Configured extraction agent
    """
    agent = ExtractionAgent(model=model)
    if system_prompt:
        # Create a new agent with custom prompt
        agent._agent = Agent[ExtractionDeps, ExtractionResult](
            model=agent.model,
            deps_type=ExtractionDeps,
            system_prompt=system_prompt,
        )
    return agent


# ===== Default Instance =====

extraction_agent = ExtractionAgent()
