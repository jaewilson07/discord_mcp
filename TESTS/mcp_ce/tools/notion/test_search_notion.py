"""Tests for search_notion tool."""

import pytest
from mcp_ce.tools.notion.search_notion import search_notion


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_pages(notion_token):
    """Test searching for pages."""
    result = await search_notion(query="Getting started", filter_type="page")
    
    pytest.assert_tool_response(result, expected_success=True)
    assert "results" in result.result
    assert "count" in result.result
    assert "query" in result.result
    assert result.result["query"] == "Getting started"


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_databases(notion_token):
    """Test searching for databases."""
    result = await search_notion(query="", filter_type="database")
    
    pytest.assert_tool_response(result, expected_success=True)
    assert "results" in result.result
    assert "count" in result.result


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_all(notion_token):
    """Test searching for both pages and databases."""
    result = await search_notion(query="test", filter_type="all")
    
    pytest.assert_tool_response(result, expected_success=True)
    assert "results" in result.result
    assert isinstance(result.result["results"], list)


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_no_results(notion_token):
    """Test search with no results."""
    result = await search_notion(
        query="xyzabc123nonexistent", 
        filter_type="page"
    )
    
    pytest.assert_tool_response(result, expected_success=True)
    assert result.result["count"] == 0
    assert len(result.result["results"]) == 0


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_cache(notion_token):
    """Test that cache works for search results."""
    # First call - cache miss
    result1 = await search_notion(query="test", filter_type="page")
    pytest.assert_tool_response(result1, expected_success=True)
    
    # Second call - should hit cache
    result2 = await search_notion(query="test", filter_type="page")
    pytest.assert_tool_response(result2, expected_success=True)
    
    # Results should be identical
    assert result1.result["count"] == result2.result["count"]
