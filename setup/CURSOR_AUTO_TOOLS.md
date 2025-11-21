# Making Cursor Auto-Magically Use MCP Tools

This guide explains how to configure Cursor to automatically use your MCP tools while you work, without explicit requests.

## What We've Set Up

### 1. `.cursorrules` File

Created a `.cursorrules` file in your project root that instructs Cursor to:
- **Proactively use MCP tools** when they're relevant
- **Automatically trigger workflows** based on context
- **Combine multiple tools** for comprehensive solutions
- **Store and reference** tool usage in memories

### 2. Workflow Instructions

Created `.github/instructions/cursor-mcp-workflows.md` with specific patterns for:
- Code review → Linear issue creation
- Feature implementation → Full workflow
- Bug investigation → Multi-tool research
- Learning new tech → Comprehensive research

## How It Works

### Automatic Triggers

Cursor will automatically use tools when it detects:

1. **TODO/FIXME Comments** → Creates Linear issues
2. **Error Messages** → Searches Context7 and Linear for solutions
3. **New Library Usage** → Fetches Context7 docs automatically
4. **Code Changes** → Links to Linear issues
5. **Questions** → Uses Context7, YouTube, web scraping for answers

### Proactive Patterns

When you:
- **Mention a bug** → Cursor checks Linear, creates issue if needed
- **Ask "how do I..."** → Cursor fetches Context7 docs automatically
- **Write code** → Cursor suggests Linear issues, fetches relevant docs
- **Review code** → Cursor creates/updates Linear issues automatically

## Examples

### Example 1: Automatic Issue Creation

**You write:**
```python
# TODO: Fix memory leak in event handler
```

**Cursor automatically:**
1. Creates a Linear issue titled "Fix memory leak in event handler"
2. Links to the code location
3. Fetches Context7 docs about memory leaks
4. Suggests solutions based on docs

### Example 2: Automatic Documentation Lookup

**You write:**
```python
from fastmcp import FastMCP
```

**Cursor automatically:**
1. Fetches FastMCP documentation from Context7
2. Shows relevant examples
3. Checks for known issues in Linear
4. Stores useful patterns in memory

### Example 3: Automatic Bug Research

**You encounter an error:**
```
ModuleNotFoundError: No module named 'xyz'
```

**Cursor automatically:**
1. Searches Context7 for solutions
2. Checks Linear for known issues
3. Searches Discord for team discussions
4. Provides solution with references

## Customization

### Adjusting Proactivity

Edit `.cursorrules` to change how proactive Cursor is:

```markdown
## Less Proactive (Current Default)
- Only use tools when clearly relevant
- Ask before creating issues
- Suggest tool usage rather than auto-using

## More Proactive
- Always check Linear for related issues
- Auto-create issues for bugs
- Fetch docs without asking
```

### Adding Custom Workflows

Add to `.github/instructions/cursor-mcp-workflows.md`:

```markdown
## Workflow: Your Custom Pattern
When [trigger condition]:
1. Use [tool] to [action]
2. Use [tool] to [action]
3. Store in [location]
```

## Testing the Setup

### Test 1: TODO Comment
1. Add a TODO comment to your code
2. Ask Cursor to review the file
3. It should offer to create a Linear issue

### Test 2: New Library
1. Import a library you haven't used
2. Ask Cursor about it
3. It should automatically fetch Context7 docs

### Test 3: Bug Report
1. Describe a bug you found
2. Cursor should check Linear and create issue if needed

## Troubleshooting

### Tools Not Being Used

1. **Check `.cursorrules` exists** in project root
2. **Verify MCP servers are connected** in Cursor settings
3. **Restart Cursor** after adding `.cursorrules`
4. **Check Cursor logs** for tool errors

### Too Proactive / Not Proactive Enough

1. Edit `.cursorrules` to adjust behavior
2. Modify workflow instructions in `.github/instructions/`
3. Restart Cursor to reload rules

### Tools Failing

1. Check API keys are set correctly
2. Verify MCP servers are running
3. Check Cursor Developer Tools for errors
4. Test tools manually first

## Advanced: Custom Prompts

You can also create custom prompts that force tool usage:

**In Cursor Chat:**
```
@cursorrules When I mention a bug, always:
1. Check Linear for existing issues
2. Create issue if not found
3. Fetch Context7 docs for solutions
4. Store findings in Notion
```

## Memory Integration

Cursor will remember:
- Which tools were useful for similar tasks
- Frequently accessed documentation
- Common Linear issue patterns
- Successful tool combinations

This makes future tool usage even more automatic!

## Best Practices

1. **Start conservative**: Let Cursor suggest tool usage first
2. **Gradually increase proactivity**: As you trust the setup more
3. **Review automatic actions**: Check Linear issues and Notion updates
4. **Refine workflows**: Update instructions based on what works
5. **Share patterns**: Document successful tool combinations

## Next Steps

1. **Test the setup** with the examples above
2. **Adjust `.cursorrules`** to match your preferences
3. **Add custom workflows** for your specific needs
4. **Monitor tool usage** and refine as needed
5. **Share feedback** on what works/doesn't work

The goal is to make Cursor so helpful that you rarely need to explicitly ask for tool usage - it just happens automatically when relevant!

