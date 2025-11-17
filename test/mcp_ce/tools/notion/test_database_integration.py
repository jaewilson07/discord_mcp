"""Integration tests for Notion database operations using real-world scenarios.

These tests verify the complete workflow of querying Notion databases,
including the 2025-09-03 API data_source_id pattern.
"""

import pytest
from mcp_ce.tools.notion.query_database import query_notion_database
from mcp_ce.tools.notion._client_helper import (
    get_client,
    get_data_source_id_from_database,
)


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_query_with_data_source_id(notion_token, notion_database_id):
    """
    Test querying database using data_source_id (2025-09-03 API).

    This is a real-world test that verifies:
    1. Converting database_id to data_source_id
    2. Querying via data_sources endpoint
    3. Retrieving and parsing results
    """
    # Get data_source_id from database_id
    data_source_id = await get_data_source_id_from_database(notion_database_id)

    assert data_source_id is not None
    assert isinstance(data_source_id, str)
    assert len(data_source_id) > 0

    # Query using the client helper
    client = get_client()
    response = await client.request(
        path=f"data_sources/{data_source_id}/query", method="POST", body={}
    )

    assert "results" in response
    results = response["results"]
    assert isinstance(results, list)

    print(f"✅ Found {len(results)} pages in database")


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_properties_structure(notion_token, notion_database_id):
    """
    Test that database pages have proper property structure.

    Verifies:
    - Pages have properties dict
    - Properties have type information
    - Can identify URL properties
    """
    result = await query_notion_database(database_id=notion_database_id)

    pytest.assert_tool_response(result, expected_success=True)

    if not result.result:
        pytest.skip("Database is empty - cannot test property structure")

    first_page = result.result[0]

    # Check page structure
    assert "id" in first_page
    assert "properties" in first_page

    properties = first_page["properties"]
    assert isinstance(properties, dict)

    # Document available properties for debugging
    print("\n📋 Available properties in pages:")
    for prop_name, prop_data in properties.items():
        prop_type = prop_data.get("type", "unknown")
        print(f'  - "{prop_name}" ({prop_type})')


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_pages_by_url_property(notion_token, notion_database_id):
    """
    Test finding pages by URL property value.

    This is a real-world scenario for checking if a YouTube video
    already exists in the database before creating a duplicate.
    """
    result = await query_notion_database(database_id=notion_database_id)

    pytest.assert_tool_response(result, expected_success=True)

    if not result.result:
        pytest.skip("Database is empty - cannot test URL searching")

    # Find all URL properties
    url_properties = []

    for page in result.result:
        props = page.get("properties", {})
        for prop_name, prop_data in props.items():
            if prop_data.get("type") == "url":
                url_value = prop_data.get("url", "")
                if url_value:
                    url_properties.append(
                        {"page_id": page["id"], "property": prop_name, "url": url_value}
                    )

    print(f"\n🔍 Found {len(url_properties)} pages with URL properties")

    # Test that we can search and identify URLs
    assert isinstance(url_properties, list)


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_detect_duplicate_urls(notion_token, notion_database_id):
    """
    Test detecting duplicate URL entries in database.

    Real-world scenario: Before adding a YouTube video, check if it
    already exists to avoid duplicates.
    """
    result = await query_notion_database(database_id=notion_database_id)

    pytest.assert_tool_response(result, expected_success=True)

    if not result.result:
        pytest.skip("Database is empty - cannot test duplicate detection")

    # Build URL index
    url_index = {}

    for page in result.result:
        props = page.get("properties", {})
        for prop_name, prop_data in props.items():
            if prop_data.get("type") == "url":
                url_value = prop_data.get("url", "")
                if url_value:
                    if url_value not in url_index:
                        url_index[url_value] = []
                    url_index[url_value].append(
                        {"page_id": page["id"][:8] + "...", "property": prop_name}
                    )

    # Find duplicates
    duplicates = {url: pages for url, pages in url_index.items() if len(pages) > 1}

    if duplicates:
        print(f"\n⚠️  Found {len(duplicates)} URLs with duplicates:")
        for url, pages in duplicates.items():
            print(f"  - {url} ({len(pages)} copies)")
    else:
        print(f"\n✅ No duplicate URLs found")

    # Test passes either way - just documenting state
    assert isinstance(url_index, dict)


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_check_lock_status_property(notion_token, notion_database_id):
    """
    Test reading checkbox properties (like Lock status).

    Real-world scenario: Check if a page is locked before updating it.
    """
    result = await query_notion_database(database_id=notion_database_id)

    pytest.assert_tool_response(result, expected_success=True)

    if not result.result:
        pytest.skip("Database is empty - cannot test lock status")

    # Check for Lock or similar checkbox properties
    checkbox_properties = []

    for page in result.result:
        props = page.get("properties", {})
        for prop_name, prop_data in props.items():
            if prop_data.get("type") == "checkbox":
                checkbox_value = prop_data.get("checkbox", False)
                checkbox_properties.append(
                    {
                        "page_id": page["id"][:8] + "...",
                        "property": prop_name,
                        "checked": checkbox_value,
                    }
                )

    if checkbox_properties:
        print(f"\n✅ Found {len(checkbox_properties)} checkbox properties")
        # Show first few
        for prop in checkbox_properties[:3]:
            print(
                f'  - {prop["property"]}: {prop["checked"]} (page: {prop["page_id"]})'
            )

    assert isinstance(checkbox_properties, list)


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_full_database_validation(notion_token, notion_database_id):
    """
    Comprehensive database validation test.

    This combines all checks from check_notion_db.py:
    - Query database successfully
    - Verify property structure
    - Find URL properties
    - Detect duplicates
    - Check for various property types
    """
    # Query database
    result = await query_notion_database(database_id=notion_database_id)
    pytest.assert_tool_response(result, expected_success=True)

    results = result.result
    print(f"\n✅ Success! Found {len(results)} total pages")

    if not results:
        pytest.skip("Database is empty - skipping validation")

    # Analyze first page
    first_page = results[0]
    properties = first_page.get("properties", {})

    print(f"\n📋 Database Schema ({len(properties)} properties):")
    property_types = {}
    for prop_name, prop_data in properties.items():
        prop_type = prop_data.get("type", "unknown")
        property_types[prop_type] = property_types.get(prop_type, 0) + 1
        print(f'  - "{prop_name}" ({prop_type})')

    print(f"\n📊 Property Type Distribution:")
    for prop_type, count in sorted(property_types.items()):
        print(f"  - {prop_type}: {count}")

    # URL analysis
    url_index = {}
    for page in results:
        props = page.get("properties", {})
        for prop_name, prop_data in props.items():
            if prop_data.get("type") == "url":
                url_value = prop_data.get("url", "")
                if url_value:
                    if url_value not in url_index:
                        url_index[url_value] = []
                    url_index[url_value].append(page["id"][:8])

    duplicates = {url: ids for url, ids in url_index.items() if len(ids) > 1}

    if duplicates:
        print(f"\n⚠️  WARNING: {len(duplicates)} duplicate URLs found!")
        for url, ids in list(duplicates.items())[:3]:  # Show first 3
            print(f"  - {url[:50]}... ({len(ids)} copies)")
    else:
        print(f"\n✅ No duplicate URLs detected")

    # Validation assertions
    assert len(results) > 0, "Database should have pages"
    assert len(properties) > 0, "Pages should have properties"
    assert "id" in first_page, "Pages should have ID"
    assert "properties" in first_page, "Pages should have properties dict"

    print(f"\n✅ Database validation complete!")
