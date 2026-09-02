#!/bin/bash
# Wrapper script to run Planka MCP server with proper environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Activate virtual environment if it exists, otherwise use system Python
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    if [ "$1" = "web" ]; then
        MCP_TRANSPORT=streamable-http exec "${VIRTUAL_ENV}/bin/python" "$SCRIPT_DIR/mcp_server.py"
    else
        exec "${VIRTUAL_ENV}/bin/python" "$SCRIPT_DIR/mcp_server.py"
    fi
else
    exec python3 "$SCRIPT_DIR/mcp_server.py"
fi
