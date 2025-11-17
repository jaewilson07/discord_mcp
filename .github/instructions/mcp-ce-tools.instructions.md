---
applyTo: "src/mcp_ce/tools/**/*.py"
---

# MCP CE Tool Development Instructions

These instructions apply when creating or modifying tools in the MCP CE (Code Execution) unified runtime system.

## Tool File Structure

Each tool must be implemented as an async function in its own file within `src/mcp_ce/tools/{server_name}/`.

### Required Pattern

#### handling server authentication
if the tool needs a client or auth, there should be a function get_client() or get_auth() that generates an instance of the client or auth inside the tool.

#### tool response
all tools should return an instance of ToolResponse or a subclass defined in the server's models.py file.


#### sample tool
```python
"""Single-line tool description."""

from typing import Dict, Any, Optional

async def tool_name(
    required_param: str,
    optional_param: Optional[int] = None
) -> Dict[str, Any]:
    """
    Comprehensive tool description.
    
    Args:
        required_param: Parameter description with type info
        optional_param: Optional parameter (default: None)
        
    Returns:
        Dictionary containing:
        - success (bool): Whether operation succeeded
        - data (Any): Result data if success=True
        - error (str): Error message if success=False
    """
    try:
        # Implementation here
        result = await perform_operation(required_param, optional_param)
        
        return {
            "success": True,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
```

## Three-Step Registration Process

**CRITICAL:** Every new tool requires updates in THREE locations in `src/mcp_ce/runtime.py`:

### Step 1: Add to _SERVERS_REGISTRY

Add tool name to the server's tools list:

```python
_SERVERS_REGISTRY = {
    "server_name": {
        "description": "Server description",
        "tools": [
            "existing_tool",
            "new_tool",  # ← Add here
        ],
    },
}
```

If creating a new server:

```python
_SERVERS_REGISTRY = {
    # ... existing servers ...
    "new_server": {
        "description": "New server description",
        "tools": ["new_tool"],
    },
}
```

### Step 2: Add Schema to query_tool_docs()

Add tool schema definition in the appropriate server block:

```python
def query_tool_docs(server: str, tool: Optional[str] = None, detail: str = "summary") -> str:
    # ... existing code ...
    
    if server == "server_name":
        schemas = {
            # ... existing tools ...
            "new_tool": {
                "name": "new_tool",
                "description": "Comprehensive tool description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "required_param": {
                            "type": "string",
                            "description": "Parameter description",
                        },
                        "optional_param": {
                            "type": "integer",
                            "description": "Optional parameter description",
                        },
                    },
                    "required": ["required_param"],
                },
            },
        }
```

**JSON Schema Types:**
- `"string"` - Text values
- `"integer"` - Whole numbers
- `"number"` - Decimals
- `"boolean"` - true/false
- `"array"` - Lists (add `"items": {...}`)
- `"object"` - Nested objects (add `"properties": {...}`)

### Step 3: Add Execution Handler to _execute_tool()

Add elif block with dynamic import:

```python
async def _execute_tool(server: str, tool: str, **kwargs) -> Dict[str, Any]:
    # ... existing elif blocks ...
    
    elif server == "server_name" and tool == "new_tool":
        from mcp_ce.tools.server_name.new_tool import new_tool
        return await new_tool(**kwargs)
    
    # ... rest of function ...
```

**IMPORTANT:** Always use dynamic imports inside the elif block to avoid circular dependencies.

## Validation Checklist

Before committing a new tool:

- [ ] Tool file created in correct location: `src/mcp_ce/tools/{server}/`
- [ ] Function is async and returns `Dict[str, Any]`
- [ ] Comprehensive docstring with Args/Returns sections
- [ ] Error handling with try/except
- [ ] Added to `_SERVERS_REGISTRY` tools list
- [ ] Schema added to `query_tool_docs()`
- [ ] Execution handler added to `_execute_tool()`
- [ ] File compiles: `python -m py_compile src/mcp_ce/tools/{server}/{tool}.py`
- [ ] Runtime compiles: `python -m py_compile src/mcp_ce/runtime.py`
- [ ] Tool appears in discovery: Run test script

### Test Script

```python
from src.mcp_ce.runtime import discovered_servers, query_tool_docs

# Check server appears
servers = discovered_servers()
print(f"Total servers: {len(servers)}")

# Check tool appears
docs = query_tool_docs("server_name", tool="new_tool")
print(docs)

# Test execution
from src.mcp_ce.runtime import _execute_tool
result = await _execute_tool("server_name", "new_tool", required_param="test")
print(result)
```

## Common Patterns

### Handling Optional Parameters

