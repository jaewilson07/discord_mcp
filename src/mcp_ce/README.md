# MCP Code Execution Server - Zero-Context Discovery

A FastMCP-based server implementing elusznik's **zero-context discovery pattern** for efficient MCP tool access with minimal context overhead.

## 🎯 Key Features

- **Zero-Context Discovery**: ~200 token overhead (vs ~30K traditional MCP)
- **On-Demand Schema Loading**: Tool schemas loaded only when needed
- **Runtime Helpers**: Discovery functions injected into Python sandbox
- **Progressive Disclosure**: Code execution pattern for autonomous tool usage
- **Single Tool Interface**: `run_python` executes code with MCP access

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install fastmcp httpx

# Or use requirements.txt
pip install -r requirements.txt
```

### Run Server

```bash
# Show sandbox helpers info
python -m src.mcp_ce.server --info

# Run FastMCP server
python -m src.mcp_ce.server
```

### Test Discovery Workflow

```bash
python src/mcp_ce/test_discovery.py
```

## 📚 Architecture

### Zero-Context Discovery Pattern

Traditional MCP preloads all tool schemas into context (~30K tokens). This pattern uses **discovery-first** approach:

1. **Discovery**: LLM calls `discovered_servers()` to see available servers (no schemas)
2. **Schema Loading**: LLM calls `query_tool_docs(server)` to load specific schemas on-demand
3. **Code Execution**: LLM writes Python using `create_tool_proxy()` to call tools
4. **Execution**: Code runs in sandbox with constant ~200 token overhead

### Files

```
src/mcp_ce/
├── server.py          # FastMCP server with run_python tool
├── runtime.py         # Discovery helpers (discovered_servers, query_tool_docs, etc.)
├── sandbox.py         # Python code execution sandbox
├── test_discovery.py  # Test suite for discovery workflow
└── tools/
    └── url_ping/
        ├── ping_url.py    # URL ping tool implementation
        └── README.md      # Tool documentation
```

## 🔧 Usage

### 1. Discovery Workflow (LLM Perspective)

```python
# Step 1: Discover available servers (no schemas loaded)
servers = discovered_servers()
# Returns: [{"name": "url_ping", "description": "..."}]

# Step 2: Query tool docs on-demand
docs = query_tool_docs("url_ping", detail="summary")
# Loads schema only for url_ping server

# Step 3: Create tool proxy
ping = create_tool_proxy("url_ping", "ping_url")

# Step 4: Execute tool
result = await ping(url="https://example.com", timeout=10)
```

### 2. Runtime Helpers

Available in sandbox:

| Helper | Description | Signature |
|--------|-------------|-----------|
| `discovered_servers()` | List servers without loading schemas | `() -> List[Dict[str, str]]` |
| `list_servers()` | Get server names only | `() -> List[str]` |
| `query_tool_docs()` | Load tool schemas on-demand | `(server_name: str, tool: Optional[str] = None, detail: str = 'summary') -> str` |
| `search_tool_docs()` | Fuzzy search for tools | `(query: str, limit: Optional[int] = None) -> str` |
| `create_tool_proxy()` | Create callable for tool | `(server_name: str, tool_name: str) -> Callable` |

### 3. Example: Ping URL

```python
import json

# Discover servers
servers = discovered_servers()
print(f"Available: {json.dumps(servers, indent=2)}")

# Query tool docs
docs = query_tool_docs("url_ping", tool="ping_url", detail="full")
print(f"Documentation: {docs}")

# Execute tool
async def main():
    ping = create_tool_proxy("url_ping", "ping_url")
    result = await ping(url="https://www.google.com", timeout=10)
    return result
```

### 4. FastMCP Tool: `run_python`

The server exposes a single MCP tool:

```json
{
  "name": "run_python",
  "description": "Execute Python code in sandbox with MCP runtime helpers",
  "parameters": {
    "code": "Python code to execute",
    "timeout": "Execution timeout in seconds (default: 30)"
  }
}
```

## 🎓 Comparison: Zero-Context vs Traditional MCP

| Aspect | Zero-Context Discovery | Traditional MCP |
|--------|------------------------|-----------------|
| **Context Overhead** | ~200 tokens (constant) | ~30K tokens (grows with tools) |
| **Schema Loading** | On-demand (query_tool_docs) | Preloaded at startup |
| **Workflow** | Discover → Query → Execute | Direct tool invocation |
| **Scalability** | Constant overhead for any # of servers | Linear growth |
| **Pattern** | Code execution via run_python | Direct MCP tool calls |

## 🧪 Testing

Run comprehensive test suite:

```bash
python src/mcp_ce/test_discovery.py
```

Tests include:
1. ✅ Capability summary
2. ✅ Server discovery (zero-context)
3. ✅ Server name listing
4. ✅ On-demand schema loading
5. ✅ Tool search (fuzzy matching)
6. ✅ Complete discovery workflow with tool execution

## 📦 Available Servers

### url_ping

Ping URLs and check availability.

**Tool**: `ping_url`

**Parameters**:
- `url` (string, required): URL to ping (must include protocol)
- `timeout` (integer, optional): Request timeout in seconds (default: 10)

**Returns**:
```json
{
  "success": true,
  "url": "https://example.com",
  "status_code": 200,
  "status_text": "OK",
  "response_time_seconds": 1.5,
  "headers": {...}
}
```

## 🔒 Sandbox Security

The Python sandbox provides restricted access:

**Allowed**:
- Runtime helpers (discovered_servers, query_tool_docs, etc.)
- Standard library modules (json, asyncio)
- Basic builtins (print, len, str, int, float, list, dict, etc.)

**Restricted**:
- File system access (no open, read, write)
- Network access (only via MCP tools)
- Process execution (no os.system, subprocess)
- Dangerous builtins (eval, exec are controlled)

## 🛠️ Adding New Servers

1. **Create server directory**: `src/mcp_ce/tools/your_server/`
2. **Implement tool**: Create `your_tool.py` with async functions
3. **Register in runtime.py**:

```python
_SERVERS_REGISTRY = {
    "your_server": {
        "name": "your_server",
        "description": "Your server description",
        "module": "src.mcp_ce.tools.your_server.your_tool",
        "tools": ["your_tool"]
    }
}
```

4. **Add tool docs** in `query_tool_docs()` function
5. **Add execution** in `_execute_tool()` function

## 📖 References

- **elusznik's Pattern**: [mcp-server-code-execution-mode](https://github.com/elusznik/mcp-server-code-execution-mode)
- **FastMCP**: [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)

## 📝 License

See main project LICENSE.

## 🤝 Contributing

This is part of the mcp-discord project. Follow the main project contribution guidelines.
