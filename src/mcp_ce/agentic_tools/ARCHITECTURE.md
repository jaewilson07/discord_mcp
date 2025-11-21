# Agent Architecture: Separation of Agents and Workflows

## Overview

This architecture **separates generic, reusable agents from specific workflow implementations**. Agents are designed to be generic and configurable, while workflows compose these agents for specific use cases.

## Architecture Principles

### 1. **Agents Are Generic**
- Base agents can be used across multiple workflows
- Accept dependencies that inject workflow-specific logic
- No hard-coded domain logic
- Configured via dependency injection

### 2. **Workflows Are Specific**
- Compose base agents to solve specific problems
- Inject domain-specific functions into agents
- Coordinate agent interactions
- Define the execution graph

### 3. **Dependency Injection**
- Agents accept functions/data as dependencies
- Workflows provide implementations
- Enables testability and reusability

## Project Structure

```
src/mcp_ce/agents/
├── base_agents/                    # Generic, reusable agents
│   ├── __init__.py
│   ├── scraper_agent.py           # Generic web scraping
│   ├── extraction_agent.py        # Generic content extraction
│   └── validation_agent.py        # Generic validation
│
├── workflows/                      # Specific workflow implementations
│   ├── __init__.py
│   └── event_extraction_workflow.py  # Events workflow using base agents
│
└── event_extraction_graph/        # Domain-specific models & tools
    ├── __init__.py
    ├── models.py                  # Event-specific Pydantic models
    └── tools.py                   # Event-specific helper functions
```

## Base Agents

### Scraper Agent

**Purpose:** Generic web content scraping  
**Reusable for:** Any workflow needing web content

```python
from mcp_ce.agents.base_agents import scraper_agent, ScraperDeps

deps = ScraperDeps(
    url="https://example.com",
    scrape_function=my_scraping_function,  # Inject implementation
)

result = await scraper_agent.run("Scrape content", deps=deps)
```

**Key Features:**
- ✅ No hard-coded scraping logic
- ✅ Accepts any scraping function
- ✅ Works with any URL
- ✅ Returns standardized `ScrapedContent` model

### Extraction Agent

**Purpose:** Generic structured data extraction  
**Reusable for:** Events, products, articles, contacts, etc.

```python
from mcp_ce.agents.base_agents import extraction_agent, ExtractionDeps

deps = ExtractionDeps(
    content=scraped_text,
    extraction_schema=MyDataModel,  # What to extract
    pattern_finder=my_pattern_function,  # How to find patterns
)

result = await extraction_agent.run("Extract data", deps=deps)
```

**Key Features:**
- ✅ No domain-specific logic
- ✅ Accepts any Pydantic schema
- ✅ Optional pattern finder injection
- ✅ Generic tools (search patterns, get sections)

### Validation Agent

**Purpose:** Generic validation and quality checking  
**Reusable for:** Any extraction validation needs

```python
from mcp_ce.agents.base_agents import validation_agent, ValidationDeps

deps = ValidationDeps(
    content=original_content,
    extracted_items=extracted_data,
    iteration=1,
    max_iterations=3,
    completeness_checker=my_completeness_function,  # Inject logic
    quality_checker=my_quality_function,  # Inject logic
)

result = await validation_agent.run("Validate extraction", deps=deps)
```

**Key Features:**
- ✅ No domain-specific validation logic
- ✅ Accepts custom checkers via injection
- ✅ Iteration-aware
- ✅ Returns standardized `ValidationResult`

## Workflows

### Event Extraction Workflow

**Purpose:** Extract events from web pages  
**Uses:** All 3 base agents + event-specific logic

```python
from mcp_ce.agents.workflows import extract_events_from_url

result = await extract_events_from_url(
    url="https://seattlebluesdance.com/",
    max_iterations=2,
    confidence_threshold=0.85,
)
```

**How it works:**
1. **Configures scraper agent** with `crawl_website` function
2. **Configures extraction agent** with `EventDetails` schema and `find_event_patterns`
3. **Configures validation agent** with `check_event_completeness` and `check_event_quality`
4. **Orchestrates** the workflow with retry logic

### Creating New Workflows

To create a new workflow (e.g., product extraction):

```python
# workflows/product_extraction_workflow.py

from ..base_agents import scraper_agent, extraction_agent, validation_agent

async def find_product_patterns(content: str) -> dict:
    # Product-specific pattern finding
    return {"prices": [...], "names": [...]}

async def check_product_completeness(...):
    # Product-specific completeness check
    pass

# Configure base agents for products
scraper_deps = ScraperDeps(url=url, scrape_function=crawl_website)
extraction_deps = ExtractionDeps(
    content=content,
    extraction_schema=ProductDetails,  # Product model
    pattern_finder=find_product_patterns,  # Product patterns
)
validation_deps = ValidationDeps(
    extracted_items=products,
    completeness_checker=check_product_completeness,  # Product validation
)

# Use same base agents with different configuration!
```

