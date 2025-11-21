# Agent Architecture Refactor: Agents vs. Workflows

## Summary

Successfully separated **generic, reusable agents** from **specific workflow implementations**. This enables the same agents to be used across multiple workflows with different configurations.

## Architecture Changes

### Before: Monolithic

```
agents/event_extraction_graph/
└── agent.py (484 lines)
    ├── scraper_agent          # Event-specific
    ├── extraction_agent       # Event-specific
    ├── validation_agent       # Event-specific
    └── workflow_agent         # Event-specific
```

**Problems:**
- ❌ Agents hard-coded for events
- ❌ Can't reuse for other domains (products, articles, etc.)
- ❌ Must copy-paste code for new workflows
- ❌ Difficult to test in isolation

### After: Modular with Dependency Injection

```
agents/
├── base_agents/               # GENERIC, REUSABLE
│   ├── scraper_agent.py      # Any web scraping
│   ├── extraction_agent.py   # Any structured extraction
│   └── validation_agent.py   # Any validation
│
├── workflows/                 # SPECIFIC USE CASES
│   └── event_extraction_workflow.py  # Uses base agents for events
│
└── event_extraction_graph/   # DOMAIN LOGIC
    ├── models.py             # Event Pydantic models
    └── tools.py              # Event helper functions
```

**Benefits:**
- ✅ Agents are generic (work for events, products, articles, etc.)
- ✅ Workflows inject domain-specific logic
- ✅ Easy to create new workflows (reuse agents)
- ✅ Easy to test (mock dependencies)
- ✅ SOLID principles (dependency inversion)

## Key Concept: Dependency Injection

### Old Approach (Hard-Coded)

```python
# ❌ Agent knows about events
@agent.tool
async def scrape_url(ctx):
    result = await crawl_website(url)  # Hard-coded scraping
    return parse_for_events(result)    # Hard-coded parsing
```

### New Approach (Injected)

```python
# ✅ Agent accepts any function
@agent.tool
async def scrape_url(ctx):
    result = await ctx.deps.scrape_function(url)  # Injected!
    return result
```

**Workflow injects the implementation:**

```python
# For events
deps = ScraperDeps(url=url, scrape_function=crawl_website)

# For different use case
deps = ScraperDeps(url=url, scrape_function=playwright_scraper)
```

## Files Created

### Base Agents (Generic)

1. **`base_agents/scraper_agent.py`** (110 lines)
   - Generic web scraping agent
   - Accepts any scraping function via injection
   - Returns `ScrapedContent` model

2. **`base_agents/extraction_agent.py`** (150 lines)
   - Generic structured data extraction
   - Accepts any Pydantic schema
   - Accepts pattern finder function via injection
   - Returns `ExtractionResult` model

3. **`base_agents/validation_agent.py`** (140 lines)
   - Generic validation and quality checking
   - Accepts completeness checker via injection
   - Accepts quality checker via injection
   - Returns `ValidationResult` model

4. **`base_agents/__init__.py`**
   - Exports all base agents and their types

### Workflows (Specific)

5. **`workflows/event_extraction_workflow.py`** (280 lines)
   - Configures base agents for event extraction
   - Injects event-specific functions
   - Orchestrates the workflow

6. **`workflows/__init__.py`**
   - Exports workflow entry point

### Documentation

7. **`ARCHITECTURE.md`** (Comprehensive guide)
   - Architecture principles
   - Dependency injection pattern
   - Examples of creating new workflows
   - Testing strategies
   - Migration guide

8. **`AGENTS_VS_WORKFLOWS.md`** (This file)
   - Quick reference
   - Before/after comparison
   - Key changes

## Usage Examples

### Using Base Agents Directly

```python
from mcp_ce.agents.base_agents import scraper_agent, ScraperDeps

# Configure for specific use case
deps = ScraperDeps(
    url="https://example.com",
    scrape_function=my_custom_scraper,
)

result = await scraper_agent.run("Scrape content", deps=deps)
```

