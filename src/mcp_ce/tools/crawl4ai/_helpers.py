"""
Helper functions for crawl4ai tools.

These are utility functions that can be used by tools, agents, and other code.
They are NOT MCP tools themselves, but support deterministic processing.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, urldefrag
from xml.etree import ElementTree
import requests


def detect_url_type(url: str) -> str:
    """
    Detect the type of URL (sitemap, txt file, markdown, or regular webpage).
    
    Args:
        url: The URL to analyze
        
    Returns:
        One of: 'sitemap', 'txt', 'markdown', 'webpage'
    """
    url_lower = url.lower()
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Check for sitemap indicators
    if 'sitemap' in path or 'sitemap' in url_lower:
        return 'sitemap'
    
    # Check file extensions
    if path.endswith('.xml'):
        # Could be sitemap or regular XML
        if 'sitemap' in url_lower:
            return 'sitemap'
        return 'webpage'  # Treat as regular page
    
    if path.endswith(('.txt', '.text')):
        return 'txt'
    
    if path.endswith(('.md', '.markdown')):
        return 'markdown'
    
    # Default to webpage
    return 'webpage'


def parse_sitemap(url: str) -> List[str]:
    """
    Parse a sitemap XML file and extract all URLs.
    
    Args:
        url: URL of the sitemap XML file
        
    Returns:
        List of URLs found in the sitemap
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        root = ElementTree.fromstring(response.content)
        
        # Handle sitemap index (contains other sitemaps)
        sitemap_index_urls = []
        for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
            loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc is not None and loc.text:
                sitemap_index_urls.append(loc.text)
        
        if sitemap_index_urls:
            # Recursively parse nested sitemaps
            all_urls = []
            for sitemap_url in sitemap_index_urls:
                all_urls.extend(parse_sitemap(sitemap_url))
            return all_urls
        
        # Handle regular sitemap (contains URLs)
        urls = []
        for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc is not None and loc.text:
                urls.append(loc.text)
        
        return urls
    
    except Exception as e:
        print(f"Error parsing sitemap {url}: {e}")
        return []


def smart_chunk_markdown(
    markdown: str,
    max_chunk_size: int = 2000,
    overlap: int = 200,
    preserve_sections: bool = True,
) -> List[Dict[str, Any]]:
    """
    Intelligently chunk markdown content preserving structure.
    
    This function chunks markdown while trying to preserve:
    - Section boundaries (headers)
    - Code blocks (kept intact)
    - Lists (kept together when possible)
    - Paragraphs (kept together)
    
    Args:
        markdown: The markdown content to chunk
        max_chunk_size: Maximum characters per chunk (default: 2000)
        overlap: Number of characters to overlap between chunks (default: 200)
        preserve_sections: Whether to try to preserve section boundaries (default: True)
        
    Returns:
        List of chunk dictionaries with:
        - content: The chunk text
        - start_pos: Starting position in original markdown
        - end_pos: Ending position in original markdown
        - section_title: Title of the section (if available)
    """
    if not markdown:
        return []
    
    chunks = []
    current_pos = 0
    markdown_len = len(markdown)
    
    # Split by headers if preserving sections
    if preserve_sections:
        # Find all header positions
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        headers = []
        for match in header_pattern.finditer(markdown):
            level = len(match.group(1))
            title = match.group(2).strip()
            pos = match.start()
            headers.append((pos, level, title))
        
        # If we have headers, chunk by sections
        if headers:
            for i, (header_pos, level, title) in enumerate(headers):
                # Determine section end
                if i + 1 < len(headers):
                    section_end = headers[i + 1][0]
                else:
                    section_end = markdown_len
                
                section_content = markdown[header_pos:section_end]
                
                # If section is small enough, keep as one chunk
                if len(section_content) <= max_chunk_size:
                    chunks.append({
                        'content': section_content,
                        'start_pos': header_pos,
                        'end_pos': section_end,
                        'section_title': title,
                    })
                else:
                    # Split large section into smaller chunks
                    section_chunks = _chunk_text(
                        section_content,
                        max_chunk_size,
                        overlap,
                        start_offset=header_pos
                    )
                    for chunk in section_chunks:
                        chunk['section_title'] = title
                    chunks.extend(section_chunks)
            
            return chunks
    
    # Fallback: chunk by paragraphs and code blocks
    return _chunk_text(markdown, max_chunk_size, overlap)


