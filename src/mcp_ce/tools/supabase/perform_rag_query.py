"""Perform RAG (Retrieval-Augmented Generation) query with reranking."""

import os
from typing import Optional, List, Dict, Any
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from ._client_helper import get_client


# Try to import CrossEncoder for reranking (optional)
try:
    from sentence_transformers import CrossEncoder
    RERANKING_AVAILABLE = True
except ImportError:
    RERANKING_AVAILABLE = False
    CrossEncoder = None


def _get_reranking_model():
    """Get or initialize the reranking model."""
    if not RERANKING_AVAILABLE:
        return None
    
    # Check if reranking is enabled
    if os.getenv("USE_RERANKING", "false").lower() != "true":
        return None
    
    # Lazy load the model
    if not hasattr(_get_reranking_model, '_model'):
        try:
            model_name = os.getenv("RERANKING_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
            _get_reranking_model._model = CrossEncoder(model_name)
        except Exception as e:
            print(f"Failed to load reranking model: {e}")
            _get_reranking_model._model = None
    
    return getattr(_get_reranking_model, '_model', None)


def _rerank_results(
    model: Any,
    query: str,
    results: List[Dict[str, Any]],
    content_key: str = "content",
    top_k: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Rerank search results using a cross-encoder model.
    
    Args:
        model: The CrossEncoder model
        query: The search query
        results: List of search results
        content_key: The key in each result dict that contains the content
        top_k: Number of top results to return (None = all)
        
    Returns:
        Reranked list of results
    """
    if not model or not results:
        return results
    
    try:
        # Prepare pairs for reranking
        pairs = [
            [query, result.get(content_key, result.get("description", ""))]
            for result in results
        ]
        
        # Get scores
        scores = model.predict(pairs)
        
        # Add scores to results and sort
        for i, result in enumerate(results):
            result['_rerank_score'] = float(scores[i])
        
        # Sort by score (descending)
        reranked = sorted(results, key=lambda x: x.get('_rerank_score', 0), reverse=True)
        
        # Return top_k if specified
        if top_k:
            return reranked[:top_k]
        
        return reranked
    
    except Exception as e:
        print(f"Reranking error: {e}")
        return results  # Return original results on error


@register_command("supabase", "perform_rag_query")
@cache_tool(ttl=180, id_param="query")  # Cache for 3 minutes
async def perform_rag_query(
    query: str,
    table_name: str = "documents",
    limit: int = 20,
    use_reranking: Optional[bool] = None,
    rerank_top_k: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    override_cache: bool = False,
) -> ToolResponse:
    """
    Perform a RAG (Retrieval-Augmented Generation) query with optional reranking.
    
    This is an agentic workflow tool that:
    1. Searches documents using text search
    2. Optionally reranks results using a cross-encoder model
    3. Returns top results for use in generation
    
    This tool is designed to be used by agents that need to:
    - Find relevant context for answering questions
    - Retrieve information from scraped content
    - Build context windows for LLM generation
    
    Args:
        query: The search query
        table_name: Name of the Supabase table (default: "documents")
        limit: Maximum number of results to retrieve before reranking (default: 20)
        use_reranking: Whether to use reranking (default: auto-detect from USE_RERANKING env)
        rerank_top_k: Number of top results to return after reranking (default: 10, None = all)
        filters: Optional dictionary of filters (e.g., {"author": "John Doe"})
        override_cache: Whether to bypass cache and force fresh query (default: False)
        
    Returns:
        ToolResponse containing:
        - results: List of reranked results with:
          - url: Source URL
          - title: Document title
          - content: Document content (or excerpt)
          - description: Document description
          - rerank_score: Reranking score (if reranking used)
        - total_found: Total number of results found
        - reranking_used: Whether reranking was applied
    """
    try:
        client = get_client()
        
        # Determine if reranking should be used
        if use_reranking is None:
            use_reranking = os.getenv("USE_RERANKING", "false").lower() == "true"
        
        # Get reranking model if needed
        reranking_model = None
        if use_reranking:
            reranking_model = _get_reranking_model()
            if not reranking_model:
                use_reranking = False  # Fallback if model not available
        
        # Retrieve more results if reranking (we'll rerank and filter)
        search_limit = limit * 2 if use_reranking else limit
        search_limit = min(search_limit, 100)  # Cap at 100
        
        # Build the query
        query_builder = client.table(table_name).select("*")
        
        # Apply text search
        if query:
            search_pattern = f"%{query}%"
            query_builder = query_builder.or_(
                f"title.ilike.{search_pattern},content.ilike.{search_pattern},description.ilike.{search_pattern}"
            )
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple)):
                    query_builder = query_builder.in_(key, value)
                else:
                    query_builder = query_builder.eq(key, value)
        
        # Execute query
        query_builder = query_builder.limit(search_limit)
        response = query_builder.execute()
        
        # Get results
        raw_results = response.data if response.data else []
        
        # Format results
        formatted_results = []
        for doc_data in raw_results:
            content = doc_data.get("content", "")
            # Truncate very long content for reranking efficiency
            content_for_rerank = content[:2000] if len(content) > 2000 else content
            
            formatted_results.append({
                "id": str(doc_data.get("id", "")),
                "url": doc_data.get("url", ""),
                "title": doc_data.get("title", ""),
                "content": content,  # Full content
                "content_excerpt": content[:500] + "..." if len(content) > 500 else content,
                "description": doc_data.get("description", ""),
                "author": doc_data.get("author", ""),
                "published_date": doc_data.get("published_date", ""),
                "keywords": doc_data.get("keywords", []),
                "metadata": doc_data.get("metadata", {}),
                "created_at": doc_data.get("created_at", ""),
            })
        
        # Apply reranking if enabled
        if use_reranking and reranking_model and formatted_results:
            formatted_results = _rerank_results(
                model=reranking_model,
                query=query,
                results=formatted_results,
                content_key="content_excerpt",  # Use excerpt for reranking
                top_k=rerank_top_k or 10
            )
        
        # Limit final results
        final_results = formatted_results[:limit]
        
        result = {
            "results": final_results,
            "total_found": len(raw_results),
            "returned": len(final_results),
            "reranking_used": use_reranking and reranking_model is not None,
        }
        
        return ToolResponse(
            is_success=True,
            result=result,
        )
        
    except RuntimeError as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=str(e)
        )
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Failed to perform RAG query: {str(e)}"
        )

