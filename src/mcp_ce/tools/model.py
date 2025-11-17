from dataclasses import dataclass, asdict, field
from typing import Optional, Any


@dataclass
class ToolResult:

    def to_dict(self):
        """Convert ToolResult to dictionary."""
        return asdict(self)


@dataclass
class ToolResponse:
    """
    Standard response format for all MCP CE tools.

    Attributes:
        is_success: True if operation completed successfully
        result: The result data (any type) if successful, None if failed
        error: Error message if operation failed, None if successful
    """

    is_success: bool
    result: ToolResult | Any
    error: Optional[str] = None
