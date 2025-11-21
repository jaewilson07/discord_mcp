"""
Extraction Agent Tool.

Exposes the ExtractionAgent as an MCP tool.
Simplified for MCP - takes content and schema name as string.
"""

from typing import Dict, Any, Optional, List
from registry import register_command
from mcp_ce.tools.model import ToolResponse, ToolResult
from dataclasses import dataclass
from pydantic import BaseModel

from ...agentic_tools.agents import ExtractionAgent, ExtractionDeps
from ...agentic_tools.logfire_config import configure_logfire

# Ensure Logfire is configured
configure_logfire()

# Create agent instance
_agent = ExtractionAgent()

# Schema registry for common extraction types
_SCHEMA_REGISTRY = {}


def register_extraction_schema(name: str, schema: type[BaseModel]):
    """Register an extraction schema for use by name."""
    _SCHEMA_REGISTRY[name] = schema


@dataclass
class ExtractionAgentResult(ToolResult):
    """Result from extraction agent tool."""

    items: List[Any]
    confidence: float
    indicators_found: List[str]
    metadata: Optional[dict] = None


@register_command("agents", "extraction_agent")
async def extraction_agent_tool(
    content: str,
    extraction_type: str = "generic",
    previous_items: Optional[List[Any]] = None,
    feedback: Optional[str] = None,
    context: Optional[dict] = None,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> ToolResponse:
    """
    Run the extraction agent to extract structured data from content.

    Args:
        content: Content to extract from
        extraction_type: Type of extraction (e.g., "event", "product", "article")
                        For custom schemas, register them first using register_extraction_schema()
        previous_items: Previously extracted items (to avoid duplicates) - JSON string
        feedback: Feedback about missed items
        context: Additional context for extraction - JSON string or dict
        request_id: Optional request ID for tracking
        user_id: Optional user ID for tracking

    Returns:
        ToolResponse with ExtractionAgentResult containing extracted items
    """
    try:
        # Get schema from registry or use a default
        extraction_schema = _SCHEMA_REGISTRY.get(extraction_type)
        if not extraction_schema:
            # For now, use a generic dict-based schema
            # In production, you'd want to register schemas properly
            from pydantic import create_model

            extraction_schema = create_model(
                "GenericItem", **{"data": (dict, Field(default_factory=dict))}
            )

        # Parse JSON strings if needed
        if isinstance(previous_items, str):
            import json

            previous_items = json.loads(previous_items)
        if isinstance(context, str):
            import json

            context = json.loads(context)

        deps = ExtractionDeps(
            content=content,
            extraction_schema=extraction_schema,
            previous_items=previous_items,
            feedback=feedback,
            context=context,
            request_id=request_id,
            user_id=user_id,
        )

        result = await _agent.run(
            f"Extract {extraction_type} items from the content",
            deps=deps,
        )

        # Convert agent output to tool result
        tool_result = ExtractionAgentResult(
            items=result.items,
            confidence=result.confidence,
            indicators_found=result.indicators_found,
            metadata=result.metadata,
        )

        return ToolResponse(is_success=True, result=tool_result)

    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Extraction agent failed: {str(e)}",
        )