def _chunk_text(
    text: str,
    max_chunk_size: int,
    overlap: int,
    start_offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Helper to chunk text with overlap, preserving code blocks.
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum chunk size
        overlap: Overlap between chunks
        start_offset: Offset to add to positions (for tracking in original text)
        
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    current_pos = 0
    text_len = len(text)
    
    # Find code blocks to preserve them
    code_block_pattern = re.compile(r'```[\s\S]*?```', re.MULTILINE)
    code_blocks = []
    for match in code_block_pattern.finditer(text):
        code_blocks.append((match.start(), match.end()))
    
    while current_pos < text_len:
        # Determine chunk end
        chunk_end = min(current_pos + max_chunk_size, text_len)
        
        # If we're in the middle of a code block, extend to end of block
        for block_start, block_end in code_blocks:
            if current_pos < block_end <= chunk_end:
                chunk_end = block_end
                break
        
        # Extract chunk
        chunk_text = text[current_pos:chunk_end]
        
        # Try to end at a sentence or paragraph boundary
        if chunk_end < text_len:
            # Look for paragraph break
            para_break = chunk_text.rfind('\n\n')
            if para_break > max_chunk_size * 0.5:  # Only if we're not cutting too much
                chunk_text = chunk_text[:para_break]
                chunk_end = current_pos + para_break
            else:
                # Look for sentence end
                sentence_end = max(
                    chunk_text.rfind('. '),
                    chunk_text.rfind('.\n'),
                    chunk_text.rfind('! '),
                    chunk_text.rfind('?\n'),
                )
                if sentence_end > max_chunk_size * 0.5:
                    chunk_text = chunk_text[:sentence_end + 1]
                    chunk_end = current_pos + sentence_end + 1
        
        chunks.append({
            'content': chunk_text.strip(),
            'start_pos': current_pos + start_offset,
            'end_pos': chunk_end + start_offset,
            'section_title': None,
        })
        
        # Move to next position with overlap
        current_pos = chunk_end - overlap
        if current_pos <= chunks[-1]['start_pos'] - start_offset:
            current_pos = chunk_end  # Prevent infinite loop
    
    return chunks


def extract_code_blocks(markdown: str) -> List[Dict[str, Any]]:
    """
    Extract all code blocks from markdown content.
    
    Args:
        markdown: Markdown content to extract from
        
    Returns:
        List of code block dictionaries with:
        - code: The code content
        - language: Programming language (if specified)
        - start_pos: Starting position in markdown
        - end_pos: Ending position in markdown
    """
    code_blocks = []
    
    # Pattern for fenced code blocks
    pattern = re.compile(r'```(\w+)?\n([\s\S]*?)```', re.MULTILINE)
    
    for match in pattern.finditer(markdown):
        language = match.group(1) or 'unknown'
        code = match.group(2)
        
        code_blocks.append({
            'code': code,
            'language': language,
            'start_pos': match.start(),
            'end_pos': match.end(),
        })
    
    return code_blocks


def extract_section_info(markdown: str, section_title: str) -> Optional[Dict[str, Any]]:
    """
    Extract information about a specific section from markdown.
    
    Args:
        markdown: Markdown content
        section_title: Title of the section to extract
        
    Returns:
        Dictionary with:
        - title: Section title
        - content: Section content
        - start_pos: Starting position
        - end_pos: Ending position
        - subsections: List of subsections
        Or None if section not found
    """
    # Escape special regex characters in title
    escaped_title = re.escape(section_title)
    
    # Find section header
    pattern = re.compile(
        rf'^(#{1,6})\s+{escaped_title}\s*$',
        re.MULTILINE | re.IGNORECASE
    )
    
    match = pattern.search(markdown)
    if not match:
        return None
    
    header_level = len(match.group(1))
    section_start = match.start()
    
    # Find next header of same or higher level
    next_header_pattern = re.compile(
        rf'^(#{{1,{header_level}}})\s+',
        re.MULTILINE
    )
    
    # Search from after current header
    next_match = next_header_pattern.search(markdown, section_start + len(match.group(0)))
    
    if next_match:
        section_end = next_match.start()
    else:
        section_end = len(markdown)
    
    section_content = markdown[section_start:section_end].strip()
    
    # Extract subsections
    subsection_pattern = re.compile(
        rf'^(#{{{header_level + 1}}})\s+(.+)$',
        re.MULTILINE
    )
    subsections = []
    for sub_match in subsection_pattern.finditer(section_content):
        subsections.append({
            'title': sub_match.group(2).strip(),
            'start_pos': section_start + sub_match.start(),
        })
    
    return {
        'title': section_title,
        'content': section_content,
        'start_pos': section_start,
        'end_pos': section_end,
        'subsections': subsections,
    }


def normalize_url(url: str) -> str:
    """
    Normalize URL by removing fragment and trailing slash.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    url, _ = urldefrag(url)
    if url.endswith('/') and len(url) > 1:
        url = url[:-1]
    return url

