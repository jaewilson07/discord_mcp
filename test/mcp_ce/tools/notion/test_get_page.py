"""Tests for get_notion_page tool."""

import pytest
from mcp_ce.tools.notion.get_page import get_notion_page


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_existing_page(notion_token, sample_notion_page_id):
    """Test getting an existing page."""
    result = await get_notion_page(page_id=sample_notion_page_id)
    
    pytest.assert_tool_response(result, expected_success=True)
    
    page = result.result
    assert "id" in page
    assert "url" in page
    assert "created_time" in page
    assert "last_edited_time" in page
    assert "properties" in page
    assert "archived" in page
    assert isinstance(page["archived"], bool)


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_invalid_page(notion_token):
    """Test getting a non-existent page."""
    result = await get_notion_page(page_id="invalid-id-12345")
    
    pytest.assert_tool_response(result, expected_success=False)
    assert result.error is not None
    assert "error" in result.error.lower()


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_page_cache(notion_token, sample_notion_page_id):
    """Test that cache works for page retrieval."""
    # First call - cache miss
    result1 = await get_notion_page(page_id=sample_notion_page_id)
    pytest.assert_tool_response(result1, expected_success=True)
    
    # Second call - should hit cache
    result2 = await get_notion_page(page_id=sample_notion_page_id)
    pytest.assert_tool_response(result2, expected_success=True)
    
    # Results should be identical
    assert result1.result["id"] == result2.result["id"]
    assert result1.result["url"] == result2.result["url"]


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_page_properties_structure(notion_token, sample_notion_page_id):
    """Test that page properties have correct structure."""
    result = await get_notion_page(page_id=sample_notion_page_id)
    
    pytest.assert_tool_response(result, expected_success=True)
    
    properties = result.result["properties"]
    assert isinstance(properties, dict)
    
    # Each property should have type and value
    for prop_name, prop_data in properties.items():
        assert "type" in prop_data
        assert "value" in prop_data
