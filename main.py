#!/usr/bin/env python3
"""
Planka MCP Server - Main entry point for MCP protocol

This file now redirects to the dedicated MCP server entry point.
For backward compatibility, it will try to run the MCP server directly.
"""
import os
import sys
import subprocess

def main():
    """Main entry point that redirects to the MCP server."""
    try:
        # Try to run the dedicated MCP server
        result = subprocess.run([
            sys.executable, 
            os.path.join(os.path.dirname(__file__), 'mcp_server.py')
        ], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
    except Exception as e:
        print(f"Failed to start MCP server: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())