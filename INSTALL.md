# Installation Guide

## macOS Installation

### Step 1: Install Dependencies

```bash
cd /Users/roel/Code/another-planka-mcp

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Planka credentials
nano .env
```

Add your Planka instance URL and credentials:
```bash
PLANKA_BASE_URL=https://planka.w22.io
PLANKA_API_TOKEN=your-token-here
```

### Step 3: Test the Server

```bash
# Make sure venv is activated
source venv/bin/activate

# Test the server
python planka_mcp.py
```

Press Ctrl+C to stop the test server.

### Step 4: Configure Claude Desktop

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Option A: Using the shell wrapper (recommended)**
```json
{
  "mcpServers": {
    "planka": {
      "command": "/Users/roel/Code/another-planka-mcp/run_server.sh",
      "args": [],
      "env": {
        "PLANKA_BASE_URL": "https://planka.w22.io",
        "PLANKA_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

**Option B: Using venv python directly**
```json
{
  "mcpServers": {
    "planka": {
      "command": "/Users/roel/Code/another-planka-mcp/venv/bin/python",
      "args": ["/Users/roel/Code/another-planka-mcp/planka_mcp.py"],
      "env": {
        "PLANKA_BASE_URL": "https://planka.w22.io",
        "PLANKA_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

### Step 5: Restart Claude Desktop

Quit Claude Desktop completely and restart it. The Planka MCP server should now connect successfully.

### Troubleshooting

**"ModuleNotFoundError: No module named 'httpx'"**
- Your virtual environment isn't being used
- Make sure you're using Option A or B above, not plain `python3`
- Verify dependencies are installed: `source venv/bin/activate && pip list | grep httpx`

**"spawn ENOENT" error**
- The path to your script is incorrect
- Update the paths in your Claude Desktop config to match your actual installation location

**"Authentication failed"**
- Your API token is invalid or expired
- Generate a new token (see README.md for instructions)
- Verify `PLANKA_BASE_URL` is correct

## Windows Installation

### Step 1: Install Dependencies

```cmd
cd C:\path\to\planka-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```cmd
# Copy example environment file
copy .env.example .env

# Edit .env with your Planka credentials
notepad .env
```

### Step 3: Configure Claude Desktop

Edit: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "planka": {
      "command": "C:\\path\\to\\planka-mcp\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\planka-mcp\\planka_mcp.py"],
      "env": {
        "PLANKA_BASE_URL": "https://planka.w22.io",
        "PLANKA_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Linux Installation

### Step 1: Install Dependencies

```bash
cd /path/to/planka-mcp

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Planka credentials
nano .env
```

### Step 3: Configure Claude Desktop

Edit: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "planka": {
      "command": "/path/to/planka-mcp/venv/bin/python",
      "args": ["/path/to/planka-mcp/planka_mcp.py"],
      "env": {
        "PLANKA_BASE_URL": "https://planka.w22.io",
        "PLANKA_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Verifying Installation

Once Claude Desktop is configured and restarted:

1. Open a new conversation in Claude
2. Look for the hammer icon (🔨) in the input box - this indicates MCP tools are available
3. Ask Claude: "What Planka boards are available?"
4. Claude should use the `planka_get_workspace` tool to fetch your workspace structure

## Quick Reference

**Activate venv (macOS/Linux)**:
```bash
source venv/bin/activate
```

**Activate venv (Windows)**:
```cmd
venv\Scripts\activate
```

**Run server manually for testing**:
```bash
python planka_mcp.py
```

**Run tests**:
```bash
pytest -v
```
