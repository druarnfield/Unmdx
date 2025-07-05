"""
Test suite for the UnMDX MCP Server.
"""

import asyncio
import json
import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import os

from unmdx_tracker.mcp_server import UnMDXMCPServer, MCPServerConfig
from unmdx_tracker.database import UnMDXDatabase
from unmdx_tracker.models import CreatePhaseRequest, CreateTaskRequest, CreateTestCaseRequest


@pytest.fixture
async def test_server():
    """Create a test MCP server with temporary database."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db_path = f.name
    
    try:
        # Setup server
        config = MCPServerConfig(database_path=test_db_path)
        
        # Initialize database
        db = UnMDXDatabase(test_db_path)
        schema_path = Path(__file__).parent.parent / "schema.sql"
        db.initialize_database(str(schema_path))
        
        # Create test data
        phase_request = CreatePhaseRequest(
            name="Test Phase",
            description="A test phase for MCP server testing",
            status="in_progress"
        )
        phase = db.create_phase(phase_request)
        
        task_request = CreateTaskRequest(
            phase_id=phase.id,
            description="Test task for MCP server",
            priority="high",
            status="in_progress"
        )
        task = db.create_task(task_request)
        
        test_case_request = CreateTestCaseRequest(
            name="Test Case 1",
            description="A test case for MCP server testing",
            test_type="unit",
            status="not_run"
        )
        test_case = db.create_test_case(test_case_request)
        
        # Create server
        server = UnMDXMCPServer(config)
        
        yield server, phase, task, test_case
        
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)


@pytest.mark.asyncio
async def test_list_tools(test_server):
    """Test listing available tools."""
    server, _, _, _ = test_server
    
    result = await server._list_tools()
    assert len(result.tools) == 13
    
    tool_names = [tool.name for tool in result.tools]
    expected_tools = [
        "get_project_status",
        "get_phase_progress", 
        "list_phases",
        "update_phase_status",
        "create_task",
        "update_task_status",
        "list_tasks",
        "record_test_result",
        "get_test_summary",
        "log_commit",
        "get_recent_activity",
        "create_test_case",
        "list_test_cases"
    ]
    
    for expected_tool in expected_tools:
        assert expected_tool in tool_names


@pytest.mark.asyncio
async def test_get_project_status(test_server):
    """Test getting project status."""
    server, _, _, _ = test_server
    
    result = await server._get_project_status()
    assert not result.isError
    
    status_data = json.loads(result.content[0].text)
    assert "total_phases" in status_data
    assert "total_tasks" in status_data
    assert "total_test_cases" in status_data
    assert status_data["total_phases"] >= 1
    assert status_data["total_tasks"] >= 1
    assert status_data["total_test_cases"] >= 1


@pytest.mark.asyncio
async def test_list_phases(test_server):
    """Test listing phases."""
    server, _, _, _ = test_server
    
    result = await server._list_phases()
    assert not result.isError
    
    phases_data = json.loads(result.content[0].text)
    assert len(phases_data) >= 1
    # Find our test phase in the list
    test_phase = next((p for p in phases_data if p["name"] == "Test Phase"), None)
    assert test_phase is not None


@pytest.mark.asyncio
async def test_get_phase_progress(test_server):
    """Test getting phase progress."""
    server, phase, _, _ = test_server
    
    result = await server._get_phase_progress({"phase_id": phase.id})
    assert not result.isError
    
    progress_data = json.loads(result.content[0].text)
    assert "phase" in progress_data
    assert "tasks" in progress_data
    assert "task_completion_rate" in progress_data
    assert progress_data["phase"]["name"] == "Test Phase"


@pytest.mark.asyncio
async def test_list_tasks(test_server):
    """Test listing tasks."""
    server, phase, _, _ = test_server
    
    # Test listing all tasks
    result = await server._list_tasks({})
    assert not result.isError
    
    tasks_data = json.loads(result.content[0].text)
    assert len(tasks_data) >= 1
    
    # Test filtering by phase
    result = await server._list_tasks({"phase_id": phase.id})
    assert not result.isError
    
    phase_tasks_data = json.loads(result.content[0].text)
    assert len(phase_tasks_data) >= 1
    assert phase_tasks_data[0]["phase_id"] == phase.id


@pytest.mark.asyncio
async def test_update_task_status(test_server):
    """Test updating task status."""
    server, _, task, _ = test_server
    
    result = await server._update_task_status({
        "task_id": task.id,
        "status": "completed",
        "notes": "Completed via test"
    })
    assert not result.isError
    
    updated_task = json.loads(result.content[0].text)
    assert updated_task["status"] == "completed"
    assert updated_task["notes"] == "Completed via test"


@pytest.mark.asyncio
async def test_create_task(test_server):
    """Test creating a new task."""
    server, phase, _, _ = test_server
    
    result = await server._create_task({
        "phase_id": phase.id,
        "description": "New test task",
        "priority": "medium",
        "status": "pending"
    })
    assert not result.isError
    
    new_task = json.loads(result.content[0].text)
    assert new_task["description"] == "New test task"
    assert new_task["priority"] == "medium"
    assert new_task["status"] == "pending"


@pytest.mark.asyncio
async def test_list_test_cases(test_server):
    """Test listing test cases."""
    server, _, _, _ = test_server
    
    result = await server._list_test_cases({})
    assert not result.isError
    
    test_cases_data = json.loads(result.content[0].text)
    assert len(test_cases_data) >= 1
    assert test_cases_data[0]["name"] == "Test Case 1"


@pytest.mark.asyncio
async def test_create_test_case(test_server):
    """Test creating a test case."""
    server, _, _, _ = test_server
    
    result = await server._create_test_case({
        "name": "New Test Case",
        "description": "A new test case",
        "test_type": "integration"
    })
    assert not result.isError
    
    new_test_case = json.loads(result.content[0].text)
    assert new_test_case["name"] == "New Test Case"
    assert new_test_case["test_type"] == "integration"


@pytest.mark.asyncio
async def test_record_test_result(test_server):
    """Test recording test results."""
    server, _, _, test_case = test_server
    
    result = await server._record_test_result({
        "test_case_id": test_case.id,
        "status": "passed",
        "duration_ms": 150
        # Note: Not using commit_hash to avoid foreign key constraint issue
    })
    assert not result.isError
    
    execution = json.loads(result.content[0].text)
    assert execution["test_case_id"] == test_case.id
    assert execution["status"] == "passed"
    assert execution["duration_ms"] == 150


@pytest.mark.asyncio
async def test_get_test_summary(test_server):
    """Test getting test summary."""
    server, _, _, test_case = test_server
    
    # First record a test result
    await server._record_test_result({
        "test_case_id": test_case.id,
        "status": "passed",
        "duration_ms": 100
    })
    
    result = await server._get_test_summary({
        "test_case_id": test_case.id,
        "limit": 5
    })
    assert not result.isError
    
    summary = json.loads(result.content[0].text)
    assert "test_case" in summary
    assert "recent_executions" in summary
    assert "success_rate" in summary
    assert len(summary["recent_executions"]) >= 1


@pytest.mark.asyncio
async def test_list_resources(test_server):
    """Test listing resources."""
    server, _, _, _ = test_server
    
    result = await server._list_resources()
    assert len(result.resources) == 5
    
    resource_uris = [str(resource.uri) for resource in result.resources]
    expected_uris = [
        "unmdx://phases",
        "unmdx://tasks/all",
        "unmdx://tests/summary",
        "unmdx://commits/recent",
        "unmdx://status/overview"
    ]
    
    for expected_uri in expected_uris:
        assert expected_uri in resource_uris


@pytest.mark.asyncio
async def test_read_resources(test_server):
    """Test reading various resources."""
    server, _, _, _ = test_server
    
    # Test reading phases resource
    result = await server._read_resource("unmdx://phases")
    assert len(result.contents) == 1
    assert result.contents[0].mimeType == "application/json"
    
    # Test reading status overview
    result = await server._read_resource("unmdx://status/overview")
    assert len(result.contents) == 1
    assert result.contents[0].mimeType == "application/json"
    
    # Test reading unknown resource
    result = await server._read_resource("unmdx://unknown")
    assert len(result.contents) == 1
    assert "Unknown resource" in result.contents[0].text


@pytest.mark.asyncio
async def test_list_prompts(test_server):
    """Test listing prompts."""
    server, _, _, _ = test_server
    
    result = await server._list_prompts()
    assert len(result.prompts) == 2
    
    prompt_names = [prompt.name for prompt in result.prompts]
    assert "project_status_report" in prompt_names
    assert "phase_analysis" in prompt_names


@pytest.mark.asyncio
async def test_get_prompts(test_server):
    """Test getting prompts."""
    server, phase, _, _ = test_server
    
    # Test project status report prompt
    result = await server._get_prompt("project_status_report", {"include_details": True})
    assert result.description == "Current project status report"
    assert len(result.messages) == 1
    assert "UnMDX Project Status Report" in result.messages[0].content.text
    
    # Test phase analysis prompt
    result = await server._get_prompt("phase_analysis", {"phase_id": phase.id})
    assert result.description == f"Analysis for phase: {phase.name}"
    assert len(result.messages) == 1
    assert "Phase Analysis" in result.messages[0].content.text


@pytest.mark.asyncio
async def test_error_handling(test_server):
    """Test error handling in tools."""
    server, _, _, _ = test_server
    
    # Test invalid phase ID
    result = await server._get_phase_progress({"phase_id": 99999})
    assert result.isError
    assert "Database error" in result.content[0].text
    
    # Test missing required parameters
    result = await server._update_task_status({"task_id": 1})  # Missing status
    assert result.isError
    assert "task_id and status are required" in result.content[0].text
    
    # Test unknown tool
    result = await server._call_tool("unknown_tool", {})
    assert result.isError
    assert "Unknown tool" in result.content[0].text