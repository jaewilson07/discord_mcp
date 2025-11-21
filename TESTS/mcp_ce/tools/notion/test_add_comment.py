"""Tests for add_notion_comment tool."""

import pytest
from mcp_ce.tools.notion.add_comment import add_notion_comment


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_comment(notion_token, sample_notion_page_id):
    """Test adding a comment to a page."""
    result = await add_notion_comment(
        page_id=sample_notion_page_id,
        comment_text="This is a test comment from pytest."
    )
    
    pytest.assert_tool_response(result, expected_success=True)
    assert "comment_id" in result.result
    assert "page_id" in result.result
    assert result.result["page_id"] == sample_notion_page_id


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_comment_with_emoji(notion_token, sample_notion_page_id):
    """Test adding a comment with emoji."""
    result = await add_notion_comment(
        page_id=sample_notion_page_id,
        comment_text="Test comment with emoji! 🎉 ✅ 🚀"
    )
    
    pytest.assert_tool_response(result, expected_success=True)
    assert result.result["comment_id"] is not None


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_comment_to_invalid_page(notion_token):
    """Test adding comment to non-existent page."""
    result = await add_notion_comment(
        page_id="invalid-id-12345",
        comment_text="This should fail"
    )
    
    pytest.assert_tool_response(result, expected_success=False)
    assert result.error is not None


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_empty_comment(notion_token, sample_notion_page_id):
    """Test adding empty comment."""
    result = await add_notion_comment(
        page_id=sample_notion_page_id,
        comment_text=""
    )
    
    # Empty comment might succeed or fail depending on API
    # Just verify it returns proper ToolResponse structure
    assert hasattr(result, 'is_success')
    assert hasattr(result, 'error')


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_long_comment(notion_token, sample_notion_page_id):
    """Test adding a long comment."""
    long_text = "This is a test comment. " * 50  # ~1250 characters
    result = await add_notion_comment(
        page_id=sample_notion_page_id,
        comment_text=long_text
    )
    
    pytest.assert_tool_response(result, expected_success=True)
    assert result.result["comment_id"] is not None
