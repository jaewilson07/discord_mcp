"""
Model Helper for Agent Configuration.

Provides dynamic model selection from environment variables with fallback to defaults.
Similar pattern to MCP tools' model configuration.
"""

import os
from typing import Optional


def _get_model(agent_name: str, default_model: str = "openai:gpt-4o") -> str:
    """
    Get LLM model for an agent from environment variables.

    Checks for agent-specific env var first, then falls back to DEFAULT_AGENT_MODEL,
    then falls back to provided default.

    Args:
        agent_name: Name of the agent (e.g., "scraper", "extraction", "validation", "workflow")
        default_model: Fallback model if no env var is set (default: "openai:gpt-4o")

    Returns:
        Model string in format "provider:model-name" (e.g., "openai:gpt-4o")

    Environment Variables:
        SCRAPER_AGENT_MODEL: Model for scraper agent
        EXTRACTION_AGENT_MODEL: Model for extraction agent
        VALIDATION_AGENT_MODEL: Model for validation agent
        WORKFLOW_AGENT_MODEL: Model for workflow orchestrator
        DEFAULT_AGENT_MODEL: Default model for all agents (if specific not set)

    Example:
        # In .env file:
        # EXTRACTION_AGENT_MODEL=openai:gpt-4o-mini
        # DEFAULT_AGENT_MODEL=openai:gpt-4o

        model = _get_model("extraction")  # Returns "openai:gpt-4o-mini"
        model = _get_model("scraper")     # Returns "openai:gpt-4o" (DEFAULT_AGENT_MODEL)
        model = _get_model("other")       # Returns "openai:gpt-4o" (fallback default)
    """
    # Normalize agent name to uppercase for env var
    env_var_name = f"{agent_name.upper()}_AGENT_MODEL"

    # Try agent-specific env var first
    model = os.getenv(env_var_name)
    if model:
        return model

    # Fall back to default agent model
    model = os.getenv("DEFAULT_AGENT_MODEL")
    if model:
        return model

    # Fall back to provided default
    return default_model
