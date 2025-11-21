# Crawl4AI Refactoring - Modular Agentic Architecture

## Overview

This refactoring transforms the crawl4ai tools from a monolithic design into a modular, agentic architecture inspired by Cole's approach. The key principle is **separation of concerns**: tools are atomic and composable, while agents orchestrate workflows.

## Key Changes

### 1. Helper Functions Module (`_helpers.py`)

Created a dedicated helper module with deterministic utility functions that can be used by tools, agents, and other code:

- **`detect_url_type(url)`** - Detects if URL is sitemap, txt, markdown, or regular webpage
- **`parse_sitemap(url)`** - Parses XML sitemap and extracts all URLs
- **`smart_chunk_markdown(markdown, ...)`** - Intelligently chunks markdown preserving structure
- **`extract_code_blocks(markdown)`** - Extracts code blocks from markdown
- **`extract_section_info(markdown, section_title)`** - Extracts specific section from markdown
- **`normalize_url(url)`** - Normalizes URLs by removing fragments

These helpers are **NOT MCP tools** - they're pure functions that can be imported and used anywhere.

### 2. Enhanced `crawl_website` Tool

The `crawl_website` tool now:
- **Automatically detects URL type** (sitemap, txt, markdown, webpage)
- **Handles sitemaps** - Returns list of URLs from sitemap XML
- **Returns `url_type`** in the result for agents to make decisions

**Before:** Tool only handled regular webpages  
**After:** Tool intelligently handles multiple URL types

### 3. New `chunk_markdown` Tool

A dedicated tool for chunking markdown content:
- Preserves section boundaries (headers)
- Keeps code blocks intact
- Maintains paragraph/list structure
- Configurable chunk size and overlap

**Why separate?** Agents can now:
1. Crawl a page → get markdown
2. Chunk the markdown → get structured chunks
3. Store chunks individually → better retrieval

### 4. New `get_available_sources` Tool

Helps agents discover what data has been scraped:
- Lists all URLs that have been stored
- Shows domains, titles, content lengths
- Enables agents to make informed decisions about what to crawl

**Use case:** Agent can check if a URL was already scraped before crawling.

### 5. New `perform_rag_query` Tool

A complete RAG workflow tool with optional reranking:
- Searches documents using text search
- Optionally reranks using CrossEncoder model
- Returns top results for LLM context

**Features:**
- Automatic reranking if `USE_RERANKING=true` env var is set
- Configurable reranking model (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- Returns relevance scores

## Architecture Pattern

### Before (Monolithic)
```
crawl_single_page(url)
  ├── Crawl page
  ├── Chunk markdown
  └── Store to Supabase
```

### After (Modular)
```
Agent orchestrates:
  1. crawl_website(url) → get markdown
  2. chunk_markdown(markdown) → get chunks
  3. For each chunk:
     add_document(chunk) → store to Supabase
```

**Benefits:**
- Each tool is atomic and testable
- Agents can compose workflows flexibly
- Tools can be reused in different contexts
- Better error handling at each step

## Usage Examples

### Example 1: Basic Crawl and Store Workflow

```python
# Agent workflow
result = await crawl_website(url="https://example.com")
if result.is_success:
    markdown = result.result['content_markdown']
    
    # Chunk the content
    chunks_result = await chunk_markdown(markdown=markdown)
    if chunks_result.is_success:
        chunks = chunks_result.result['chunks']
        
        # Store each chunk
        for chunk in chunks:
            await add_document(
                url=result.result['url'],
                title=result.result['title'],
                content=chunk['content'],
                description=result.result['description']
            )
```

### Example 2: Sitemap Handling

```python
# Agent detects sitemap and handles it
result = await crawl_website(url="https://example.com/sitemap.xml")
if result.is_success and result.result['url_type'] == 'sitemap':
    urls = result.result['sitemap_urls']
    
    # Agent decides to crawl first 10 URLs
    for url in urls[:10]:
        page_result = await crawl_website(url=url)
        # Process and store...
```

### Example 3: RAG Query with Reranking

```python
# Agent performs RAG query
rag_result = await perform_rag_query(
    query="Python async programming",
    limit=10,
    use_reranking=True
)

if rag_result.is_success:
    top_results = rag_result.result['results']
    # Use top_results as context for LLM generation
```

### Example 4: Check Available Sources

```python
# Agent checks what's already been scraped
sources = await get_available_sources(domain_filter="example.com")

if sources.is_success:
    available_urls = [s['url'] for s in sources.result['sources']]
    # Agent can skip already-scraped URLs
```

## Environment Variables

### Reranking (Optional)

```bash
# Enable reranking
USE_RERANKING=true

# Optional: specify custom model
RERANKING_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

**Note:** Reranking requires `sentence-transformers` package:
```bash
pip install sentence-transformers
```

## Tool Registration

All new tools are registered in `src/mcp_ce/runtime.py`:

- `crawl4ai`: `chunk_markdown`
- `supabase`: `get_available_sources`, `perform_rag_query`

## Design Principles

1. **Atomic Tools** - Each tool does ONE thing well
2. **Composable** - Agents orchestrate multiple tools
3. **Deterministic Helpers** - Helper functions are pure and reusable
4. **Agentic Workflows** - Complex operations are agent-driven, not tool-driven
5. **Separation of Concerns** - Crawling, chunking, and storage are separate

## Migration Guide

### If you were using `crawl_single_page` pattern:

**Old:**
```python
# Monolithic function
result = crawl_single_page(url)  # Does everything
```

**New:**
```python
# Agent orchestrates
crawl_result = await crawl_website(url)
chunks_result = await chunk_markdown(crawl_result.result['content_markdown'])
for chunk in chunks_result.result['chunks']:
    await add_document(...)
```

### Benefits of New Approach:

1. **Flexibility** - Can chunk differently for different use cases
2. **Error Handling** - Can handle errors at each step
3. **Caching** - Can cache crawl results separately from chunks
4. **Testing** - Each tool can be tested independently
5. **Reusability** - Tools can be used in different workflows

## Next Steps

Consider creating agents that:
- Automatically chunk and store crawled content
- Handle sitemaps intelligently
- Use RAG queries for context-aware generation
- Check available sources before crawling

See `src/mcp_ce/agentic_tools/` for agent patterns.

