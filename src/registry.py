"""
Tool registration system.

Provides decorator-based registration for MCP tools with auto-discovery.
"""

import functools
import inspect
from typing import Any, Callable, Dict

_registry: Dict[str, Dict[str, Callable]] = {}


def register_command(server: str, tool: str):
    """
    Decorator to register a tool with a server.

    Enforces that the tool function must return a ToolResponse object.
    If the function returns a dict (legacy format), a warning is issued.

    Args:
        server: Server name (e.g., "discord", "youtube")
        tool: Tool name (e.g., "send_message", "get_video_metadata")

    Returns:
        Decorated function registered in the global registry

    Example:
        @register_command("discord", "send_message")
        async def send_message(channel_id: str, content: str) -> ToolResponse:
            return ToolResponse(is_success=True, result={"message_id": "123"})

    Raises:
        TypeError: If the function returns a non-ToolResponse object
    """

    def decorator(func: Callable) -> Callable:
        # Determine if function is async
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)

                # Validate return type
                if not _is_tool_response(result):
                    raise TypeError(
                        f"Tool '{server}.{tool}' must return ToolResponse, "
                        f"got {type(result).__name__}. "
                        f"Import: from mcp_ce.tools.model import ToolResponse"
                    )

                return result

            wrapper = async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)

                # Validate return type
                if not _is_tool_response(result):
                    raise TypeError(
                        f"Tool '{server}.{tool}' must return ToolResponse, "
                        f"got {type(result).__name__}. "
                        f"Import: from mcp_ce.tools.model import ToolResponse"
                    )

                return result

            wrapper = sync_wrapper

        # Register the wrapper
        if server not in _registry:
            _registry[server] = {}
        _registry[server][tool] = wrapper

        return wrapper

    return decorator


def _is_tool_response(obj: Any) -> bool:
    """
    Check if an object is a ToolResponse.

    Uses duck typing to avoid circular imports.

    Args:
        obj: Object to check

    Returns:
        True if object has ToolResponse attributes
    """
    return (
        hasattr(obj, "is_success") and hasattr(obj, "result") and hasattr(obj, "error")
    )


def get_registry() -> Dict[str, Dict[str, Callable]]:
    """
    Get the current tool registry.

    Returns:
        Dictionary mapping server names to tool dictionaries
        Structure: {server_name: {tool_name: tool_function}}
    """
    return _registry.copy()


def get_tool(server: str, tool: str) -> Callable | None:
    """
    Get a specific tool function from the registry.

    Args:
        server: Server name
        tool: Tool name

    Returns:
        Tool function if found, None otherwise
    """
    return _registry.get(server, {}).get(tool)


def get_server_tools(server: str) -> Dict[str, Callable]:
    """
    Get all tools for a specific server.

    Args:
        server: Server name

    Returns:
        Dictionary mapping tool names to tool functions
    """
    return _registry.get(server, {}).copy()


def list_servers() -> list[str]:
    """
    List all registered servers.

    Returns:
        List of server names
    """
    return list(_registry.keys())
