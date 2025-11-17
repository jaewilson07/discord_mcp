"""Query a Notion database with optional filters and sorting using 2025-09-03 API."""

import json
from typing import Optional, Union, List, Dict, Any
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import DatabaseQueryResult
from ._client_helper import get_client, get_data_source_id_from_database


@register_command("notion", "query_notion_database")
@cache_tool(ttl=180, id_param="database_id")  # Cache for 3 minutes
async def query_notion_database(
    database_id: str,
    filter_json: Optional[Union[str, Dict[str, Any]]] = None,
    sorts_json: Optional[Union[str, List[Dict[str, str]]]] = None,
    override_cache: bool = False,
) -> ToolResponse:
    """
    Query a Notion database with optional filters and sorting.

    Uses the 2025-09-03 API with data_source_id for querying.

    Args:
        database_id: The ID of the database to query
        filter_json: Filter criteria as JSON string or dict.
                    Example: {"property": "Status", "select": {"equals": "In Progress"}}
        sorts_json: Sort criteria as JSON string or list.
                   Example: [{"property": "Created", "direction": "descending"}]
        override_cache: Whether to bypass cache and force fresh query (default: False)

    Returns:
        ToolResponse with DatabaseQueryResult dataclass containing:
        - results: List of page results
        - has_more: Whether there are more results
        - next_cursor: Cursor for pagination
        - count: Number of results returned
    """
    # Parse JSON parameters
    filter_obj = None
    sorts_obj = None

    try:
        if filter_json:
            filter_obj = (
                json.loads(filter_json) if isinstance(filter_json, str) else filter_json
            )
        if sorts_json:
            sorts_obj = (
                json.loads(sorts_json) if isinstance(sorts_json, str) else sorts_json
            )
    except json.JSONDecodeError as e:
        return ToolResponse(
            is_success=False, result=None, error=f"Invalid JSON: {str(e)}"
        )

    try:
        client = get_client()

        # Step 1: Get data_source_id from database_id (2025-09-03 API requirement)
        data_source_id = await get_data_source_id_from_database(database_id)

        # Step 2: Query using data_sources endpoint
        body = {}
        if filter_obj:
            body["filter"] = filter_obj
        if sorts_obj:
            body["sorts"] = sorts_obj

        response = await client.request(
            path=f"data_sources/{data_source_id}/query", method="POST", body=body
        )

        results = response.get("results", [])
        has_more = response.get("has_more", False)
        next_cursor = response.get("next_cursor")

        if not results:
            result = DatabaseQueryResult(
                results=[], has_more=False, next_cursor=None, count=0
            )
            return ToolResponse(is_success=True, result=result)

        # Format results
        formatted_results = []
        for entry in results:
            entry_id = entry.get("id", "unknown")

            # Extract title/name
            title = "Untitled"
            if "properties" in entry:
                props = entry["properties"]
                for prop_name in ["Name", "Title", "title"]:
                    if prop_name in props:
                        prop_obj = props[prop_name]
                        if "title" in prop_obj and prop_obj["title"]:
                            title = prop_obj["title"][0]["text"]["content"]
                            break

            # Extract key properties
            properties = {}
            if "properties" in entry:
                for prop_name, prop_value in entry["properties"].items():
                    prop_type = prop_value.get("type", "")
                    if prop_type in ["select", "status"]:
                        value = prop_value.get(prop_type, {}).get("name", "")
                        if value:
                            properties[prop_name] = value
                    elif prop_type == "number":
                        value = prop_value.get("number")
                        if value is not None:
                            properties[prop_name] = value
                    elif prop_type == "checkbox":
                        properties[prop_name] = prop_value.get("checkbox", False)
                    elif prop_type == "url":
                        value = prop_value.get("url")
                        if value:
                            properties[prop_name] = value

            formatted_results.append(
                {"id": entry_id, "title": title, "properties": properties}
            )

        result = DatabaseQueryResult(
            results=formatted_results,
            has_more=has_more,
            next_cursor=next_cursor,
            count=len(formatted_results),
        )

        return ToolResponse(is_success=True, result=result)
    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
    except Exception as e:
        return ToolResponse(
            is_success=False, result=None, error=f"Error querying database: {str(e)}"
        )
