"""
Logfire Configuration for Pydantic-AI Agents.

Centralized Logfire setup for all agents in the project.
"""

import os
import logging
from typing import Optional

import logfire

logger = logging.getLogger(__name__)

# Track if Logfire has been initialized
_logfire_initialized = False


def configure_logfire(
    project_name: Optional[str] = None,
    send_to_logfire: str = "if-token-present",
    enable: bool = True,
) -> bool:
    """
    Configure Logfire for Pydantic-AI agents.

    This should be called once at application startup, before creating any agents.

    Args:
        project_name: Optional project name (deprecated, not needed)
        send_to_logfire: When to send logs ("if-token-present", "always", "never")
        enable: Whether to enable Logfire (default: True)

    Returns:
        True if Logfire was successfully configured, False otherwise

    Environment Variables:
        LOGFIRE_TOKEN: Logfire authentication token (optional)
        ENABLE_LOGFIRE: Set to "false" to disable Logfire

    Example:
        >>> from mcp_ce.agentic_tools.logfire_config import configure_logfire
        >>> configure_logfire()
        True
    """
    global _logfire_initialized

    if _logfire_initialized:
        logger.debug("Logfire already initialized, skipping")
        return True

    # Check if Logfire is disabled
    if not enable or os.getenv("ENABLE_LOGFIRE", "true").lower() == "false":
        logger.info("Logfire disabled by configuration")
        return False

    try:
        # Configure Logfire
        logfire.configure(send_to_logfire=send_to_logfire)

        # Instrument Pydantic-AI for automatic logging
        logfire.instrument_pydantic_ai()

        _logfire_initialized = True
        logger.info(
            "Logfire configured successfully",
            send_to_logfire=send_to_logfire,
        )

        return True

    except Exception as e:
        logger.warning(f"Failed to configure Logfire: {e}", exc_info=True)
        return False


def is_logfire_enabled() -> bool:
    """Check if Logfire has been initialized."""
    return _logfire_initialized

