"""Pytest configuration and shared fixtures.

This file provides:
- Common fixtures for all tests
- Environment setup
- Test utilities
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()


@pytest.fixture(scope="session")
def notion_token():
    """Get Notion token from environment."""
    token = os.getenv("NOTION_TOKEN")
    if not token:
        pytest.skip("NOTION_TOKEN not configured")
    return token


@pytest.fixture(scope="session")
def notion_database_id():
    """Get Notion database ID from environment."""
    db_id = os.getenv("NOTION_DATABASE_ID")
    if not db_id:
        pytest.skip("NOTION_DATABASE_ID not configured")
    return db_id


@pytest.fixture(scope="session")
def youtube_api_key():
    """Get YouTube API key from environment."""
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        pytest.skip("YOUTUBE_API_KEY not configured")
    return key


@pytest.fixture(scope="session")
def discord_token():
    """Get Discord token from environment."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        pytest.skip("DISCORD_TOKEN not configured")
    return token


@pytest.fixture
def sample_notion_page_id():
    """Get sample Notion page ID for testing."""
    page_id = os.getenv("TEST_NOTION_PAGE_ID")
    if not page_id:
        pytest.skip("TEST_NOTION_PAGE_ID not configured")
    return page_id


@pytest.fixture
def test_data_dir():
    """Get path to test data directory."""
    return Path(__file__).parent / "test_data"


# Utility functions for tests
def assert_tool_response(response, expected_success=True):
    """
    Assert that a ToolResponse has expected structure.
    
    Args:
        response: ToolResponse object to check
        expected_success: Expected value of is_success
    """
    assert hasattr(response, 'is_success'), "Response should have is_success attribute"
    assert hasattr(response, 'result'), "Response should have result attribute"
    assert hasattr(response, 'error'), "Response should have error attribute"
    assert response.is_success == expected_success, \
        f"Expected is_success={expected_success}, got {response.is_success}. Error: {response.error}"
    
    if expected_success:
        assert response.result is not None, "Successful response should have result"
        assert response.error is None, "Successful response should not have error"
    else:
        assert response.error is not None, "Failed response should have error"


# Make utility functions available to all tests
pytest.assert_tool_response = assert_tool_response