### Using Event Workflow

```python
from mcp_ce.agents.workflows import extract_events_from_url

# High-level API (uses base agents internally)
result = await extract_events_from_url(
    url="https://seattlebluesdance.com/",
    max_iterations=2,
)
```

### Creating New Workflow

```python
# workflows/product_extraction_workflow.py

from ..base_agents import extraction_agent, ExtractionDeps

# Define product-specific helpers
async def find_product_patterns(content):
    return {"prices": [...], "names": [...]}

# Configure generic extraction agent for products
deps = ExtractionDeps(
    content=content,
    extraction_schema=ProductDetails,        # Product model
    pattern_finder=find_product_patterns,    # Product patterns
)

# Reuse same agent with different configuration!
result = await extraction_agent.run("Extract products", deps=deps)
```

## Dependency Injection Points

### Scraper Agent
- `scrape_function`: Function to scrape URLs
- `additional_params`: Extra parameters for scraper

### Extraction Agent
- `extraction_schema`: Pydantic model to extract
- `pattern_finder`: Function to find patterns in content
- `previous_items`: Items from previous iteration
- `feedback`: Feedback for improvement
- `context`: Additional context data

### Validation Agent
- `completeness_checker`: Function to check completeness
- `quality_checker`: Function to check quality
- `context`: Additional context data

## Testing Benefits

### Test Agents in Isolation

```python
# Mock dependencies
async def mock_scraper(url, **kwargs):
    return MockResult(markdown="test content")

# Test agent with mock
deps = ScraperDeps(url="test.com", scrape_function=mock_scraper)
result = await scraper_agent.run("Scrape", deps=deps)

assert result.output.success == True
```

### Test Workflows with Mocks

```python
# Mock all dependencies
deps = EventExtractionWorkflowDeps(
    url="test.com",
    scrape_function=mock_scraper,
    pattern_finder=mock_patterns,
    completeness_checker=mock_checker,
)

result = await workflow.run("Extract", deps=deps)
```

## Reusability Example

**Same 3 base agents, multiple workflows:**

```
Scraper Agent    →  Event Workflow
                 →  Product Workflow
                 →  Article Workflow

Extraction Agent →  Event Workflow
                 →  Product Workflow
                 →  Article Workflow

Validation Agent →  Event Workflow
                 →  Product Workflow
                 →  Article Workflow
```

**No code duplication!** Just different configurations.

## Key Design Principles

1. **Separation of Concerns**
   - Agents: Generic coordination logic
   - Workflows: Domain-specific orchestration
   - Tools: Domain-specific helpers

2. **Dependency Inversion**
   - High-level agents don't depend on low-level implementations
   - Both depend on abstractions (function signatures)

3. **Open/Closed Principle**
   - Agents open for extension (via injection)
   - Agents closed for modification (don't edit agent code)

4. **Single Responsibility**
   - Each agent has one job
   - Workflows compose agents

5. **Interface Segregation**
   - Small, focused dependencies
   - Only inject what's needed

## Migration Path

### For Existing Code

**Old import:**
```python
from src.mcp_ce.agents.event_extraction_graph import extract_events_from_url
```

**New import:**
```python
from src.mcp_ce.agents.workflows import extract_events_from_url
```

**API stays the same!**

### For New Workflows

1. Import base agents
2. Define domain-specific helpers
3. Create workflow function
4. Inject helpers into base agents
5. Orchestrate with workflow agent

## Summary

✅ **Agents are generic** - Work for any domain  
✅ **Workflows are specific** - Configure agents for use cases  
✅ **Dependency injection** - Maximum flexibility  
✅ **Highly reusable** - One codebase, many workflows  
✅ **Easy to test** - Mock any dependency  
✅ **SOLID principles** - Clean, maintainable architecture  

**Result: 3 generic agents can power unlimited workflows!**
