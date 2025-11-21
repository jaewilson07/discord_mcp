# Action Plan: Remove Duplicate Code

## Summary of Findings

✅ **Safe to delete:** `event_extraction_graph/agent.py` (484 lines)
- No external imports found
- Only internal `__init__.py` references it
- Superseded by `workflows/event_extraction_workflow.py`

⚠️ **Still in use:** Several standalone agent files
- `facebook_event_agent.py` - Used by TEMP test scripts
- `save_article.py` - **Registered as MCP tool** in runtime.py
- `create_youtube_research_plan.py` - Listed in runtime.py
- `extract_structured_data.py` - Used by multiple files

## Immediate Actions (High Confidence)

### Action 1: Delete `event_extraction_graph/agent.py`

**Files to modify:**

1. **DELETE:** `src/mcp_ce/agents/event_extraction_graph/agent.py`
2. **UPDATE:** `src/mcp_ce/agents/event_extraction_graph/__init__.py`

**Changes:**

```python
# event_extraction_graph/__init__.py

# REMOVE these imports
# from .agent import extract_events_from_url
# from .agent import (
#     scraper_agent,
#     extraction_agent,
#     validation_agent,
#     workflow_agent,
# )

# KEEP only models and tools
from .models import (
    EventDetails,
    EventExtractionWorkflowResult,
    ExtractionResult,
    ValidationResult,
    ScrapedContent,
    ScrapingFailed,
    ExtractionFailed,
    NoEventsFound,
)

from .tools import (
    find_date_patterns,
    find_time_patterns,
    find_event_keywords,
    count_event_indicators,
    validate_event_completeness,
    compare_extraction_iterations,
)

__all__ = [
    # Models
    "EventDetails",
    "EventExtractionWorkflowResult",
    "ExtractionResult",
    "ValidationResult",
    "ScrapedContent",
    "ScrapingFailed",
    "ExtractionFailed",
    "NoEventsFound",
    # Tools
    "find_date_patterns",
    "find_time_patterns",
    "find_event_keywords",
    "count_event_indicators",
    "validate_event_completeness",
    "compare_extraction_iterations",
]
```

**Impact:**
- ✅ Removes 484 lines of duplicate code
- ✅ No breaking changes (no external usage)
- ✅ Forces use of new workflow architecture

---

## Follow-Up Actions (Need Review)

### Action 2: Review `save_article.py` Location

**Current location:** `src/mcp_ce/agents/save_article.py`

**Issue:** This is a **tool** (single operation), not an **agent** (orchestration)

**Usage:**
- Registered in `registry.py` as `@register_command("crawl4ai", "save_article")`
- Called from `runtime.py`
- Used in TEMP test scripts

**Recommendation:** Move to `src/mcp_ce/tools/crawl4ai/save_article.py`

**Why:** 
- Follows repository pattern (tools in `tools/`, agents in `agents/`)
- Already registered as crawl4ai tool
- Simple save operation, not multi-step workflow

**Steps:**
1. Move file: `agents/save_article.py` → `tools/crawl4ai/save_article.py`
2. Update import in `runtime.py`:
   ```python
   # OLD
   from .agents.save_article import save_article
   
   # NEW
   from .tools.crawl4ai.save_article import save_article
   ```
3. Test: Run TEMP test scripts

---

### Action 3: Review `facebook_event_agent.py`

**File:** `src/mcp_ce/agents/facebook_event_agent.py` (541 lines)

**Usage:** Only used in TEMP test scripts

**Purpose:** MCP-Agent wrapper for Facebook event scraping

**Question:** Does this duplicate the new `extract_events_from_url()` workflow?

**Findings:**
- Uses `extract_structured_data.py` for extraction
- Has Facebook-specific scraping logic
- Could potentially use new workflow architecture

**Recommendation:** **Keep for now**, but mark for future refactoring

**Future Refactoring:**
- Could use new `workflows/event_extraction_workflow.py`
- Facebook-specific logic stays in this file
- Delegates to generic workflow for extraction

---

### Action 4: Review `extract_structured_data.py`

**File:** `src/mcp_ce/agents/extract_structured_data.py`

