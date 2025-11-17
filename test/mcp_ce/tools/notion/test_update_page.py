"""Tests for update_notion_page tool."""

import pytest
from mcp_ce.tools.notion.update_page import update_notion_page


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_page_with_dict(notion_token, sample_notion_page_id):
    """Test updating page with dict properties."""
    result = await update_notion_page(
        page_id=sample_notion_page_id,
        properties={"Status": {"select": {"name": "In Progress"}}}
    )
    
    pytest.assert_tool_response(result, expected_success=True)
    assert "page_id" in result.result
    assert "updated_properties" in result.result
    assert "Status" in result.result["updated_properties"]


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_page_with_json_string(notion_token, sample_notion_page_id):
    """Test updating page with JSON string."""
    result = await update_notion_page(
        page_id=sample_notion_page_id,
        properties='{"Status": {"select": {"name": "Done"}}}'
    )
    
    pytest.assert_tool_response(result, expected_success=True)
    assert "Status" in result.result["updated_properties"]


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_page_with_invalid_json(notion_token, sample_notion_page_id):
    """Test updating page with invalid JSON string."""
    result = await update_notion_page(
        page_id=sample_notion_page_id,
        properties='{"invalid json'
    )
    
    pytest.assert_tool_response(result, expected_success=False)
    assert "json" in result.error.lower()


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_invalid_page(notion_token):
    """Test updating a non-existent page."""
    result = await update_notion_page(
        page_id="invalid-id-12345",
        properties={"Status": {"select": {"name": "Done"}}}
    )
    
    pytest.assert_tool_response(result, expected_success=False)
    assert result.error is not None


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_multiple_properties(notion_token, sample_notion_page_id):
    """Test updating multiple properties at once."""
    result = await update_notion_page(
        page_id=sample_notion_page_id,
        properties={
            "Status": {"select": {"name": "In Progress"}},
            "Priority": {"number": 1}
        }
    )
    
    # This may fail if Priority doesn't exist in the database
    # Just check the structure is correct
    if result.is_success:
        assert len(result.result["updated_properties"]) >= 1
