# Test Suite Documentation

This directory contains the test suite for the MCP Discord Server project.

## Structure

The test structure mirrors the source code structure:

```
test/
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_registry_enforcement.py  # Registry decorator tests (10 tests)
├── mcp_ce/
│   └── tools/
│       ├── notion/             # Notion tool tests (8 test files)
│       │   ├── test_search_notion.py
│       │   ├── test_get_page.py
│       │   ├── test_create_page.py
│       │   ├── test_update_page.py
│       │   ├── test_query_database.py
│       │   ├── test_add_comment.py
│       │   ├── test_database_integration.py
│       │   └── test_registry_integration.py  # Notion registry tests
│       ├── discord/            # Discord tool tests (coming soon)
│       ├── youtube/            # YouTube tool tests (coming soon)
│       └── ...
└── test_data/                  # Test data files (optional)
```

## Running Tests

### Quick Start

Run all tests:
```bash
pytest
```

Run tests for a specific server:
```bash
# Using pytest directly
pytest tests/mcp_ce/tools/notion/ -v

# Using test runner script
python run_tests.py notion
```

Run specific test file:
```bash
pytest tests/mcp_ce/tools/notion/test_search_notion.py -v
```

### Test Runner Script

The `run_tests.py` script provides convenient shortcuts:

```bash
# Run all Notion tests
python run_tests.py notion

# Run all Discord tests
python run_tests.py discord

# Run all tests
python run_tests.py all

# Run with coverage report
python run_tests.py notion --coverage

# List available test servers
python run_tests.py list
```

### Using Markers

Tests are categorized with markers for flexible filtering:

```bash
# Run only integration tests
pytest -m integration

# Run only unit tests (fast, no external dependencies)
pytest -m unit

# Run only Notion tests
pytest -m notion

# Run slow tests
pytest -m slow

# Exclude slow tests
pytest -m "not slow"
```

## Configuration

### Environment Variables

Tests require environment variables for API access. Create a `.env` file:

```env
# Required for Notion tests
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here
TEST_NOTION_PAGE_ID=a_test_page_id_here

# Required for YouTube tests
YOUTUBE_API_KEY=your_youtube_api_key_here

# Required for Discord tests
DISCORD_TOKEN=your_discord_token_here
```

If environment variables are not configured, tests will be automatically skipped.

### pytest.ini

The `pytest.ini` file in the project root configures:
- Test discovery patterns
- Output formatting
- Test markers
- Async support

## Writing Tests

### Test Structure

Each test should:
1. Use appropriate pytest markers (`@pytest.mark.notion`, `@pytest.mark.integration`, etc.)
2. Be async if testing async tools (`@pytest.mark.asyncio`)
3. Use fixtures for API credentials
4. Use `pytest.assert_tool_response()` for ToolResponse validation

### Example Test

```python
"""Tests for my_tool."""

import pytest
from mcp_ce.tools.server.my_tool import my_tool


@pytest.mark.server_name
@pytest.mark.integration
@pytest.mark.asyncio
async def test_my_tool_success(api_token):
    """Test my_tool with valid input."""
    result = await my_tool(param="value")
    
    # Use helper to verify ToolResponse structure
    pytest.assert_tool_response(result, expected_success=True)
    
    # Check specific result data
    assert "expected_key" in result.result


@pytest.mark.server_name
@pytest.mark.integration
@pytest.mark.asyncio
async def test_my_tool_error(api_token):
    """Test my_tool with invalid input."""
    result = await my_tool(param="invalid")
    
    pytest.assert_tool_response(result, expected_success=False)
    assert "error" in result.error.lower()
```

### Available Fixtures

Defined in `conftest.py`:

- `notion_token` - Notion API token (auto-skips if not configured)
- `notion_database_id` - Notion database ID for testing
- `sample_notion_page_id` - Sample page ID for read/write tests
- `youtube_api_key` - YouTube API key
- `discord_token` - Discord bot token
- `test_data_dir` - Path to test data directory

