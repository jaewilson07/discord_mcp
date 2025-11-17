# GitHub Copilot Custom Instructions

This directory contains custom instructions for GitHub Copilot to provide context-aware assistance for this repository.

## Structure

### Repository-Wide Instructions
- **`.github/copilot-instructions.md`** - Main instructions for the entire repository
  - Repository overview and architecture
  - Building, running, and testing
  - Common pitfalls and solutions
  - Code style conventions
  - Environment setup with `uv`

### Path-Specific Instructions
Located in `.github/instructions/`:

- **`mcp-ce-tools.instructions.md`** - Instructions for MCP CE tool development
  - **Applies to:** `src/mcp_ce/tools/**/*.py`
  - Tool file structure and patterns
  - Three-step registration process (registry, schema, execution)
  - Validation checklists
  - Common patterns and examples
  
- **`mcp-agent.instructions.md`** - Instructions for MCP-Agent development
  - **Applies to:** `src/**/*agent*.py`
  - **Excluded from:** Code review agent
  - Agent structure with `@app.tool()` decorators
  - Tool patterns (sync vs async)
  - Agent instructions and LLM configuration
  - Integration with FastMCP

## How It Works

GitHub Copilot automatically uses these instructions when:
- **Repository-wide**: Any request in the context of this repository
- **Path-specific**: Working on files that match the `applyTo` glob patterns

The instructions appear in the References list of Copilot responses when they're used.

## Best Practices

1. **Keep instructions under 2 pages** - Copilot has token limits
2. **Be specific and actionable** - Focus on concrete patterns and requirements
3. **Include examples** - Code examples are more helpful than prose
4. **Avoid task-specific guidance** - Focus on reusable patterns
5. **Update when patterns change** - Keep instructions in sync with codebase

## Frontmatter Options

Path-specific instruction files use YAML frontmatter:

```yaml
---
applyTo: "path/pattern/**/*.py"
excludeAgent: "code-review"
---
```

**Options:**
- `applyTo` (required): Glob pattern for matching files
  - Single: `"src/tools/**/*.py"`
  - Multiple: `"**/*.ts,**/*.tsx"`
  - All files: `"**"` or `"**/*"`
  
- `excludeAgent` (optional): Exclude from specific agents
  - `"code-review"` - Don't use for PR reviews
  - `"coding-agent"` - Don't use for coding agent

## Verification

Check if custom instructions are being used:
1. Make a Copilot request in VS Code
2. Expand the References list in the response
3. Look for `.github/copilot-instructions.md` or `.instructions.md` files

## Enabling/Disabling

### VS Code
1. Open Settings (`Ctrl+,` / `Cmd+,`)
2. Search for "instruction file"
3. Toggle "Code Generation: Use Instruction Files"

### Per-Repository on GitHub
1. Go to repository Settings
2. Navigate to Copilot settings
3. Toggle custom instructions for code review

## Documentation

- [GitHub Docs: Add Repository Instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)
- [Customization Library](https://docs.github.com/en/copilot/tutorials/customization-library)
- [VS Code: Custom Instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)

## Related Files

- **`DISCORD_MIGRATION.md`** - Detailed Discord tool migration documentation
- **`INSTALL.md`** - Installation and setup instructions
- **`README.md`** - Public-facing repository documentation

## Maintenance

Update these instructions when:
- Adding new development patterns
- Changing tool registration process
- Updating build/test procedures
- Identifying common mistakes or pitfalls
- Major architectural changes

**Last Updated:** November 2024
