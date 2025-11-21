"""Extract code blocks from markdown content (deterministic tool)."""

from typing import List, Dict, Any
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from ._helpers import extract_code_blocks


@register_command("crawl4ai", "extract_code_blocks")
async def extract_code_blocks_tool(
    markdown: str,
) -> ToolResponse:
    """
    Extract all code blocks from markdown content.
    
    This is a DETERMINISTIC tool that uses regex to find code blocks.
    It does NOT use AI - it's a pure parsing function.
    
    For AI-powered code analysis or summarization, use an agent that:
    1. Calls this tool to extract code blocks
    2. Uses an AI agent to analyze/summarize the code
    
    Args:
        markdown: The markdown content to extract code blocks from
        
    Returns:
        ToolResponse containing:
        - code_blocks: List of code block dictionaries with:
          - code: The code content
          - language: Programming language (if specified, else 'unknown')
          - start_pos: Starting position in original markdown
          - end_pos: Ending position in original markdown
        - total_blocks: Number of code blocks found
    """
    try:
        if not markdown:
            return ToolResponse(
                is_success=False,
                result=None,
                error="Markdown content is required"
            )
        
        blocks = extract_code_blocks(markdown)
        
        result = {
            'code_blocks': blocks,
            'total_blocks': len(blocks),
        }
        
        return ToolResponse(
            is_success=True,
            result=result,
        )
        
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Failed to extract code blocks: {str(e)}"
        )

