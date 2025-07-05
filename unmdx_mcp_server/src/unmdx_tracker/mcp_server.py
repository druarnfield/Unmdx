"""
MCP Server for UnMDX Project Tracking System.

This server exposes the UnMDX project tracking database through MCP tools and resources.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.session import ServerSession
from mcp.types import (
    Tool,
    Resource,
    TextContent,
    TextResourceContents,
    CallToolResult,
    ListResourcesResult,
    ListToolsResult,
    ReadResourceResult,
    Prompt,
    ListPromptsResult,
    GetPromptResult,
    PromptMessage,
    EmbeddedResource,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
)
from pydantic import BaseModel, Field

from .database import UnMDXDatabase, DatabaseError
from .models import (
    CreatePhaseRequest, UpdatePhaseRequest, CreateTaskRequest, UpdateTaskRequest,
    CreateTestCaseRequest, UpdateTestCaseRequest, CreateCommitRequest,
    RecordTestExecutionRequest, ProjectStatus, PhaseProgress, TestCaseResult
)

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    """Configuration for the MCP server."""
    database_path: str = Field(default="unmdx_tracking.db", description="Path to SQLite database")
    log_level: str = Field(default="INFO", description="Logging level")
    enable_debug: bool = Field(default=False, description="Enable debug logging")


class UnMDXMCPServer:
    """MCP Server for UnMDX project tracking."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.db = UnMDXDatabase(config.database_path)
        self.server = Server("unmdx-tracker")
        self._setup_logging()
        self._setup_handlers()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        if self.config.enable_debug:
            logging.getLogger('mcp').setLevel(logging.DEBUG)
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        self.server.list_tools = self._list_tools
        self.server.call_tool = self._call_tool
        self.server.list_resources = self._list_resources
        self.server.read_resource = self._read_resource
        self.server.list_prompts = self._list_prompts
        self.server.get_prompt = self._get_prompt
    
    async def _list_tools(self) -> ListToolsResult:
        """List available MCP tools."""
        tools = [
            Tool(
                name="get_project_status",
                description="Get overall project status including phases, tasks, and test statistics",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_phase_progress",
                description="Get detailed progress for a specific phase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phase_id": {
                            "type": "integer",
                            "description": "ID of the phase to get progress for"
                        }
                    },
                    "required": ["phase_id"]
                }
            ),
            Tool(
                name="list_phases",
                description="List all project phases with their current status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="update_phase_status",
                description="Update the status of a specific phase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phase_id": {
                            "type": "integer",
                            "description": "ID of the phase to update"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["not_started", "in_progress", "completed", "blocked"],
                            "description": "New status for the phase"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional notes about the status change"
                        }
                    },
                    "required": ["phase_id", "status"]
                }
            ),
            Tool(
                name="create_task",
                description="Create a new task within a phase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phase_id": {
                            "type": "integer",
                            "description": "ID of the phase this task belongs to"
                        },
                        "description": {
                            "type": "string",
                            "description": "Task description"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Task priority",
                            "default": "medium"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "blocked"],
                            "description": "Initial task status",
                            "default": "pending"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional notes about the task"
                        }
                    },
                    "required": ["phase_id", "description"]
                }
            ),
            Tool(
                name="update_task_status",
                description="Update the status of a specific task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "integer",
                            "description": "ID of the task to update"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "blocked"],
                            "description": "New status for the task"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional notes about the status change"
                        }
                    },
                    "required": ["task_id", "status"]
                }
            ),
            Tool(
                name="list_tasks",
                description="List tasks, optionally filtered by phase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phase_id": {
                            "type": "integer",
                            "description": "Optional phase ID to filter tasks"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "blocked"],
                            "description": "Optional status filter"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="record_test_result",
                description="Record the result of a test execution",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_case_id": {
                            "type": "integer",
                            "description": "ID of the test case"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["passed", "failed", "skipped", "error"],
                            "description": "Test execution status"
                        },
                        "duration_ms": {
                            "type": "integer",
                            "description": "Test execution duration in milliseconds"
                        },
                        "error_message": {
                            "type": "string",
                            "description": "Error message if test failed"
                        },
                        "commit_hash": {
                            "type": "string",
                            "description": "Git commit hash where test was executed"
                        }
                    },
                    "required": ["test_case_id", "status"]
                }
            ),
            Tool(
                name="get_test_summary",
                description="Get test case summary with recent execution history",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_case_id": {
                            "type": "integer",
                            "description": "ID of the test case"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of recent executions to return",
                            "default": 10
                        }
                    },
                    "required": ["test_case_id"]
                }
            ),
            Tool(
                name="log_commit",
                description="Log a git commit with associated phase and test results",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hash": {
                            "type": "string",
                            "description": "Git commit hash"
                        },
                        "branch": {
                            "type": "string",
                            "description": "Git branch name"
                        },
                        "message": {
                            "type": "string",
                            "description": "Commit message"
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "Commit timestamp in ISO format"
                        },
                        "phase_id": {
                            "type": "integer",
                            "description": "Associated phase ID"
                        },
                        "test_results": {
                            "type": "object",
                            "description": "Test results as JSON object"
                        },
                        "author": {
                            "type": "string",
                            "description": "Commit author"
                        }
                    },
                    "required": ["hash", "branch", "message", "timestamp"]
                }
            ),
            Tool(
                name="get_recent_activity",
                description="Get recent project activity including commits and task updates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of recent activities to return",
                            "default": 10
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="create_test_case",
                description="Create a new test case",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Test case name"
                        },
                        "description": {
                            "type": "string",
                            "description": "Test case description"
                        },
                        "test_type": {
                            "type": "string",
                            "enum": ["unit", "integration", "e2e"],
                            "description": "Type of test case"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["passing", "failing", "skipped", "not_run"],
                            "description": "Initial test status",
                            "default": "not_run"
                        }
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="list_test_cases",
                description="List all test cases with their current status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["passing", "failing", "skipped", "not_run"],
                            "description": "Optional status filter"
                        },
                        "test_type": {
                            "type": "string",
                            "enum": ["unit", "integration", "e2e"],
                            "description": "Optional test type filter"
                        }
                    },
                    "required": []
                }
            )
        ]
        
        return ListToolsResult(tools=tools)
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle tool calls."""
        try:
            if name == "get_project_status":
                return await self._get_project_status()
            elif name == "get_phase_progress":
                return await self._get_phase_progress(arguments)
            elif name == "list_phases":
                return await self._list_phases()
            elif name == "update_phase_status":
                return await self._update_phase_status(arguments)
            elif name == "create_task":
                return await self._create_task(arguments)
            elif name == "update_task_status":
                return await self._update_task_status(arguments)
            elif name == "list_tasks":
                return await self._list_tasks(arguments)
            elif name == "record_test_result":
                return await self._record_test_result(arguments)
            elif name == "get_test_summary":
                return await self._get_test_summary(arguments)
            elif name == "log_commit":
                return await self._log_commit(arguments)
            elif name == "get_recent_activity":
                return await self._get_recent_activity(arguments)
            elif name == "create_test_case":
                return await self._create_test_case(arguments)
            elif name == "list_test_cases":
                return await self._list_test_cases(arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    isError=True
                )
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def _get_project_status(self) -> CallToolResult:
        """Get overall project status."""
        try:
            status = self.db.get_project_status()
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(status.dict(), indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _get_phase_progress(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get phase progress."""
        try:
            phase_id = arguments.get("phase_id")
            if not phase_id:
                return CallToolResult(
                    content=[TextContent(type="text", text="phase_id is required")],
                    isError=True
                )
            
            progress = self.db.get_phase_progress(phase_id)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(progress.dict(), indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _list_phases(self) -> CallToolResult:
        """List all phases."""
        try:
            phases = self.db.get_all_phases()
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps([p.dict() for p in phases], indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _update_phase_status(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Update phase status."""
        try:
            phase_id = arguments.get("phase_id")
            status = arguments.get("status")
            notes = arguments.get("notes")
            
            if not phase_id or not status:
                return CallToolResult(
                    content=[TextContent(type="text", text="phase_id and status are required")],
                    isError=True
                )
            
            request = UpdatePhaseRequest(status=status, notes=notes)
            updated_phase = self.db.update_phase(phase_id, request)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(updated_phase.dict(), indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _create_task(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Create a new task."""
        try:
            phase_id = arguments.get("phase_id")
            description = arguments.get("description")
            priority = arguments.get("priority", "medium")
            status = arguments.get("status", "pending")
            notes = arguments.get("notes")
            
            if not phase_id or not description:
                return CallToolResult(
                    content=[TextContent(type="text", text="phase_id and description are required")],
                    isError=True
                )
            
            request = CreateTaskRequest(
                phase_id=phase_id,
                description=description,
                priority=priority,
                status=status,
                notes=notes
            )
            task = self.db.create_task(request)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(task.dict(), indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _update_task_status(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Update task status."""
        try:
            task_id = arguments.get("task_id")
            status = arguments.get("status")
            notes = arguments.get("notes")
            
            if not task_id or not status:
                return CallToolResult(
                    content=[TextContent(type="text", text="task_id and status are required")],
                    isError=True
                )
            
            request = UpdateTaskRequest(status=status, notes=notes)
            updated_task = self.db.update_task(task_id, request)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(updated_task.dict(), indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _list_tasks(self, arguments: Dict[str, Any]) -> CallToolResult:
        """List tasks with optional filtering."""
        try:
            phase_id = arguments.get("phase_id")
            status_filter = arguments.get("status")
            
            if phase_id:
                tasks = self.db.get_tasks_by_phase(phase_id)
            else:
                # Get all tasks from all phases
                phases = self.db.get_all_phases()
                tasks = []
                for phase in phases:
                    tasks.extend(self.db.get_tasks_by_phase(phase.id))
            
            # Apply status filter if provided
            if status_filter:
                tasks = [t for t in tasks if t.status == status_filter]
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps([t.dict() for t in tasks], indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _record_test_result(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Record test execution result."""
        try:
            test_case_id = arguments.get("test_case_id")
            status = arguments.get("status")
            duration_ms = arguments.get("duration_ms")
            error_message = arguments.get("error_message")
            commit_hash = arguments.get("commit_hash")
            
            if not test_case_id or not status:
                return CallToolResult(
                    content=[TextContent(type="text", text="test_case_id and status are required")],
                    isError=True
                )
            
            request = RecordTestExecutionRequest(
                test_case_id=test_case_id,
                status=status,
                duration_ms=duration_ms,
                error_message=error_message,
                commit_hash=commit_hash
            )
            execution = self.db.record_test_execution(request)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(execution.dict(), indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _get_test_summary(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get test case summary."""
        try:
            test_case_id = arguments.get("test_case_id")
            limit = arguments.get("limit", 10)
            
            if not test_case_id:
                return CallToolResult(
                    content=[TextContent(type="text", text="test_case_id is required")],
                    isError=True
                )
            
            result = self.db.get_test_case_results(test_case_id, limit)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result.dict(), indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _log_commit(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Log a git commit."""
        try:
            hash_val = arguments.get("hash")
            branch = arguments.get("branch")
            message = arguments.get("message")
            timestamp_str = arguments.get("timestamp")
            phase_id = arguments.get("phase_id")
            test_results = arguments.get("test_results")
            author = arguments.get("author")
            
            if not hash_val or not branch or not message or not timestamp_str:
                return CallToolResult(
                    content=[TextContent(type="text", text="hash, branch, message, and timestamp are required")],
                    isError=True
                )
            
            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            request = CreateCommitRequest(
                hash=hash_val,
                branch=branch,
                message=message,
                timestamp=timestamp,
                phase_id=phase_id,
                test_results=test_results,
                author=author
            )
            commit = self.db.create_commit(request)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(commit.dict(), indent=2, default=str))]
            )
        except (ValueError, DatabaseError) as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {e}")],
                isError=True
            )
    
    async def _get_recent_activity(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get recent project activity."""
        try:
            limit = arguments.get("limit", 10)
            
            # Get recent commits
            commits = self.db.get_recent_commits(limit)
            
            # Format activity list
            activity = []
            for commit in commits:
                activity.append({
                    "type": "commit",
                    "timestamp": commit.timestamp,
                    "data": commit.dict()
                })
            
            # Sort by timestamp
            activity.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(activity[:limit], indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _create_test_case(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Create a new test case."""
        try:
            name = arguments.get("name")
            description = arguments.get("description")
            test_type = arguments.get("test_type")
            status = arguments.get("status", "not_run")
            
            if not name:
                return CallToolResult(
                    content=[TextContent(type="text", text="name is required")],
                    isError=True
                )
            
            request = CreateTestCaseRequest(
                name=name,
                description=description,
                test_type=test_type,
                status=status
            )
            test_case = self.db.create_test_case(request)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(test_case.dict(), indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _list_test_cases(self, arguments: Dict[str, Any]) -> CallToolResult:
        """List test cases with optional filtering."""
        try:
            status_filter = arguments.get("status")
            test_type_filter = arguments.get("test_type")
            
            test_cases = self.db.get_all_test_cases()
            
            # Apply filters
            if status_filter:
                test_cases = [tc for tc in test_cases if tc.status == status_filter]
            if test_type_filter:
                test_cases = [tc for tc in test_cases if tc.test_type == test_type_filter]
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps([tc.dict() for tc in test_cases], indent=2, default=str))]
            )
        except DatabaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Database error: {e}")],
                isError=True
            )
    
    async def _list_resources(self) -> ListResourcesResult:
        """List available MCP resources."""
        resources = [
            Resource(
                uri="unmdx://phases",
                name="Project Phases",
                description="List of all project phases with their status",
                mimeType="application/json"
            ),
            Resource(
                uri="unmdx://tasks/all",
                name="All Tasks",
                description="List of all tasks across all phases",
                mimeType="application/json"
            ),
            Resource(
                uri="unmdx://tests/summary",
                name="Test Summary",
                description="Summary of all test cases and their current status",
                mimeType="application/json"
            ),
            Resource(
                uri="unmdx://commits/recent",
                name="Recent Commits",
                description="List of recent git commits",
                mimeType="application/json"
            ),
            Resource(
                uri="unmdx://status/overview",
                name="Project Status Overview",
                description="Complete project status overview",
                mimeType="application/json"
            )
        ]
        
        return ListResourcesResult(resources=resources)
    
    async def _read_resource(self, uri: str) -> ReadResourceResult:
        """Read a specific resource."""
        try:
            if uri == "unmdx://phases":
                phases = self.db.get_all_phases()
                return ReadResourceResult(
                    contents=[TextResourceContents(
                        uri=uri,
                        mimeType="application/json",
                        text=json.dumps([p.dict() for p in phases], indent=2, default=str)
                    )]
                )
            elif uri == "unmdx://tasks/all":
                # Get all tasks from all phases
                phases = self.db.get_all_phases()
                all_tasks = []
                for phase in phases:
                    tasks = self.db.get_tasks_by_phase(phase.id)
                    all_tasks.extend(tasks)
                return ReadResourceResult(
                    contents=[TextResourceContents(
                        uri=uri,
                        mimeType="application/json",
                        text=json.dumps([t.dict() for t in all_tasks], indent=2, default=str)
                    )]
                )
            elif uri == "unmdx://tests/summary":
                test_cases = self.db.get_all_test_cases()
                return ReadResourceResult(
                    contents=[TextResourceContents(
                        uri=uri,
                        mimeType="application/json",
                        text=json.dumps([tc.dict() for tc in test_cases], indent=2, default=str)
                    )]
                )
            elif uri == "unmdx://commits/recent":
                commits = self.db.get_recent_commits(20)
                return ReadResourceResult(
                    contents=[TextResourceContents(
                        uri=uri,
                        mimeType="application/json",
                        text=json.dumps([c.dict() for c in commits], indent=2, default=str)
                    )]
                )
            elif uri == "unmdx://status/overview":
                status = self.db.get_project_status()
                return ReadResourceResult(
                    contents=[TextResourceContents(
                        uri=uri,
                        mimeType="application/json",
                        text=json.dumps(status.dict(), indent=2, default=str)
                    )]
                )
            elif uri.startswith("unmdx://tasks/"):
                # Handle phase-specific tasks
                phase_id_str = uri.split("/")[-1]
                try:
                    phase_id = int(phase_id_str)
                    tasks = self.db.get_tasks_by_phase(phase_id)
                    return ReadResourceResult(
                        contents=[TextResourceContents(
                            uri=uri,
                            mimeType="application/json",
                            text=json.dumps([t.dict() for t in tasks], indent=2, default=str)
                        )]
                    )
                except ValueError:
                    return ReadResourceResult(
                        contents=[TextResourceContents(
                            uri=uri,
                            mimeType="text/plain",
                            text=f"Invalid phase ID: {phase_id_str}"
                        )]
                    )
            else:
                return ReadResourceResult(
                    contents=[TextResourceContents(
                        uri=uri,
                        mimeType="text/plain",
                        text=f"Unknown resource: {uri}"
                    )]
                )
        except DatabaseError as e:
            return ReadResourceResult(
                contents=[TextResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text=f"Database error: {e}"
                )]
            )
    
    async def _list_prompts(self) -> ListPromptsResult:
        """List available prompts."""
        prompts = [
            Prompt(
                name="project_status_report",
                description="Generate a comprehensive project status report",
                arguments=[
                    {
                        "name": "include_details",
                        "description": "Include detailed task and test information",
                        "required": False
                    }
                ]
            ),
            Prompt(
                name="phase_analysis",
                description="Analyze progress and blockers for a specific phase",
                arguments=[
                    {
                        "name": "phase_id",
                        "description": "ID of the phase to analyze",
                        "required": True
                    }
                ]
            )
        ]
        
        return ListPromptsResult(prompts=prompts)
    
    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> GetPromptResult:
        """Get a specific prompt with populated data."""
        try:
            if name == "project_status_report":
                status = self.db.get_project_status()
                include_details = arguments.get("include_details", False)
                
                prompt_text = f"""
# UnMDX Project Status Report

## Overview
- **Total Phases**: {status.total_phases}
- **Completed Phases**: {status.completed_phases}
- **In Progress Phases**: {status.in_progress_phases}
- **Total Tasks**: {status.total_tasks}
- **Completed Tasks**: {status.completed_tasks}
- **Test Cases**: {status.total_test_cases} (Passing: {status.passing_tests}, Failing: {status.failing_tests})

## Recent Activity
{json.dumps([c.dict() for c in status.recent_commits[:5]], indent=2, default=str)}

## Next Milestone
{status.next_milestone.dict() if status.next_milestone else "No upcoming milestones"}
"""
                
                if include_details:
                    phases = self.db.get_all_phases()
                    prompt_text += "\n\n## Phase Details\n"
                    for phase in phases:
                        progress = self.db.get_phase_progress(phase.id)
                        prompt_text += f"\n### {phase.name} ({phase.status})\n"
                        prompt_text += f"- Tasks: {len(progress.tasks)} ({progress.task_completion_rate:.1%} complete)\n"
                        prompt_text += f"- Test Pass Rate: {progress.test_pass_rate:.1%}\n"
                
                return GetPromptResult(
                    description="Current project status report",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=prompt_text)
                        )
                    ]
                )
            
            elif name == "phase_analysis":
                phase_id = arguments.get("phase_id")
                if not phase_id:
                    return GetPromptResult(
                        description="Error: phase_id is required",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(type="text", text="Error: phase_id is required for phase analysis")
                            )
                        ]
                    )
                
                progress = self.db.get_phase_progress(phase_id)
                
                prompt_text = f"""
# Phase Analysis: {progress.phase.name}

## Phase Information
- **Status**: {progress.phase.status}
- **Description**: {progress.phase.description or "No description"}
- **Start Date**: {progress.phase.start_date or "Not set"}
- **End Date**: {progress.phase.end_date or "Not set"}

## Progress Metrics
- **Task Completion Rate**: {progress.task_completion_rate:.1%}
- **Test Pass Rate**: {progress.test_pass_rate:.1%}
- **Total Tasks**: {len(progress.tasks)}

## Task Breakdown
{json.dumps([t.dict() for t in progress.tasks], indent=2, default=str)}

## Recent Commits
{json.dumps([c.dict() for c in progress.related_commits[:5]], indent=2, default=str)}

## Analysis Request
Please analyze this phase data and provide insights on:
1. Current progress and blockers
2. Risk assessment
3. Recommendations for next steps
"""
                
                return GetPromptResult(
                    description=f"Analysis for phase: {progress.phase.name}",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=prompt_text)
                        )
                    ]
                )
            
            else:
                return GetPromptResult(
                    description="Unknown prompt",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=f"Unknown prompt: {name}")
                        )
                    ]
                )
        
        except DatabaseError as e:
            return GetPromptResult(
                description="Database error",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=f"Database error: {e}")
                    )
                ]
            )
    
    async def run(self, read_stream, write_stream):
        """Run the MCP server."""
        async with self.server.run_server(read_stream, write_stream) as context:
            await context.finish()


async def main():
    """Main entry point for the MCP server."""
    import sys
    import os
    
    # Initialize database if needed
    config = MCPServerConfig()
    
    # Ensure database exists
    db_path = Path(config.database_path)
    if not db_path.exists():
        logger.info(f"Database not found at {db_path}, initializing...")
        db = UnMDXDatabase(config.database_path)
        schema_path = Path(__file__).parent.parent.parent / "schema.sql"
        if schema_path.exists():
            db.initialize_database(str(schema_path))
        else:
            logger.warning("Schema file not found, database may not be properly initialized")
    
    # Create and run server
    server = UnMDXMCPServer(config)
    await server.run(sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())