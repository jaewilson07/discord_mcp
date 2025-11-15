"""
Python code execution sandbox for zero-context discovery pattern.

Executes user Python code with injected runtime helpers for MCP discovery.
"""

import sys
import io
import contextlib
import traceback
from typing import Dict, Any, Optional
import asyncio


async def execute_python(code: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute Python code in a sandboxed environment with MCP runtime helpers.
    
    Args:
        code: Python code to execute
        timeout: Execution timeout in seconds (default: 30)
    
    Returns:
        Dictionary with:
            - success: bool
            - stdout: captured standard output
            - stderr: captured standard error
            - result: return value (if any)
            - error: error message (if failed)
    
    The code has access to:
        - discovered_servers(): List available MCP servers
        - list_servers(): Get server names
        - query_tool_docs(server, tool, detail): Load tool docs on-demand
        - search_tool_docs(query, limit): Search for tools
        - create_tool_proxy(server, tool): Create tool callable
    """
    from .runtime import (
        discovered_servers,
        list_servers,
        list_servers_sync,
        query_tool_docs,
        query_tool_docs_sync,
        search_tool_docs,
        search_tool_docs_sync,
        create_tool_proxy,
        capability_summary,
        _execute_tool,
        _execute_tool_sync,
    )
    
    # Prepare sandbox globals
    sandbox_globals = {
        # Runtime helpers
        "discovered_servers": discovered_servers,
        "list_servers": list_servers,
        "list_servers_sync": list_servers_sync,
        "query_tool_docs": query_tool_docs,
        "query_tool_docs_sync": query_tool_docs_sync,
        "search_tool_docs": search_tool_docs,
        "search_tool_docs_sync": search_tool_docs_sync,
        "create_tool_proxy": create_tool_proxy,
        "capability_summary": capability_summary,
        # Standard library
        "json": __import__("json"),
        "asyncio": asyncio,
        # Python builtins (restricted)
        "__builtins__": {
            "print": print,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "isinstance": isinstance,
            "type": type,
            "__import__": __import__,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
        },
    }
    
    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    result = {
        "success": False,
        "stdout": "",
        "stderr": "",
        "result": None,
        "error": None,
    }
    
    try:
        # Execute with timeout
        async def _execute():
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                try:
                    # Compile code
                    compiled = compile(code, "<sandbox>", "exec")
                    
                    # Execute in sandbox
                    exec(compiled, sandbox_globals)
                    
                    # Check if there's a main coroutine to await
                    if "main" in sandbox_globals and asyncio.iscoroutinefunction(sandbox_globals["main"]):
                        return await sandbox_globals["main"]()
                    
                    return None
                    
                except Exception as e:
                    raise
        
        # Run with timeout
        exec_result = await asyncio.wait_for(_execute(), timeout=timeout)
        
        result["success"] = True
        result["result"] = exec_result
        
    except asyncio.TimeoutError:
        result["error"] = f"Execution timed out after {timeout} seconds"
        result["stderr"] = stderr_capture.getvalue()
        
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
        result["stderr"] = stderr_capture.getvalue() + "\n" + traceback.format_exc()
    
    finally:
        result["stdout"] = stdout_capture.getvalue()
        if not result["stderr"]:
            result["stderr"] = stderr_capture.getvalue()
    
    return result


# Synchronous version (for non-async contexts)
def execute_python_sync(code: str, timeout: int = 30) -> Dict[str, Any]:
    """Synchronous wrapper for execute_python()"""
    return asyncio.run(execute_python(code, timeout))