## Dependency Injection Pattern

### Why Dependency Injection?

**Traditional Approach (Tight Coupling):**
```python
# ❌ Agent hard-codes specific implementation
@agent.tool
async def scrape_url(ctx):
    result = await crawl_website(url)  # Hard-coded!
    return result
```

**Dependency Injection (Loose Coupling):**
```python
# ✅ Agent accepts any scraping function
@agent.tool
async def scrape_url(ctx):
    result = await ctx.deps.scrape_function(url)  # Injected!
    return result
```

**Benefits:**
- ✅ Same agent works with different implementations
- ✅ Easy to test (inject mocks)
- ✅ Easy to extend (new implementations)
- ✅ No code duplication

### Injection Points

1. **Functions** - Business logic
   ```python
   scrape_function=crawl_website
   pattern_finder=find_event_patterns
   completeness_checker=check_event_completeness
   ```

2. **Schemas** - Data structures
   ```python
   extraction_schema=EventDetails
   ```

3. **Context** - Additional data
   ```python
   context={"url": url, "user_id": 123}
   ```

## Example: Multiple Workflows Using Same Agents

### Workflow 1: Event Extraction
```python
# Uses: scraper_agent + extraction_agent + validation_agent
# Configured for: Events (dates, times, venues)

extraction_deps = ExtractionDeps(
    extraction_schema=EventDetails,
    pattern_finder=find_event_patterns,  # Event-specific
)
```

### Workflow 2: Product Extraction (Future)
```python
# Uses: scraper_agent + extraction_agent + validation_agent
# Configured for: Products (prices, names, SKUs)

extraction_deps = ExtractionDeps(
    extraction_schema=ProductDetails,
    pattern_finder=find_product_patterns,  # Product-specific
)
```

### Workflow 3: Article Extraction (Future)
```python
# Uses: scraper_agent + extraction_agent + validation_agent
# Configured for: Articles (title, author, content)

extraction_deps = ExtractionDeps(
    extraction_schema=ArticleDetails,
    pattern_finder=find_article_patterns,  # Article-specific
)
```

**Same 3 base agents, 3 different workflows!**

## Testing Benefits

### Test Agents in Isolation
```python
# Test scraper agent with mock function
async def mock_scrape(url, **kwargs):
    return MockResult(markdown="test content")

deps = ScraperDeps(url="https://test.com", scrape_function=mock_scrape)
result = await scraper_agent.run("Scrape", deps=deps)
```

### Test Workflows with Mock Agents
```python
# Test workflow with mock dependencies
deps = EventExtractionWorkflowDeps(
    url="https://test.com",
    scrape_function=mock_scrape,
    pattern_finder=mock_patterns,
    completeness_checker=mock_completeness,
)
```

## Factory Functions

Create custom agent instances:

```python
from mcp_ce.agents.base_agents import create_extraction_agent

# Custom extraction agent for specific use case
my_agent = create_extraction_agent(
    model="openai:gpt-4o-mini",  # Different model
    system_prompt="Custom prompt for specific task",
    extraction_type="products",
)
```

## Migration from Old Architecture

### Old (Monolithic)
```
event_extraction_graph/
└── agent.py (484 lines)
    ├── scraper_agent
    ├── extraction_agent
    ├── validation_agent
    └── workflow_agent
    # All mixed together, hard to reuse
```

### New (Modular)
```
base_agents/
├── scraper_agent.py (generic)
├── extraction_agent.py (generic)
└── validation_agent.py (generic)

workflows/
└── event_extraction_workflow.py (uses base agents)

event_extraction_graph/
├── models.py (domain models)
└── tools.py (domain helpers)
```

## Key Differences

| Aspect | Old Architecture | New Architecture |
|--------|-----------------|------------------|
| **Agents** | Event-specific | Generic, reusable |
| **Workflows** | Mixed with agents | Separate files |
| **Injection** | Hard-coded logic | Dependency injection |
| **Reusability** | Copy-paste needed | Import and configure |
| **Testing** | Difficult to isolate | Easy to mock |
| **Extensibility** | Modify agent code | Create new workflow |

## Summary

✅ **Agents are generic** - No domain-specific logic  
✅ **Workflows are specific** - Compose agents for use cases  
✅ **Dependency injection** - Configure agents without modifying them  
✅ **Highly reusable** - Same agents for events, products, articles, etc.  
✅ **Easy to test** - Mock dependencies easily  
✅ **Clean separation** - Agents vs. workflows vs. domain logic  

**This architecture follows SOLID principles and enables rapid development of new workflows without duplicating agent code!**
