# Claude Integration Setup for UnMDX MCP Server

## Overview

This MCP server enables Claude to track and manage the UnMDX project rewrite progress through standardized MCP tools and resources.

## Installation & Setup

### 1. Server Installation

```bash
cd /home/dru/dev/unmdx/unmdx_mcp_server
uv sync
uv run unmdx-tracker init  # Initialize database
```

### 2. Claude Desktop Configuration

Add to your Claude Desktop config file (`claude_desktop_config.json`):

**On macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**On Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**On Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "unmdx-tracker": {
      "command": "uv",
      "args": ["run", "unmdx-mcp-server"],
      "cwd": "/home/dru/dev/unmdx/unmdx_mcp_server"
    }
  }
}
```

### 3. Restart Claude Desktop

After adding the configuration, restart Claude Desktop to load the MCP server.

## Available Tools

### Project Management
- `get_project_status` - Get overall project status and metrics
- `list_phases` - List all project phases with status
- `get_phase_progress` - Get detailed progress for a specific phase
- `update_phase_status` - Update phase status and notes

### Task Management  
- `create_task` - Create new tasks within phases
- `list_tasks` - List tasks with optional filtering
- `update_task_status` - Update task completion status

### Test Tracking
- `create_test_case` - Add new test cases
- `list_test_cases` - List all test cases and status
- `record_test_result` - Record test execution results
- `get_test_summary` - Get test execution analytics

### Development Tracking
- `log_commit` - Log git commits with test results
- `get_recent_activity` - Get recent project activity

## Available Resources

Browse project data through standardized URIs:

- `unmdx://phases` - All project phases
- `unmdx://tasks/all` - All tasks across phases  
- `unmdx://tests/summary` - Test execution summary
- `unmdx://commits/recent` - Recent git commits
- `unmdx://status/overview` - Complete project overview

## Example Usage

Once configured, you can ask Claude:

```
"What's the current status of the UnMDX rewrite project?"
"Which test cases are currently failing?"
"Show me the progress on Phase 2"
"Log this commit: abc123 - Fixed WHERE clause parsing"
"What tasks are pending in the current phase?"
```

## Verification

To verify the MCP server is working:

1. **Check server startup**:
   ```bash
   uv run unmdx-mcp-server --help
   ```

2. **Test CLI tools**:
   ```bash
   uv run unmdx-tracker status
   ```

3. **Run MCP tests**:
   ```bash
   uv run python test_mcp_server.py
   ```

## Troubleshooting

### Common Issues

1. **"MCP server not found"**
   - Verify the `cwd` path in config is correct
   - Ensure UV is installed and in PATH
   - Check that `uv sync` was run in the server directory

2. **"Database error"**
   - Run `uv run unmdx-tracker init` to initialize database
   - Check database permissions

3. **"Tools not available"**
   - Restart Claude Desktop after config changes
   - Verify JSON config file syntax

### Debugging

Enable debug logging by adding to the config:

```json
{
  "mcpServers": {
    "unmdx-tracker": {
      "command": "uv",
      "args": ["run", "unmdx-mcp-server", "--debug"],
      "cwd": "/home/dru/dev/unmdx/unmdx_mcp_server"
    }
  }
}
```

## Database Location

The project database is stored at:
```
/home/dru/dev/unmdx/unmdx_mcp_server/unmdx_tracking.db
```

This database contains all project phases, tasks, test cases, and commit history.

## Development

To extend the MCP server:

1. **Add new tools**: Edit `src/unmdx_tracker/mcp_server.py`
2. **Update database schema**: Modify `schema.sql` and migration scripts
3. **Add new models**: Update `src/unmdx_tracker/models.py`
4. **Test changes**: Run `uv run python test_mcp_server.py`

## Project Context

This MCP server is part of the UnMDX rewrite project recovery plan. It enables Claude to maintain context about:

- Project phases and milestones
- Task completion and progress
- Test case status and execution history  
- Git commit history and test results
- Overall project health and next steps

The server helps ensure continuity and progress tracking throughout the 12-week rewrite plan.