#!/bin/bash
# Wrapper script to run Planka MCP server with proper environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists, otherwise use system Python
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    #!/bin/bash
    # Check if we should run as web server or MCP server
    if [ "$1" = "web" ]; then
        exec "${VIRTUAL_ENV}/bin/uvicorn" src.planka_mcp.server:app --host 0.0.0.0 --port "${PORT:-8000}"
    else
        exec "${VIRTUAL_ENV}/bin/python" "$SCRIPT_DIR/mcp_server.py"
    fi
else
    exec python3 "$SCRIPT_DIR/main.py"
fi
