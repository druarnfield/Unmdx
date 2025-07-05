#!/usr/bin/env python3
"""
Startup script for the UnMDX MCP Server.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unmdx_tracker.mcp_server import main


if __name__ == "__main__":
    print("Starting UnMDX MCP Server...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutdown by user")
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)