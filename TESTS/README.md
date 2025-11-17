# Tests

This directory contains integration and validation tests for the MCP Discord server.

## Running Tests

### Registry Test (Recommended for Development)

Test tool registration and discovery:

```bash
python TESTS\test_registry.py
```

This test:
- ✅ Verifies all tool modules import correctly
- ✅ Validates tool discovery and registration
- ✅ Checks expected server counts (Discord, Notion, YouTube, etc.)
- ✅ Prints comprehensive registry information

**Use this test frequently during development to verify:**
- New tools are properly registered with `@register_command`
- Tool counts match expectations after adding/removing tools
- Registry system is working correctly

### Other Tests

- `test_cache.py` - Cache system validation
- `test_complete_event_workflow.py` - End-to-end event workflow
- `test_deep_crawl.py` - Web crawling functionality
- `check_notion_db.py` - Notion database connectivity

## Test Requirements

Most tests can run without pytest. The registry test will automatically detect if pytest is installed and use it, or fall back to manual test execution.

To install pytest:
```bash
uv pip install pytest
```

## Writing New Tests

Tests should be self-contained and follow these patterns:

```python
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_something():
    """Test description."""
    from your_module import your_function
    result = your_function()
    assert result == expected_value

if __name__ == "__main__":
    test_something()
    print("✅ Test passed")
```
