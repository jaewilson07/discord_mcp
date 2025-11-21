"""
Generic Validation Agent.

Reusable for validating extraction completeness and quality.
Can be configured for different validation criteria.
Follows BaseAgent pattern with proper Logfire integration.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Any, Callable

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ..base_agent import BaseAgent, AgentDependencies
from .._model_helper import _get_model

logger = logging.getLogger(__name__)


# ===== Models =====


class ValidationResult(BaseModel):
    """Result from validation assessment."""

    is_complete: bool = Field(description="Whether extraction is complete")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in completeness assessment"
    )
    missing_indicators: List[str] = Field(
        description="Indicators that suggest missed items", default_factory=list
    )
    quality_issues: List[str] = Field(
        description="Quality issues with extracted items", default_factory=list
    )
    should_retry: bool = Field(description="Whether to retry extraction")
    metadata: Optional[dict] = Field(
        default=None, description="Additional validation metadata"
    )


# ===== Dependencies =====


@dataclass
class ValidationDeps(AgentDependencies):
    """Dependencies for validation agent."""

    # Required fields using Ellipsis to allow ordering after default fields
    content: str = field(default=...)  # Required field
    extracted_items: List[Any] = field(default=...)  # Required field
    iteration: int = field(default=...)  # Required field
    max_iterations: int = field(default=...)  # Required field
    # Optional fields with defaults
    quality_checker: Optional[Callable] = None  # Inject quality checking logic
    completeness_checker: Optional[Callable] = None  # Inject completeness checking
    context: Optional[dict] = None  # Additional validation context


# ===== Agent Class =====


class ValidationAgent(BaseAgent[ValidationDeps, ValidationResult]):
    """
    Agent for validating extraction completeness and quality.

    Capabilities:
    - Assess extraction completeness
    - Check quality of extracted items
    - Recommend retries when needed
    - Provide detailed validation feedback
    """

    def __init__(self, model: Optional[str] = None, **kwargs):
        """Initialize the validation agent."""
        super().__init__(
            model=model or _get_model("validation"),
            name="ValidationAgent",
            **kwargs,
        )

    def _create_agent(self, **kwargs) -> Agent:
        """Create the Pydantic-AI agent with tools and prompts."""
        agent = Agent[ValidationDeps, ValidationResult](
            model=self.model,
            deps_type=ValidationDeps,
            system_prompt=self.get_system_prompt(),
            **kwargs,
        )

        @agent.tool
        async def analyze_completeness(ctx: RunContext[ValidationDeps]) -> str:
            """Analyze whether extraction captured all items."""
            if not ctx.deps.completeness_checker:
                return "No completeness checker provided. Manual assessment needed."

            try:
                logfire.info("Analyzing extraction completeness")

                # Use injected completeness checker
                analysis = await ctx.deps.completeness_checker(
                    content=ctx.deps.content,
                    extracted_items=ctx.deps.extracted_items,
                    iteration=ctx.deps.iteration,
                    max_iterations=ctx.deps.max_iterations,
                    context=ctx.deps.context or {},
                )

                logfire.info(
                    "Completeness analysis done",
                    completeness=analysis.get("completeness", 0.0),
                    quality=analysis.get("quality", 0.0),
                )

                return str(analysis)

            except Exception as e:
                logger.error(f"Completeness analysis error: {e}", exc_info=True)
                logfire.error("Completeness analysis error", error=str(e))
                return f"Error analyzing completeness: {str(e)}"

        @agent.tool
        async def check_quality(ctx: RunContext[ValidationDeps]) -> str:
            """Check quality of individual extracted items."""
            if not ctx.deps.quality_checker:
                return "No quality checker provided. Manual assessment needed."

            try:
                logfire.info("Checking item quality")

                # Use injected quality checker
                quality_report = await ctx.deps.quality_checker(
                    items=ctx.deps.extracted_items, context=ctx.deps.context or {}
                )

                logfire.info(
                    "Quality check done", issues=len(quality_report.get("issues", []))
                )

                return str(quality_report)

            except Exception as e:
                logger.error(f"Quality check error: {e}", exc_info=True)
                logfire.error("Quality check error", error=str(e))
                return f"Error checking quality: {str(e)}"

        return agent

    def get_system_prompt(self) -> str:
        """Get the base system prompt for this agent."""
        return """You are a validation specialist.

Your job is to assess whether all items have been found from the content.

**Assessment Criteria:**
1. Compare number of items extracted vs. indicators in content
2. Check if item quality is good (all required fields present)
3. Identify any patterns suggesting missed items
4. Recommend retry if confident items were missed

**Important:**
- Don't expect perfection - some indicators may be false positives
- Consider iteration count - don't retry endlessly
- Balance between completeness and quality
- Be pragmatic about what's achievable

**Your Approach:**
1. Use analyze_completeness tool to assess overall extraction
2. Use check_quality tool to validate individual items
3. Provide clear feedback on what's missing or needs improvement
4. Recommend retry only when confident items were missed"""


# ===== Factory Function (for backward compatibility) =====


def create_validation_agent(
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    validation_type: str = "generic",
) -> ValidationAgent:
    """
    Create a customized validation agent.

    Args:
        model: LLM model to use (default: from env or "openai:gpt-4o")
        system_prompt: Custom system prompt (optional, overrides default)
        validation_type: Type of validation (for logging/debugging)

    Returns:
        Configured validation agent
    """
    agent = ValidationAgent(model=model)
    if system_prompt:
        # Create a new agent with custom prompt
        agent._agent = Agent[ValidationDeps, ValidationResult](
            model=agent.model,
            deps_type=ValidationDeps,
            system_prompt=system_prompt,
        )
    return agent


# ===== Default Instance =====

validation_agent = ValidationAgent()
