"""Chunk markdown content into smaller pieces for storage and retrieval."""

from typing import List, Dict, Any, Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from ._helpers import smart_chunk_markdown


@register_command("crawl4ai", "chunk_markdown")
async def chunk_markdown(
    markdown: str,
    max_chunk_size: int = 2000,
    overlap: int = 200,
    preserve_sections: bool = True,
) -> ToolResponse:
    """
    Intelligently chunk markdown content preserving structure.
    
    This tool splits markdown into smaller chunks while preserving:
    - Section boundaries (headers)
    - Code blocks (kept intact)
    - Lists and paragraphs (kept together when possible)
    
    This is useful for:
    - Preparing content for vector storage
    - Breaking large documents into searchable pieces
    - Maintaining context within chunks
    
    Args:
        markdown: The markdown content to chunk
        max_chunk_size: Maximum characters per chunk (default: 2000)
        overlap: Number of characters to overlap between chunks (default: 200)
        preserve_sections: Whether to try to preserve section boundaries (default: True)
        
    Returns:
        ToolResponse containing:
        - chunks: List of chunk dictionaries with:
          - content: The chunk text
          - start_pos: Starting position in original markdown
          - end_pos: Ending position in original markdown
          - section_title: Title of the section (if available)
        - total_chunks: Number of chunks created
        - original_length: Length of original markdown
    """
    try:
        if not markdown:
            return ToolResponse(
                is_success=False,
                result=None,
                error="Markdown content is required"
            )
        
        chunks = smart_chunk_markdown(
            markdown=markdown,
            max_chunk_size=max_chunk_size,
            overlap=overlap,
            preserve_sections=preserve_sections,
        )
        
        result = {
            'chunks': chunks,
            'total_chunks': len(chunks),
            'original_length': len(markdown),
        }
        
        return ToolResponse(
            is_success=True,
            result=result,
        )
        
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Failed to chunk markdown: {str(e)}"
        )

