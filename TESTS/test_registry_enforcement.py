"""Test registry.py ToolResponse enforcement."""

import pytest
from registry import register_command, get_registry
from mcp_ce.tools.model import ToolResponse


class TestRegistryEnforcement:
    """Test that register_command enforces ToolResponse return type."""

    def test_valid_async_tool_with_toolresponse(self):
        """Test that async tools returning ToolResponse are accepted."""

        @register_command("test_enforcement", "valid_async")
        async def valid_async_tool(param: str) -> ToolResponse:
            return ToolResponse(is_success=True, result={"param": param})

        # Should execute without error
        import asyncio

        result = asyncio.run(valid_async_tool("test"))

        assert isinstance(result, ToolResponse)
        assert result.is_success is True
        assert result.result == {"param": "test"}

    def test_valid_sync_tool_with_toolresponse(self):
        """Test that sync tools returning ToolResponse are accepted."""

        @register_command("test_enforcement", "valid_sync")
        def valid_sync_tool(param: str) -> ToolResponse:
            return ToolResponse(is_success=True, result={"param": param})

        # Should execute without error
        result = valid_sync_tool("test")

        assert isinstance(result, ToolResponse)
        assert result.is_success is True
        assert result.result == {"param": "test"}

    def test_invalid_async_tool_with_dict_raises_typeerror(self):
        """Test that async tools returning dict are rejected."""

        @register_command("test_enforcement", "invalid_async")
        async def invalid_async_tool(param: str) -> dict:
            return {"success": True, "data": param}

        # Should raise TypeError when executed
        import asyncio

        with pytest.raises(TypeError) as exc_info:
            asyncio.run(invalid_async_tool("test"))

        assert "must return ToolResponse" in str(exc_info.value)
        assert "got dict" in str(exc_info.value)

    def test_invalid_sync_tool_with_dict_raises_typeerror(self):
        """Test that sync tools returning dict are rejected."""

        @register_command("test_enforcement", "invalid_sync")
        def invalid_sync_tool(param: str) -> dict:
            return {"success": True, "data": param}

        # Should raise TypeError when executed
        with pytest.raises(TypeError) as exc_info:
            invalid_sync_tool("test")

        assert "must return ToolResponse" in str(exc_info.value)
        assert "got dict" in str(exc_info.value)

    def test_tools_are_registered_in_registry(self):
        """Test that decorated tools appear in the registry."""

        @register_command("test_enforcement", "registered_tool")
        async def registered_tool() -> ToolResponse:
            return ToolResponse(is_success=True, result={})

        registry = get_registry()

        assert "test_enforcement" in registry
        assert "registered_tool" in registry["test_enforcement"]

    def test_error_message_includes_import_hint(self):
        """Test that error message includes helpful import hint."""

        @register_command("test_enforcement", "needs_import_hint")
        async def tool_without_import() -> dict:
            return {}

        import asyncio

        with pytest.raises(TypeError) as exc_info:
            asyncio.run(tool_without_import())

        error_msg = str(exc_info.value)
        assert "from mcp_ce.tools.model import ToolResponse" in error_msg

    def test_toolresponse_with_error(self):
        """Test that ToolResponse with is_success=False is accepted."""

        @register_command("test_enforcement", "error_response")
        async def tool_with_error() -> ToolResponse:
            return ToolResponse(
                is_success=False, result=None, error="Something went wrong"
            )

        import asyncio

        result = asyncio.run(tool_with_error())

        assert isinstance(result, ToolResponse)
        assert result.is_success is False
        assert result.error == "Something went wrong"
        assert result.result is None


@pytest.mark.unit
class TestRegistryBasicFunctionality:
    """Test basic registry functionality."""

    def test_get_registry_returns_dict(self):
        """Test that get_registry returns a dictionary."""
        registry = get_registry()
        assert isinstance(registry, dict)

    def test_multiple_servers_in_registry(self):
        """Test that registry can handle multiple servers."""

        @register_command("server_a", "tool_1")
        async def tool_a1() -> ToolResponse:
            return ToolResponse(is_success=True, result={})

        @register_command("server_b", "tool_1")
        async def tool_b1() -> ToolResponse:
            return ToolResponse(is_success=True, result={})

        registry = get_registry()

        assert "server_a" in registry
        assert "server_b" in registry
        assert "tool_1" in registry["server_a"]
        assert "tool_1" in registry["server_b"]

    def test_multiple_tools_per_server(self):
        """Test that a server can have multiple tools."""

        @register_command("multi_tool_server", "tool_1")
        async def multi_tool_1() -> ToolResponse:
            return ToolResponse(is_success=True, result={"tool": 1})

        @register_command("multi_tool_server", "tool_2")
        async def multi_tool_2() -> ToolResponse:
            return ToolResponse(is_success=True, result={"tool": 2})

        @register_command("multi_tool_server", "tool_3")
        async def multi_tool_3() -> ToolResponse:
            return ToolResponse(is_success=True, result={"tool": 3})

        registry = get_registry()

        assert "multi_tool_server" in registry
        assert len(registry["multi_tool_server"]) >= 3
        assert "tool_1" in registry["multi_tool_server"]
        assert "tool_2" in registry["multi_tool_server"]
        assert "tool_3" in registry["multi_tool_server"]
