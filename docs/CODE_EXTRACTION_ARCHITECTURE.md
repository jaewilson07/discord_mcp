# Code Extraction Architecture - Deterministic vs Agentic

## Overview

This document explains the code-specific extraction functionality with a clear separation between **deterministic tools** (no AI) and **agentic tools** (uses AI).

## Design Principle

**Deterministic tools** = Pure functions, no AI, predictable results  
**Agentic tools** = Use AI, should be agents, can have variable results

## Deterministic Tools (No AI)

### 1. `extract_code_blocks` (crawl4ai)

**Purpose:** Extract code blocks from markdown using regex  
**AI Required:** ❌ No  
**Deterministic:** ✅ Yes (pure regex parsing)

```python
# Extract code blocks from markdown
result = await extract_code_blocks(markdown="# Title\n```python\ndef hello():\n    pass\n```")
# Returns: List of code blocks with code, language, positions
```

**Use Cases:**
- Extract code from scraped documentation
- Parse code examples from markdown
- Find all code blocks in a document

### 2. `add_code_example` (supabase)

**Purpose:** Store code examples in Supabase  
**AI Required:** ❌ No  
**Deterministic:** ✅ Yes (pure database operation)

```python
# Store a code example
result = await add_code_example(
    source_url="https://example.com/docs",
    code="def hello(): pass",
    language="python",
    summary="",  # Can be empty, filled by agent later
    context="Introduction section"
)
```

**Use Cases:**
- Store extracted code examples
- Persist code snippets for later retrieval
- Build a code example database

### 3. `search_code_examples` (supabase)

**Purpose:** Search stored code examples  
**AI Required:** ❌ No  
**Deterministic:** ✅ Yes (pure database query)

```python
# Search code examples
result = await search_code_examples(
    query="async function",
    language="javascript",
    limit=10
)
```

**Use Cases:**
- Find code examples by keyword
- Filter by programming language
- Retrieve code snippets for RAG

## Agentic Tools (Uses AI)

### 1. `code_summarizer` (agents)

**Purpose:** Generate AI-powered summaries of code  
**AI Required:** ✅ Yes  
**Deterministic:** ❌ No (uses LLM)

```python
# Generate code summary using AI
result = await code_summarizer(
    code="def hello(name): return f'Hello {name}'",
    language="python",
    context="Introduction section"
)
# Returns: summary, purpose, key_concepts, complexity, confidence
```

**Use Cases:**
- Generate summaries for code examples
- Understand code snippets automatically
- Create code documentation

## Workflow Patterns

### Pattern 1: Extract and Store (Deterministic Only)

```python
# 1. Extract code blocks (deterministic)
extract_result = await extract_code_blocks(markdown=scraped_content)

# 2. Store each code block (deterministic)
for block in extract_result.result['code_blocks']:
    await add_code_example(
        source_url=source_url,
        code=block['code'],
        language=block['language'],
        context="Extracted from documentation"
    )
```

**When to use:** When you just need to extract and store code, no analysis needed.

### Pattern 2: Extract, Summarize, Store (Deterministic + Agentic)

```python
# 1. Extract code blocks (deterministic)
extract_result = await extract_code_blocks(markdown=scraped_content)

# 2. For each code block, generate summary (agentic)
for block in extract_result.result['code_blocks']:
    # Generate AI summary
    summary_result = await code_summarizer(
        code=block['code'],
        language=block['language'],
        context="Extracted from documentation"
    )
    
    # Store with summary (deterministic)
    await add_code_example(
        source_url=source_url,
        code=block['code'],
        language=block['language'],
        summary=summary_result.result['summary'],
        context="Extracted from documentation"
    )
```

**When to use:** When you want AI-generated summaries for better searchability.

### Pattern 3: Agent Orchestration

An agent can orchestrate these tools:

```python
# Agent workflow:
# 1. Crawl documentation
crawl_result = await crawl_website(url="https://docs.example.com")

# 2. Extract code blocks (deterministic)
code_blocks = await extract_code_blocks(markdown=crawl_result.result['content_markdown'])

# 3. For each code block:
for block in code_blocks.result['code_blocks']:
    # 3a. Generate summary (agentic)
    summary = await code_summarizer(
        code=block['code'],
        language=block['language']
    )
    
    # 3b. Store with summary (deterministic)
    await add_code_example(
        source_url=crawl_result.result['url'],
        code=block['code'],
        language=block['language'],
        summary=summary.result['summary']
    )
```

## Tool Classification Summary

| Tool | Server | AI Required | Type | Purpose |
|------|--------|-------------|------|---------|
| `extract_code_blocks` | crawl4ai | ❌ | Deterministic | Extract code from markdown |
| `add_code_example` | supabase | ❌ | Deterministic | Store code examples |
| `search_code_examples` | supabase | ❌ | Deterministic | Search code examples |
| `code_summarizer` | agents | ✅ | Agentic | Generate code summaries |

## Benefits of This Architecture

1. **Clear Separation:** Easy to understand what uses AI vs what doesn't
2. **Cost Control:** Deterministic tools are free, agentic tools cost money
3. **Performance:** Deterministic tools are fast, agentic tools are slower
4. **Composability:** Agents can orchestrate deterministic tools efficiently
5. **Testability:** Deterministic tools are easy to test, agentic tools need mocks

## Usage Guidelines

### When to Use Deterministic Tools

- ✅ Extracting code from markdown
- ✅ Storing code examples
- ✅ Searching stored code
- ✅ Batch processing code blocks
- ✅ When you need predictable results

### When to Use Agentic Tools

- ✅ Generating code summaries
- ✅ Understanding code purpose
- ✅ Analyzing code complexity
- ✅ When you need AI understanding
- ✅ Creating documentation

### Best Practices

1. **Extract first, then analyze:** Use deterministic extraction before AI analysis
2. **Cache summaries:** Store AI-generated summaries to avoid re-computation
3. **Batch processing:** Extract all code blocks deterministically, then summarize in batch
4. **Agent orchestration:** Let agents decide when to use AI vs deterministic tools

## Example: Complete Workflow

```python
# Agent orchestrates the workflow:

# Step 1: Crawl documentation (deterministic)
crawl = await crawl_website("https://docs.example.com/api")

# Step 2: Extract code blocks (deterministic)
blocks = await extract_code_blocks(crawl.result['content_markdown'])

# Step 3: For each code block
for block in blocks.result['code_blocks']:
    # Check if we already have this code (deterministic)
    existing = await search_code_examples(
        query=block['code'][:50],  # First 50 chars as fingerprint
        language=block['language']
    )
    
    if existing.result['count'] == 0:
        # Generate summary (agentic - costs money)
        summary = await code_summarizer(
            code=block['code'],
            language=block['language']
        )
        
        # Store with summary (deterministic)
        await add_code_example(
            source_url=crawl.result['url'],
            code=block['code'],
            language=block['language'],
            summary=summary.result['summary']
        )
```

This workflow:
- Uses deterministic tools for extraction and storage (fast, free)
- Uses agentic tools only when needed (AI summary)
- Avoids duplicate work (checks existing examples)
- Is cost-efficient (only calls AI when necessary)

