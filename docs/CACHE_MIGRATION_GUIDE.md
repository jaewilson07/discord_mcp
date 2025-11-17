# Cache Migration Guide

## Issue: Old Dict Format in Cache Files

**Date:** November 17, 2025

### Problem Summary

During the Discord tools refactoring (dict → ToolResponse), we discovered that **old cached data with dict format was causing runtime errors** even after tools were properly refactored.

### Root Cause

The `@cache_tool` decorator caches function results to disk (`.cache/` directory). When tools were refactored from returning `dict` to returning `ToolResponse`, the old cached data still contained the dict format:

**Old Format (Before Refactoring):**
```json
{
  "timestamp": 1763388593.304694,
  "result": {
    "success": true,
    "user": {
      "id": "1438974658786627597",
      "name": "MyBot"
    }
  }
}
```

**New Format (After Refactoring):**
```json
{
  "timestamp": 1763389123.456789,
  "result": {
    "is_success": true,
    "result": {
      "user_id": "1438974658786627597",
      "username": "MyBot",
      ...
    },
    "error": null
  },
  "result_type": "UserInfo"
}
```

### Symptoms

**Error Message:**
```
TypeError: Tool 'discord.get_user_info' must return ToolResponse, got dict.
Import: from mcp_ce.tools.model import ToolResponse
```

**When It Occurs:**
- Tool code is correctly refactored to return ToolResponse
- Tool compiles successfully
- Tests fail at runtime when cache hit occurs
- Fresh (non-cached) calls work fine

### Solution

**Immediate Fix:**
Clear the cache directory to force fresh fetches:

```powershell
# Clear all caches
Remove-Item -Path ".cache\*" -Recurse -Force

# Or clear specific tool cache
Remove-Item -Path ".cache\get_user_info" -Recurse -Force
```

**Finding Old Format Caches:**
```powershell
# Find all cache files with old dict format
Get-ChildItem -Path ".cache" -Recurse -File -Filter "*.json" | ForEach-Object {
    $content = Get-Content $_.FullName | ConvertFrom-Json
    if ($content.result.success -ne $null -and $content.result.is_success -eq $null) {
        Write-Host "Old format: $($_.FullName)"
    }
}

# Delete all old format caches
Get-ChildItem -Path ".cache" -Recurse -File -Filter "*.json" | ForEach-Object {
    $content = Get-Content $_.FullName | ConvertFrom-Json
    if ($content.result.success -ne $null -and $content.result.is_success -eq $null) {
        Remove-Item $_.FullName -Force
        Write-Host "Deleted: $($_.Name)"
    }
}
```

### Prevention

**Going Forward:**
1. **After major refactoring:** Always clear `.cache/` directory
2. **Before running tests:** Clear cache to ensure fresh data
3. **Cache versioning:** Consider adding version field to cache format
4. **Documentation:** Document cache format changes in migration notes

### Tools Affected in This Migration

During live Discord testing, we found these tools had old cached data:
- `get_user_info` - Had dict with nested "user" field
- `read_messages` - Had dict with "success" and "messages" fields
- `get_video_metadata` - Had old YouTube metadata format

### Cache Decorator Behavior

The `@cache_tool` decorator in `src/mcp_ce/cache/cache.py`:
1. Checks if cached file exists and is within TTL
2. Returns cached data directly if valid
3. Does NOT validate cached data format against current tool signature
4. Only caches successful results (`is_success=True`)

**Key Insight:** The cache decorator trusts cached data format and doesn't validate it against the current tool's return type. This means **format changes require manual cache invalidation**.

### Recommendations

**For Future Refactoring:**
1. Add cache version to decorator: `@cache_tool(ttl=3600, version="v2")`
2. Invalidate cache automatically when version changes
3. Add validation layer to check cached data format
4. Consider cache migration script for major format changes

**For Testing:**
1. Always test with clean cache after refactoring
2. Run tests twice: once with cold cache, once with warm cache
3. Add cache validation to test suite
4. Document expected cache format in tool docstrings

### Related Files

- `src/mcp_ce/cache/cache.py` - Cache decorator implementation
- `src/registry.py` - ToolResponse validation (catches dict returns)
- `COMPREHENSIVE_CODE_REVIEW.md` - Refactoring status tracker
- `.cache/` - Cache storage directory (git-ignored)

### Lessons Learned

1. **Compilation ≠ Runtime Success** - Tools can compile but fail at runtime due to cached data
2. **Test with Live Data** - Live server testing caught issues that unit tests missed
3. **Cache is State** - Cached data is mutable state that persists across refactoring
4. **Format Changes = Breaking Changes** - Changing return format requires cache invalidation
5. **Documentation Matters** - This guide will help future developers understand cache-related failures
