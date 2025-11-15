"""
Query a Notion database with optional filters and sorting.
"""

import os
import json
from typing import Dict, Any, Optional, Union, List
from notion_mcp import NotionMCPClient


async def query_notion_database(
    database_id: str,
    filter_json: Optional[Union[str, Dict[str, Any]]] = None,
    sorts_json: Optional[Union[str, List[Dict[str, str]]]] = None
) -> Dict[str, Any]:
    """
    Query a Notion database with optional filters and sorting.
    
    Args:
        database_id: The ID of the database to query
        filter_json: Filter criteria as JSON string or dict.
                    Example: {"property": "Status", "select": {"equals": "In Progress"}}
        sorts_json: Sort criteria as JSON string or list.
                   Example: [{"property": "Created", "direction": "descending"}]
    
    Returns:
        Dict containing:
        - success: bool indicating if query succeeded
        - results: list of database entries with id, title, and key properties
        - count: number of results found
        - error: error message if query failed
    """
    # Get Notion token from environment
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "error": "NOTION_TOKEN environment variable not set."
        }
    
    # Parse JSON parameters
    filter_obj = None
    sorts_obj = None
    
    try:
        if filter_json:
            filter_obj = json.loads(filter_json) if isinstance(filter_json, str) else filter_json
        if sorts_json:
            sorts_obj = json.loads(sorts_json) if isinstance(sorts_json, str) else sorts_json
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "error": f"Invalid JSON: {str(e)}"
        }
    
    try:
        async with NotionMCPClient(notion_token) as client:
            results = await client.query_database(
                database_id=database_id,
                filter_obj=filter_obj,
                sorts=sorts_obj
            )
            
            if not results:
                return {
                    "success": True,
                    "results": [],
                    "count": 0,
                    "error": None
                }
            
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
                
                formatted_results.append({
                    "id": entry_id,
                    "title": title,
                    "properties": properties
                })
            
            return {
                "success": True,
                "results": formatted_results,
                "count": len(formatted_results),
                "error": None
            }
    
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "error": f"Error querying database: {str(e)}"
        }


# Test code
if __name__ == "__main__":
    import asyncio
    import sys
    
    async def test():
        if len(sys.argv) > 1:
            result = await query_notion_database(sys.argv[1])
            
            print(f"Success: {result['success']}")
            print(f"Count: {result['count']}")
            for entry in result.get('results', []):
                print(f"  - {entry['title']} (ID: {entry['id']})")
                for prop, val in entry.get('properties', {}).items():
                    print(f"      {prop}: {val}")
            if result.get('error'):
                print(f"Error: {result['error']}")
        else:
            print("Usage: python query_database.py <database_id>")
    
    asyncio.run(test())
