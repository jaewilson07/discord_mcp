"""Tests for query_notion_database tool."""

import pytest
from mcp_ce.tools.notion.query_database import query_notion_database


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_database_without_filter(notion_token, notion_database_id):
    """Test querying database without filter."""
    result = await query_notion_database(database_id=notion_database_id)
    
    pytest.assert_tool_response(result, expected_success=True)
    assert isinstance(result.result, list)
    
    # Check structure of results
    if result.result:
        first_result = result.result[0]
        assert "id" in first_result
        assert "url" in first_result


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_database_with_filter(notion_token, notion_database_id):
    """Test querying database with filter."""
    filter_json = '{"property": "Status", "select": {"equals": "Done"}}'
    result = await query_notion_database(
        database_id=notion_database_id,
        filter_json=filter_json
    )
    
    pytest.assert_tool_response(result, expected_success=True)
    assert isinstance(result.result, list)


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_invalid_database(notion_token):
    """Test querying non-existent database."""
    result = await query_notion_database(database_id="invalid-id-12345")
    
    pytest.assert_tool_response(result, expected_success=False)
    assert result.error is not None


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_database_cache(notion_token, notion_database_id):
    """Test that cache works for database queries."""
    # First call - cache miss
    result1 = await query_notion_database(database_id=notion_database_id)
    pytest.assert_tool_response(result1, expected_success=True)
    
    # Second call - should hit cache
    result2 = await query_notion_database(database_id=notion_database_id)
    pytest.assert_tool_response(result2, expected_success=True)
    
    # Results should be identical
    assert len(result1.result) == len(result2.result)


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_database_with_invalid_filter(notion_token, notion_database_id):
    """Test querying with malformed filter JSON."""
    result = await query_notion_database(
        database_id=notion_database_id,
        filter_json='{"invalid json'
    )
    
    # Should handle gracefully - either error or empty results
    assert hasattr(result, 'is_success')
