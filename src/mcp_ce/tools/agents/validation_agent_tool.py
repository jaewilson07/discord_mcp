"""
Validation Agent Tool.

Exposes the ValidationAgent as an MCP tool.
Simplified for MCP - takes content and extracted items as JSON.
"""

from typing import Dict, Any, Optional, List
from registry import register_command
from mcp_ce.tools.model import ToolResponse, ToolResult
from dataclasses import dataclass
import json

from ...agentic_tools.agents import ValidationAgent, ValidationDeps
from ...agentic_tools.logfire_config import configure_logfire

# Ensure Logfire is configured
configure_logfire()

# Create agent instance
_agent = ValidationAgent()


@dataclass
class ValidationAgentResult(ToolResult):
    """Result from validation agent tool."""

    is_complete: bool
    confidence: float
    missing_indicators: List[str]
    quality_issues: List[str]
    should_retry: bool
    metadata: Optional[dict] = None


@register_command("agents", "validation_agent")
async def validation_agent_tool(
    content: str,
    extracted_items: str,  # JSON string
    iteration: int,
    max_iterations: int = 2,
    context: Optional[str] = None,  # JSON string
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> ToolResponse:
    """
    Run the validation agent to validate extraction completeness and quality.

    Args:
        content: Original content that was extracted from
        extracted_items: JSON string of extracted items to validate
        iteration: Current iteration number
        max_iterations: Maximum number of iterations allowed (default: 2)
        context: Additional context for validation - JSON string (optional)
        request_id: Optional request ID for tracking
        user_id: Optional user ID for tracking

    Returns:
        ToolResponse with ValidationAgentResult containing validation assessment
    """
    try:
        # Parse JSON strings
        try:
            items = json.loads(extracted_items) if isinstance(extracted_items, str) else extracted_items
        except json.JSONDecodeError:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"Invalid JSON in extracted_items: {extracted_items}",
            )

        validation_context = None
        if context:
            try:
                validation_context = json.loads(context) if isinstance(context, str) else context
            except json.JSONDecodeError:
                validation_context = {}

        deps = ValidationDeps(
            content=content,
            extracted_items=items,
            iteration=iteration,
            max_iterations=max_iterations,
            context=validation_context,
            request_id=request_id,
            user_id=user_id,
        )

        result = await _agent.run(
            f"Validate extraction completeness and quality (iteration {iteration}/{max_iterations})",
            deps=deps,
        )

        # Convert agent output to tool result
        tool_result = ValidationAgentResult(
            is_complete=result.is_complete,
            confidence=result.confidence,
            missing_indicators=result.missing_indicators,
            quality_issues=result.quality_issues,
            should_retry=result.should_retry,
            metadata=result.metadata,
        )

        return ToolResponse(is_success=True, result=tool_result)

    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Validation agent failed: {str(e)}",
        )
