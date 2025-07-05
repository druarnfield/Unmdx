#!/usr/bin/env python3
"""
Test script for the UnMDX MCP Server.

This script tests the MCP server functionality by initializing the database,
creating some test data, and verifying that the tools work correctly.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from unmdx_tracker.mcp_server import UnMDXMCPServer, MCPServerConfig
from unmdx_tracker.database import UnMDXDatabase
from unmdx_tracker.models import CreatePhaseRequest, CreateTaskRequest, CreateTestCaseRequest


async def test_mcp_server():
    """Test the MCP server functionality."""
    
    # Setup test database
    test_db_path = "test_mcp_server.db"
    config = MCPServerConfig(database_path=test_db_path)
    
    # Initialize database
    db = UnMDXDatabase(test_db_path)
    schema_path = Path(__file__).parent / "schema.sql"
    if schema_path.exists():
        db.initialize_database(str(schema_path))
        print("✓ Database initialized")
    else:
        print("✗ Schema file not found")
        return False
    
    # Create test data
    print("\nCreating test data...")
    
    # Create a test phase
    phase_request = CreatePhaseRequest(
        name="Test Phase",
        description="A test phase for MCP server testing",
        status="in_progress"
    )
    phase = db.create_phase(phase_request)
    print(f"✓ Created phase: {phase.name} (ID: {phase.id})")
    
    # Create test tasks
    task_request = CreateTaskRequest(
        phase_id=phase.id,
        description="Test task for MCP server",
        priority="high",
        status="in_progress"
    )
    task = db.create_task(task_request)
    print(f"✓ Created task: {task.description} (ID: {task.id})")
    
    # Create test case
    test_case_request = CreateTestCaseRequest(
        name="Test Case 1",
        description="A test case for MCP server testing",
        test_type="unit",
        status="not_run"
    )
    test_case = db.create_test_case(test_case_request)
    print(f"✓ Created test case: {test_case.name} (ID: {test_case.id})")
    
    # Test MCP server
    print("\nTesting MCP server...")
    server = UnMDXMCPServer(config)
    
    # Test list_tools
    tools_result = await server._list_tools()
    print(f"✓ List tools returned {len(tools_result.tools)} tools")
    
    # Test get_project_status
    status_result = await server._get_project_status()
    if not status_result.isError:
        status_data = json.loads(status_result.content[0].text)
        print(f"✓ Project status: {status_data['total_phases']} phases, {status_data['total_tasks']} tasks")
    else:
        print("✗ Failed to get project status")
        return False
    
    # Test list_phases
    phases_result = await server._list_phases()
    if not phases_result.isError:
        phases_data = json.loads(phases_result.content[0].text)
        print(f"✓ List phases returned {len(phases_data)} phases")
    else:
        print("✗ Failed to list phases")
        return False
    
    # Test get_phase_progress
    progress_result = await server._get_phase_progress({"phase_id": phase.id})
    if not progress_result.isError:
        progress_data = json.loads(progress_result.content[0].text)
        print(f"✓ Phase progress: {progress_data['task_completion_rate']:.1%} completion rate")
    else:
        print("✗ Failed to get phase progress")
        return False
    
    # Test list_tasks
    tasks_result = await server._list_tasks({"phase_id": phase.id})
    if not tasks_result.isError:
        tasks_data = json.loads(tasks_result.content[0].text)
        print(f"✓ List tasks returned {len(tasks_data)} tasks")
    else:
        print("✗ Failed to list tasks")
        return False
    
    # Test update_task_status
    update_result = await server._update_task_status({
        "task_id": task.id,
        "status": "completed",
        "notes": "Completed via MCP server test"
    })
    if not update_result.isError:
        print("✓ Task status updated successfully")
    else:
        print("✗ Failed to update task status")
        return False
    
    # Test list_test_cases
    test_cases_result = await server._list_test_cases({})
    if not test_cases_result.isError:
        test_cases_data = json.loads(test_cases_result.content[0].text)
        print(f"✓ List test cases returned {len(test_cases_data)} test cases")
    else:
        print("✗ Failed to list test cases")
        return False
    
    # Test resources
    resources_result = await server._list_resources()
    print(f"✓ List resources returned {len(resources_result.resources)} resources")
    
    # Test reading a resource
    status_resource = await server._read_resource("unmdx://status/overview")
    if status_resource.contents:
        print("✓ Successfully read status overview resource")
    else:
        print("✗ Failed to read resource")
        return False
    
    # Test prompts
    prompts_result = await server._list_prompts()
    print(f"✓ List prompts returned {len(prompts_result.prompts)} prompts")
    
    # Test getting a prompt
    prompt_result = await server._get_prompt("project_status_report", {"include_details": True})
    if prompt_result.messages:
        print("✓ Successfully generated project status report prompt")
    else:
        print("✗ Failed to generate prompt")
        return False
    
    print("\n✓ All MCP server tests passed!")
    return True


async def main():
    """Main test function."""
    print("UnMDX MCP Server Test")
    print("=" * 30)
    
    try:
        success = await test_mcp_server()
        if success:
            print("\n🎉 All tests passed! MCP server is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())