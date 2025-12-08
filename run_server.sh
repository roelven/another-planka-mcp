#!/bin/bash
# Wrapper script to run Planka MCP server with proper environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists, otherwise use system Python
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    exec python "$SCRIPT_DIR/main.py"
else
    exec python3 "$SCRIPT_DIR/main.py"
fi
