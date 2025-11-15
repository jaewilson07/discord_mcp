"""
Search for pages and databases in Notion workspace.
"""

import os
from typing import Dict, Any, Optional, Literal
from notion_mcp import NotionMCPClient


async def search_notion(
    query: str,
    filter_type: Literal["page", "database", "all"] = "all"
) -> Dict[str, Any]:
    """
    Search for pages and databases in Notion workspace.
    
    Args:
        query: The search query to find pages/databases. Can be page title, 
               database name, or content keywords.
        filter_type: Filter results by type. Use 'page' for pages only, 
                    'database' for databases only, or 'all' for both.
    
    Returns:
        Dict containing:
        - success: bool indicating if search succeeded
        - results: list of matching pages/databases with id, title, type, url
        - count: number of results found
        - error: error message if search failed
    """
    # Get Notion token from environment
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "error": "NOTION_TOKEN environment variable not set. Please configure your Notion integration token."
        }
    
    try:
        async with NotionMCPClient(notion_token) as client:
            # Perform search
            results = await client.search_pages(
                query=query,
                filter_type=None if filter_type == "all" else filter_type,
            )
            
            if not results:
                return {
                    "success": True,
                    "results": [],
                    "count": 0,
                    "query": query
                }
            
            # Format results
            formatted_results = []
            for result in results:
                obj_type = result.get("object", "unknown")
                result_id = result.get("id", "unknown")
                
                # Extract title
                title = "Untitled"
                if "properties" in result:
                    props = result["properties"]
                    # Try different title property locations
                    if "title" in props:
                        title_obj = props["title"]
                        if "title" in title_obj and title_obj["title"]:
                            title = title_obj["title"][0]["text"]["content"]
                    elif "Name" in props:
                        name_obj = props["Name"]
                        if "title" in name_obj and name_obj["title"]:
                            title = name_obj["title"][0]["text"]["content"]
                
                formatted_results.append({
                    "id": result_id,
                    "title": title,
                    "type": obj_type,
                    "url": result.get("url", "")
                })
            
            return {
                "success": True,
                "results": formatted_results,
                "count": len(formatted_results),
                "query": query
            }
    
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "error": f"Error searching Notion: {str(e)}. Please check: 1) NOTION_TOKEN is valid, 2) Node.js 18+ is installed, 3) Integration has access to pages"
        }


# Test code
if __name__ == "__main__":
    import asyncio
    
    async def test():
        result = await search_notion("Getting started", filter_type="page")
        print(f"Success: {result['success']}")
        print(f"Count: {result['count']}")
        for item in result.get('results', []):
            print(f"  - {item['title']} ({item['type']}): {item['url']}")
        if result.get('error'):
            print(f"Error: {result['error']}")
    
    asyncio.run(test())
