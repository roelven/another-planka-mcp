#!/usr/bin/env python3
"""
Planka MCP Server - Bridge file for backward compatibility
"""
# Import all the tool functions from the new modular structure
# This file maintains the original API for backward compatibility
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from planka_mcp.server import app

if __name__ == "__main__":
    app.run()