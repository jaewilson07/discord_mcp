"""Tests for create_notion_page tool."""

import pytest
from mcp_ce.tools.notion.create_page import create_notion_page


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_page_at_workspace_root(notion_token):
    """Test creating a page at workspace root."""
    result = await create_notion_page(
        title="Test Page from Pytest",
        content="This is a test page.\n\nIt has multiple paragraphs."
    )
    
    pytest.assert_tool_response(result, expected_success=True)
    
    assert "page_id" in result.result
    assert "url" in result.result
    assert "title" in result.result
    assert result.result["title"] == "Test Page from Pytest"
    assert result.result["page_id"] is not None


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_page_without_content(notion_token):
    """Test creating a page without content."""
    result = await create_notion_page(title="Empty Test Page")
    
    pytest.assert_tool_response(result, expected_success=True)
    assert result.result["page_id"] is not None
    assert result.result["title"] == "Empty Test Page"


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_page_with_invalid_parent(notion_token):
    """Test creating a page with invalid parent ID."""
    result = await create_notion_page(
        title="Invalid Parent Test",
        parent_page_id="invalid-id-12345"
    )
    
    pytest.assert_tool_response(result, expected_success=False)
    assert result.error is not None


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_page_multiline_content(notion_token):
    """Test creating a page with multiple paragraphs."""
    content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    result = await create_notion_page(
        title="Multi-paragraph Test",
        content=content
    )
    
    pytest.assert_tool_response(result, expected_success=True)
    assert result.result["page_id"] is not None
