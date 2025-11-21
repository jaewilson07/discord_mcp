# Cursor MCP Workflow Instructions

This file provides specific workflow patterns for using MCP tools proactively in Cursor.

## Workflow: Code Review with Auto-Issue Creation

When reviewing code:

```python
# Pattern:
1. Analyze code for bugs, issues, or improvements
2. For each issue found:
   a. Check Linear for existing issue (use Linear search/list tools)
   b. If exists: Update with current context
   c. If not: Create Linear issue with:
      - Title: Brief description
      - Description: Code location, issue details, suggested fix
      - Labels: Appropriate tags (bug, enhancement, etc.)
      - Link to code: File path and line numbers
3. Use Context7 to find best practices for fixes
4. Store review notes in Notion
```

## Workflow: Feature Implementation

When implementing features:

```python
# Pattern:
1. Planning Phase:
   - Create Linear issue for feature tracking
   - Use Context7 to research implementation approaches
   - Check YouTube for tutorials/examples
   - Store research in Notion

2. Implementation Phase:
   - Use Context7 docs while coding
   - Reference Linear issue in commits/comments
   - Update Notion with progress

3. Completion Phase:
   - Update Linear issue with completion status
   - Document in Notion with final implementation
   - Optionally notify team via Discord
```

## Workflow: Bug Investigation

When investigating bugs:

```python
# Pattern:
1. Search Linear for similar issues
2. Use Context7 to find debugging techniques
3. Check Discord for team discussions
4. Use web scraping if bug involves external services
5. Document findings in Notion
6. Create/update Linear issue with findings
```

## Workflow: Learning New Technology

When learning something new:

```python
# Pattern:
1. Use Context7 to get official documentation
2. Search YouTube for video tutorials
3. Use web scraping to find additional resources
4. Store learning materials in Notion
5. Create Linear issue to track learning progress
```

## Workflow: Documentation Updates

When updating documentation:

```python
# Pattern:
1. Check Notion for existing documentation
2. Use Context7 to ensure accuracy
3. Update Notion with new information
4. Link to relevant Linear issues
5. Notify team via Discord if major changes
```

## Automatic Triggers

### Trigger: TODO/FIXME Comments
```python
# When you see TODO/FIXME in code:
1. Extract the comment text
2. Check Linear for existing issue
3. If not found, create Linear issue with:
   - Title from comment
   - Code location
   - Context from surrounding code
4. Link issue in code comment
```

### Trigger: Error Messages
```python
# When user encounters an error:
1. Use Context7 to search for error solutions
2. Check Linear for known issues
3. Search Discord for team discussions
4. Provide solution with references
5. Create Linear issue if it's a new bug
```

### Trigger: New Library Usage
```python
# When code uses a new library:
1. Use Context7 to fetch library docs
2. Get examples and best practices
3. Check for known issues or gotchas
4. Store library notes in Notion
5. Update project dependencies in Linear
```

### Trigger: Code Changes
```python
# When making significant code changes:
1. Check Linear for related issues
2. Update or create Linear issue
3. Use Context7 to verify best practices
4. Update Notion documentation
5. Link changes to Linear issue in commit
```

## Tool Combinations

### Research Combo
```python
# For comprehensive research:
1. Context7 → Official docs
2. YouTube → Video tutorials
3. Web scraping → Additional resources
4. Notion → Store findings
```

### Bug Fix Combo
```python
# For bug fixes:
1. Linear → Track issue
2. Context7 → Find solutions
3. Discord → Coordinate with team
4. Notion → Document fix
```

### Feature Development Combo
```python
# For new features:
1. Linear → Track feature
2. Context7 → Research implementation
3. Notion → Document design
4. Discord → Coordinate development
```

## Memory Patterns

Store in Cursor memories:
- Frequently used Linear issue templates
- Common Context7 queries that were helpful
- Discord channel IDs for different purposes
- Notion page IDs for different documentation types
- Tool usage patterns that worked well

## Proactive Suggestions

When user is working, suggest:
- "I can create a Linear issue for this"
- "Let me fetch the latest docs for this library"
- "Should I check if there's a related Linear issue?"
- "I can store this in Notion for the team"
- "Want me to search for examples of this pattern?"

## Error Handling

If a tool fails:
1. Explain what went wrong
2. Suggest alternative approaches
3. Offer to retry or use different tool
4. Document the failure for future reference

## Performance Tips

- Cache frequently accessed docs
- Batch related tool calls
- Use tool discovery to find alternatives
- Remember successful tool combinations

