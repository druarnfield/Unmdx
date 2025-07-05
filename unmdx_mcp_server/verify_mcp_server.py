#!/usr/bin/env python3
"""
Verification script for the UnMDX MCP Server.

This script verifies that the MCP server can be imported and initialized correctly.
"""

import sys
from pathlib import Path

# Add src to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

def verify_mcp_server():
    """Verify MCP server can be imported and initialized."""
    
    print("UnMDX MCP Server Verification")
    print("=" * 40)
    
    try:
        # Test imports
        print("✓ Testing imports...")
        from unmdx_tracker.mcp_server import UnMDXMCPServer, MCPServerConfig
        from unmdx_tracker.database import UnMDXDatabase
        from unmdx_tracker.models import CreatePhaseRequest
        print("✓ All imports successful")
        
        # Test configuration
        print("✓ Testing configuration...")
        config = MCPServerConfig(database_path="test_verify.db")
        print(f"✓ Config created: {config.database_path}")
        
        # Test server creation
        print("✓ Testing server creation...")
        server = UnMDXMCPServer(config)
        print("✓ MCP server created successfully")
        
        # Test database operations
        print("✓ Testing database operations...")
        db = UnMDXDatabase("test_verify.db")
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            db.initialize_database(str(schema_path))
            print("✓ Database initialized")
        else:
            print("⚠ Schema file not found, skipping database init")
        
        # Test MCP tools listing
        print("✓ Testing MCP tools...")
        import asyncio
        async def test_tools():
            tools_result = await server._list_tools()
            return len(tools_result.tools)
        
        tool_count = asyncio.run(test_tools())
        print(f"✓ MCP server has {tool_count} tools available")
        
        # Cleanup
        import os
        if os.path.exists("test_verify.db"):
            os.remove("test_verify.db")
        
        print("\n🎉 MCP Server verification successful!")
        print("\nThe server is ready for use. You can start it with:")
        print("  uv run unmdx-mcp-server")
        print("  or")
        print("  uv run python scripts/start_server.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_mcp_server()
    sys.exit(0 if success else 1)