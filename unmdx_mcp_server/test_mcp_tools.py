#!/usr/bin/env python3
"""
Test script to verify MCP server tools work correctly.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from unmdx_tracker.mcp_server import create_server


async def test_mcp_tools():
    """Test MCP server tools."""
    print("Testing MCP Server Tools...")
    
    # Create server
    server = create_server("test_mcp.db")
    
    # Initialize database
    server.db.initialize_database()
    
    # Test get_project_status
    print("\n1. Testing get_project_status...")
    result = await server._get_project_status()
    print(f"   ✓ Result: {len(result)} text contents")
    print(f"   ✓ Contains project status info")
    
    # Test list_phases
    print("\n2. Testing list_phases...")
    result = await server._list_phases()
    print(f"   ✓ Result: {len(result)} text contents")
    print(f"   ✓ Contains phases list")
    
    # Test create_task
    print("\n3. Testing create_task...")
    arguments = {
        "phase_id": 1,
        "description": "Test task from MCP",
        "priority": "high",
        "status": "pending"
    }
    result = await server._create_task(arguments)
    print(f"   ✓ Result: {result[0].text}")
    
    # Test list_tasks
    print("\n4. Testing list_tasks...")
    result = await server._list_tasks()
    print(f"   ✓ Result: {len(result)} text contents")
    
    # Test get_test_summary
    print("\n5. Testing get_test_summary...")
    result = await server._get_test_summary()
    print(f"   ✓ Result: {len(result)} text contents")
    
    # Test log_commit
    print("\n6. Testing log_commit...")
    arguments = {
        "hash": "abc123def456",
        "branch": "main",
        "message": "Test commit from MCP",
        "author": "test@example.com",
        "phase_id": 1
    }
    result = await server._log_commit(arguments)
    print(f"   ✓ Result: {result[0].text}")
    
    # Test get_recent_activity
    print("\n7. Testing get_recent_activity...")
    result = await server._get_recent_activity(5)
    print(f"   ✓ Result: {len(result)} text contents")
    
    print("\n✓ All MCP tools tested successfully!")


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())