**Usage:**
- `evaluator_optimizer.py` (events workflow)
- `create_from_url.py` (events workflow)
- `facebook_event_agent.py`
- `_old/smart_extract.py` (archived)
- TESTS

**Purpose:** Extract EventDetails from markdown content using LLM

**Status:** **KEEP - Actively used**

**Note:** This is a simple extraction function, not a full agent workflow. Different from the multi-agent extraction workflow.

---

### Action 5: Review `create_youtube_research_plan.py`

**File:** `src/mcp_ce/agents/create_youtube_research_plan.py`

**Usage:** 
- Listed in `runtime.py` servers registry
- Tested in TEMP scripts

**Purpose:** Generate research plan from YouTube video

**Status:** **KEEP - Registered as MCP tool**

**Note:** This is a standalone agent/tool, not part of event extraction workflow.

---

### Action 6: Clean Up `_old` Folder

**Location:** `src/mcp_ce/agents/events/_old/`

**Files:**
- `event_extraction_agent.py`
- `extract_events_workflow.py`
- `smart_extract.py`

**Usage:** None (archived)

**Recommendation:** **Delete after Action 1 is tested and confirmed working**

**Rationale:**
- Already replaced by new implementation
- Archived for reference only
- Can always recover from git history

---

## Execution Plan

### Phase 1: Delete Duplicate Workflow ✅ **READY TO EXECUTE**

```powershell
# Step 1: Delete agent.py
Remove-Item "src\mcp_ce\agents\event_extraction_graph\agent.py"

# Step 2: Update __init__.py (see changes above)
# Use replace_string_in_file tool

# Step 3: Test
python TEMP\test_agent_graph.py
```

**Expected Result:**
- No errors
- Workflow still works
- Imports from `mcp_ce.agents.workflows` work correctly

---

### Phase 2: Move save_article.py ⏸️ **OPTIONAL**

```powershell
# Step 1: Move file
Move-Item "src\mcp_ce\agents\save_article.py" "src\mcp_ce\tools\crawl4ai\save_article.py"

# Step 2: Update runtime.py import
# Use replace_string_in_file tool

# Step 3: Test
python TEMP\test_all_tools.py
```

**Risk:** Low (simple file move, only 1 import to update)

---

### Phase 3: Delete _old Folder ⏸️ **AFTER PHASE 1 CONFIRMED**

```powershell
Remove-Item -Recurse "src\mcp_ce\agents\events\_old"
```

**Risk:** None (already archived, can recover from git)

---

## Testing Checklist

### Before Making Changes

- [x] Verified no external imports of `agent.py`
- [x] Verified save_article usage
- [x] Verified facebook_event_agent usage
- [x] Verified extract_structured_data usage

### After Phase 1 (Delete agent.py)

- [ ] Run test: `python TEMP\test_agent_graph.py`
- [ ] Verify import: `from mcp_ce.agents import extract_events_from_url`
- [ ] Verify workflow: `await extract_events_from_url("https://example.com")`
- [ ] Check no import errors anywhere

### After Phase 2 (Move save_article)

- [ ] Run test: `python TEMP\test_all_tools.py`
- [ ] Verify runtime can find tool
- [ ] Check runtime.py imports

### After Phase 3 (Delete _old)

- [ ] Confirm new workflow works
- [ ] Archive commit hash for recovery if needed

---

## Summary

### Immediate Impact (Phase 1)

- **Delete:** 484 lines (agent.py)
- **Update:** 1 file (__init__.py)
- **Risk:** None (no external usage)
- **Benefit:** Eliminates duplicate workflow, forces new architecture

### Optional Improvements (Phase 2)

- **Move:** save_article.py to correct location
- **Risk:** Low (1 import to update)
- **Benefit:** Better organization, follows repository conventions

### Clean-Up (Phase 3)

- **Delete:** ~300 lines (_old folder)
- **Risk:** None (archived)
- **Benefit:** Cleaner repository

### Total Cleanup

**Lines Removed:** ~784 lines
**Files Removed:** 4 files
**Breaking Changes:** 0

---

## Ready to Execute?

✅ **Phase 1 is ready - no blockers found**

Shall I proceed with Phase 1?