### Utility Functions

- `pytest.assert_tool_response(response, expected_success=True)` - Validates ToolResponse structure

## Test Coverage

Created 8 comprehensive test files with 43+ test cases:

**Registry Tests:**

1. **test_registry_enforcement.py** (10 tests) 🆕
   - ToolResponse enforcement for async/sync tools
   - Error handling for invalid return types
   - Registry metadata preservation
   - Multiple servers/tools per server

**Notion Tool Tests:**

2. **test_search_notion.py** (5 tests)
   - Search pages, databases, all
   - Empty results
   - Cache verification

3. **test_get_page.py** (4 tests)
   - Get existing page
   - Invalid page error
   - Cache verification
   - Properties structure

4. **test_create_page.py** (4 tests)
   - Create at workspace root
   - Create without content
   - Invalid parent error
   - Multiline content

5. **test_update_page.py** (5 tests)
   - Update with dict
   - Update with JSON string
   - Invalid JSON error
   - Invalid page error
   - Multiple properties

6. **test_query_database.py** (5 tests)
   - Query without filter
   - Query with filter
   - Invalid database error
   - Cache verification
   - Invalid filter handling

7. **test_add_comment.py** (5 tests)
   - Add comment
   - Comment with emoji
   - Invalid page error
   - Empty comment
   - Long comment

8. **test_database_integration.py** (6 tests)
   - Real-world database query with data_source_id
   - Property structure validation
   - Finding pages by URL
   - Duplicate URL detection
   - Lock status checking
   - Full database validation

9. **test_registry_integration.py** (11 tests) 🆕
   - Notion tools registration verification
   - ToolResponse return type enforcement
   - Error handling with ToolResponse
   - Function metadata preservation

Tests that require:
- API keys/tokens
- Network access
- External services

Mark with: `@pytest.mark.integration`

### Unit Tests

Tests that:
- Run entirely offline
- Use mocks/fixtures
- Are very fast (<1s)

Mark with: `@pytest.mark.unit`

### Slow Tests

Tests that take >5 seconds.

Mark with: `@pytest.mark.slow`

## Coverage

Generate coverage report:

```bash
# HTML report (creates htmlcov/ directory)
pytest --cov=src --cov-report=html

# Terminal report
pytest --cov=src --cov-report=term

# Using test runner
python run_tests.py notion --coverage
```

View HTML coverage:
```bash
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows
```

## Best Practices

1. **One test file per tool** - `test_tool_name.py` for each `tool_name.py`
2. **Descriptive test names** - `test_search_pages_with_filter()` not `test_1()`
3. **Test both success and failure** - Include error cases
4. **Use fixtures** - Don't hardcode credentials
5. **Mark appropriately** - Use markers for categorization
6. **Keep tests isolated** - Each test should work independently
7. **Clean up after tests** - Delete test pages/data if created
8. **Document test intent** - Use docstrings to explain what's being tested

## Continuous Integration

Tests can be integrated with CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest tests/mcp_ce/tools/notion/ -v
  env:
    NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
    NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
```

## Troubleshooting

### Tests are skipped

**Cause:** Missing environment variables

**Solution:** Configure required variables in `.env`

### Import errors

**Cause:** Python path not configured

**Solution:** Run from project root, or `conftest.py` handles this automatically

### Cache interference

**Cause:** Cached results from previous test runs

**Solution:** Clear cache: `rm -rf .cache/`

### Async warnings

**Cause:** Async tests without `@pytest.mark.asyncio`

**Solution:** Add `@pytest.mark.asyncio` decorator

## Adding Tests for New Servers

1. Create directory: `tests/mcp_ce/tools/your_server/`
2. Add `__init__.py` 
3. Create test files: `test_tool_name.py`
4. Add fixtures to `conftest.py` if needed
5. Update markers in `pytest.ini`
6. Run: `python run_tests.py your_server`

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest markers](https://docs.pytest.org/en/stable/mark.html)