```python
async def tool(param: Optional[str] = None) -> Dict[str, Any]:
    if param is None:
        param = "default_value"
    # ...
```

### Pagination

```python
async def tool(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    Args:
        limit: Number of items to return (default: 50, max: 100)
        offset: Number of items to skip (default: 0)
    """
    # Validate limits
    limit = min(limit, 100)
    # ...
```

### Resource Validation

```python
async def tool(resource_id: str) -> Dict[str, Any]:
    try:
        resource = await fetch_resource(resource_id)
        if not resource:
            return {
                "success": False,
                "error": f"Resource {resource_id} not found"
            }
        # ...
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Handling External APIs

```python
import httpx

async def tool(api_param: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.example.com/{api_param}")
            response.raise_for_status()
            data = response.json()
            
        return {
            "success": True,
            "data": data,
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
```

## Package Initialization

When creating a new server, add `__init__.py`:

```python
"""Server name package."""

from .tool1 import tool1
from .tool2 import tool2

__all__ = [
    "tool1",
    "tool2",
]
```

## Error Messages Best Practices

- Be specific about what failed
- Include relevant parameter values
- Suggest solutions when possible

```python
# ✓ Good
return {
    "success": False,
    "error": f"Channel {channel_id} not found. Ensure bot has access and ID is correct."
}

# ✗ Bad
return {"success": False, "error": "Error occurred"}
```

## Performance Considerations

- **Lazy imports**: Import heavy dependencies inside functions
- **Connection pooling**: Reuse client connections (httpx.AsyncClient)
- **Timeouts**: Always set timeouts for external calls
- **Rate limiting**: Implement backoff for rate-limited APIs

## Security Guidelines

- **Input validation**: Validate all parameters before use
- **SQL injection**: Use parameterized queries
- **Path traversal**: Validate file paths
- **Secrets**: Never log or return sensitive data

```python
# Validate numeric IDs
try:
    numeric_id = int(string_id)
except ValueError:
    return {"success": False, "error": f"Invalid ID format: {string_id}"}

# Validate file paths (if needed)
from pathlib import Path
safe_path = Path(base_dir) / user_path
if not safe_path.resolve().is_relative_to(base_dir):
    return {"success": False, "error": "Invalid path"}
```

## Testing Tools

Create test files in `tests/` directory:

```python
import pytest
from src.mcp_ce.tools.server_name.tool_name import tool_name

@pytest.mark.asyncio
async def test_tool_success():
    result = await tool_name(required_param="test")
    assert result["success"] is True
    assert "data" in result

@pytest.mark.asyncio
async def test_tool_validation():
    result = await tool_name(required_param="")
    assert result["success"] is False
    assert "error" in result
```

## Example: Complete Tool Implementation

```python
"""Search users by username or email."""

from typing import Dict, Any, Optional, List
import httpx


async def search_users(
    query: str,
    limit: Optional[int] = 10,
    include_inactive: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Search for users matching the query.
    
    Args:
        query: Username or email to search for (min 3 characters)
        limit: Maximum results to return (default: 10, max: 100)
        include_inactive: Include inactive users (default: False)
        
    Returns:
        Dictionary with:
        - success: True if search completed
        - data: List of matching users with id, username, email
        - count: Total number of matches
        - error: Error message if failed
    """
    # Input validation
    if len(query) < 3:
        return {
            "success": False,
            "error": "Query must be at least 3 characters"
        }
    
    # Sanitize inputs
    limit = min(max(1, limit or 10), 100)
    
    try:
        # External API call with timeout
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.example.com/users/search",
                params={
                    "q": query,
                    "limit": limit,
                    "include_inactive": include_inactive,
                }
            )
            response.raise_for_status()
            data = response.json()
        
        return {
            "success": True,
            "data": data.get("users", []),
            "count": data.get("total", 0),
        }
        
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Search request timed out after 10 seconds"
        }
        
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": f"API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
```

## Quick Reference

| Aspect | Required |
|--------|----------|
| Function type | `async def` |
| Return type | `Dict[str, Any]` |
| Error handling | Try/except with error dict |
| Docstring | Args, Returns, description |
| Registry entry | `_SERVERS_REGISTRY` |
| Schema | `query_tool_docs()` |
| Execution | `_execute_tool()` |
| Import style | Dynamic inside elif |
| Package export | `__init__.py` |

## Getting Help

- Reference existing tools in `src/mcp_ce/tools/discord/` or `src/mcp_ce/tools/url_ping/`
- Check `DISCORD_MIGRATION.md` for migration patterns
- Review `runtime.py` for registration examples
- Run validation commands frequently during development
