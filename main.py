#!/usr/bin/env python3
"""
Planka MCP Server - Bridge file for backward compatibility
"""
# Import all the tool functions from the new modular structure
# This file maintains the original API for backward compatibility
from planka_mcp.server import app

# This file serves as a bridge to maintain backward compatibility
# while the codebase is refactored into modular components in src/planka_mcp/

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)