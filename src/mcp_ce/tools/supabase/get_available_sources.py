"""Get available sources (URLs) that have been scraped and stored."""

from typing import Optional, Dict, Any
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from ._client_helper import get_client


@register_command("supabase", "get_available_sources")
@cache_tool(ttl=300, id_param=None)  # Cache for 5 minutes
async def get_available_sources(
    table_name: str = "documents",
    limit: int = 100,
    domain_filter: Optional[str] = None,
    override_cache: bool = False,
) -> ToolResponse:
    """
    Get a list of available sources (URLs) that have been scraped and stored.

    This tool helps agents understand what data has been scraped in the past,
    enabling them to make informed decisions about what to crawl or query.

    Args:
        table_name: Name of the Supabase table (default: "documents")
        limit: Maximum number of sources to return (default: 100, max: 500)
        domain_filter: Optional domain to filter by (e.g., "example.com")
        override_cache: Whether to bypass cache and force fresh query (default: False)

    Returns:
        ToolResponse containing:
        - sources: List of source dictionaries with:
          - url: Source URL
          - title: Document title
          - description: Document description
          - created_at: When it was scraped
          - content_length: Length of content
        - total_count: Total number of sources
        - domains: List of unique domains found
    """
    try:
        client = get_client()

        # Limit the maximum results
        limit = min(limit, 500)

        # Build the query - select distinct URLs with metadata
        query_builder = client.table(table_name).select(
            "url, title, description, created_at, content"
        )

        # Apply domain filter if provided
        if domain_filter:
            query_builder = query_builder.ilike("url", f"%{domain_filter}%")

        # Order by most recent first
        query_builder = query_builder.order("created_at", desc=True).limit(limit)

        # Execute query
        response = query_builder.execute()

        # Get results
        results = response.data if response.data else []

        # Format results and extract unique domains
        sources = []
        domains = set()

        for doc_data in results:
            url = doc_data.get("url", "")
            if url:
                # Extract domain
                from urllib.parse import urlparse

                parsed = urlparse(url)
                if parsed.netloc:
                    domains.add(parsed.netloc)

                sources.append(
                    {
                        "url": url,
                        "title": doc_data.get("title", ""),
                        "description": doc_data.get("description", ""),
                        "created_at": doc_data.get("created_at", ""),
                        "content_length": len(doc_data.get("content", "")),
                    }
                )

        result = {
            "sources": sources,
            "total_count": len(sources),
            "domains": sorted(list(domains)),
        }

        return ToolResponse(
            is_success=True,
            result=result,
        )

    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Failed to get available sources: {str(e)}",
        )
