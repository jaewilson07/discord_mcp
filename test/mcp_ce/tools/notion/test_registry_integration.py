"""Test that Notion tools work correctly with enforced ToolResponse registry."""

import pytest
from registry import get_registry
from mcp_ce.tools.model import ToolResponse


@pytest.mark.notion
@pytest.mark.integration
class TestNotionToolsRegistration:
    """Test that all Notion tools are properly registered with ToolResponse enforcement."""

    def test_notion_server_in_registry(self):
        """Test that notion server exists in registry."""
        # Import to trigger registration
        from mcp_ce.tools.notion.create_page import create_notion_page
        from mcp_ce.tools.notion.get_page import get_notion_page
        from mcp_ce.tools.notion.update_page import update_notion_page
        from mcp_ce.tools.notion.search_notion import search_notion
        from mcp_ce.tools.notion.add_comment import add_notion_comment
        from mcp_ce.tools.notion.query_database import query_notion_database

        registry = get_registry()

        assert "notion" in registry, "Notion server should be in registry"

    def test_all_notion_tools_registered(self):
        """Test that all Notion tools are registered."""
        # Import to trigger registration
        from mcp_ce.tools.notion.create_page import create_notion_page
        from mcp_ce.tools.notion.get_page import get_notion_page
        from mcp_ce.tools.notion.update_page import update_notion_page
        from mcp_ce.tools.notion.search_notion import search_notion
        from mcp_ce.tools.notion.add_comment import add_notion_comment
        from mcp_ce.tools.notion.query_database import query_notion_database

        registry = get_registry()

        expected_tools = [
            "create_notion_page",
            "get_notion_page",
            "update_notion_page",
            "search_notion",
            "add_notion_comment",
            "query_notion_database",
        ]

        for tool_name in expected_tools:
            assert (
                tool_name in registry["notion"]
            ), f"Tool '{tool_name}' should be registered"

    @pytest.mark.asyncio
    async def test_search_notion_returns_toolresponse(self):
        """Test that search_notion returns ToolResponse (even on error)."""
        from mcp_ce.tools.notion.search_notion import search_notion

        # Call with minimal params (will fail due to missing env vars, but should return ToolResponse)
        result = await search_notion(query="test", filter_type="page")

        assert isinstance(
            result, ToolResponse
        ), "search_notion should return ToolResponse"
        assert hasattr(result, "is_success")
        assert hasattr(result, "result")
        assert hasattr(result, "error")

    @pytest.mark.asyncio
    async def test_get_notion_page_returns_toolresponse(self, sample_notion_page_id):
        """Test that get_notion_page returns ToolResponse."""
        from mcp_ce.tools.notion.get_page import get_notion_page

        result = await get_notion_page(page_id=sample_notion_page_id)

        assert isinstance(
            result, ToolResponse
        ), "get_notion_page should return ToolResponse"
        assert hasattr(result, "is_success")
        assert hasattr(result, "result")
        assert hasattr(result, "error")

    @pytest.mark.asyncio
    async def test_query_database_returns_toolresponse(self, notion_database_id):
        """Test that query_notion_database returns ToolResponse."""
        from mcp_ce.tools.notion.query_database import query_notion_database

        result = await query_notion_database(database_id=notion_database_id)

        assert isinstance(
            result, ToolResponse
        ), "query_notion_database should return ToolResponse"
        assert hasattr(result, "is_success")
        assert hasattr(result, "result")
        assert hasattr(result, "error")

    @pytest.mark.asyncio
    async def test_create_notion_page_returns_toolresponse(self, notion_database_id):
        """Test that create_notion_page returns ToolResponse."""
        from mcp_ce.tools.notion.create_page import create_notion_page

        result = await create_notion_page(
            database_id=notion_database_id, title="Registry Test Page", properties={}
        )

        assert isinstance(
            result, ToolResponse
        ), "create_notion_page should return ToolResponse"
        assert hasattr(result, "is_success")
        assert hasattr(result, "result")
        assert hasattr(result, "error")

    @pytest.mark.asyncio
    async def test_update_notion_page_returns_toolresponse(self, sample_notion_page_id):
        """Test that update_notion_page returns ToolResponse."""
        from mcp_ce.tools.notion.update_page import update_notion_page

        result = await update_notion_page(
            page_id=sample_notion_page_id,
            properties={"Name": {"title": [{"text": {"content": "Updated Title"}}]}},
        )

        assert isinstance(
            result, ToolResponse
        ), "update_notion_page should return ToolResponse"
        assert hasattr(result, "is_success")
        assert hasattr(result, "result")
        assert hasattr(result, "error")

    @pytest.mark.asyncio
    async def test_add_comment_returns_toolresponse(self, sample_notion_page_id):
        """Test that add_notion_comment returns ToolResponse."""
        from mcp_ce.tools.notion.add_comment import add_notion_comment

        result = await add_notion_comment(
            page_id=sample_notion_page_id,
            comment_text="Test comment from registry integration test",
        )

        assert isinstance(
            result, ToolResponse
        ), "add_notion_comment should return ToolResponse"
        assert hasattr(result, "is_success")
        assert hasattr(result, "result")
        assert hasattr(result, "error")


@pytest.mark.notion
@pytest.mark.unit
class TestNotionToolsErrorHandling:
    """Test that Notion tools handle errors correctly with ToolResponse."""

    @pytest.mark.asyncio
    async def test_invalid_page_id_returns_error_toolresponse(self):
        """Test that invalid page ID returns ToolResponse with error."""
        from mcp_ce.tools.notion.get_page import get_notion_page

        result = await get_notion_page(page_id="invalid-page-id-12345")

        assert isinstance(result, ToolResponse)
        # Should be unsuccessful due to invalid ID
        assert result.is_success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_invalid_database_id_returns_error_toolresponse(self):
        """Test that invalid database ID returns ToolResponse with error."""
        from mcp_ce.tools.notion.query_database import query_notion_database

        result = await query_notion_database(database_id="invalid-db-id-12345")

        assert isinstance(result, ToolResponse)
        # Should be unsuccessful due to invalid ID
        assert result.is_success is False
        assert result.error is not None


@pytest.mark.notion
@pytest.mark.unit
class TestRegistryPreservesToolMetadata:
    """Test that registry decorator preserves function metadata."""

    def test_function_name_preserved(self):
        """Test that registered function keeps its name."""
        from mcp_ce.tools.notion.search_notion import search_notion

        assert search_notion.__name__ == "search_notion"

    def test_function_docstring_preserved(self):
        """Test that registered function keeps its docstring."""
        from mcp_ce.tools.notion.search_notion import search_notion

        assert search_notion.__doc__ is not None
        assert len(search_notion.__doc__) > 0

    def test_function_is_coroutine(self):
        """Test that async functions remain coroutines after registration."""
        import inspect
        from mcp_ce.tools.notion.search_notion import search_notion

        assert inspect.iscoroutinefunction(search_notion)
