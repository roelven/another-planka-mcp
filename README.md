# Another Planka MCP
A Model Context Protocol (MCP) server that enables AI Chat clients to read and update your Planka boards using the Planka REST API.

[![Tests](https://github.com/roelven/another-planka-mcp/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/roelven/another-planka-mcp/actions/workflows/test.yml)

## Overview
Another Planka MCP Server provides you with a lightweight bridge between MCP clients and your self‑hosted Planka instance. It exposes projects, boards, lists, cards, tasks, and labels through MCP tools, allowing assistants to retrieve workspace data and perform write operations such as creating or updating cards.

## Features
- List projects, boards, lists, labels, and members.
- Search and retrieve cards with multiple detail levels.
- Create and update cards (title, description, labels, tasks).
- Move cards between lists.
- Efficient token usage through structured MCP tools.
- Works with Claude Desktop and any MCP‑compatible client.

Example use cases:
- “Show all ‘In Progress’ cards across my workspace.”
- “Create a new card in `<Board> / TODO` with subtasks…”
- “Find the ‘Login bug’ card and list all tasks.”

### Prerequisites
- Python 3.10+
- Access to a Planka instance
- Planka API credentials (see below)

### Obtaining API Credentials

Generate a JWT access token by authenticating via API:

```bash
curl -X POST https://your-planka-instance.com/api/access-tokens \
  -H "Content-Type: application/json" \
  -d '{
    "emailOrUsername": "your-email@example.com",
    "password": "your-password"
  }'
```

**Response:**
```json
{
  "item": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

Copy the `accessToken` value and use it as `PLANKA_API_TOKEN` in your `.env` file.

**Note**: JWT tokens may expire. If you get authentication errors, generate a new token.

#### Email/Password (Fallback)

Use your Planka login credentials directly. The MCP server will authenticate automatically at startup:

```bash
PLANKA_EMAIL=your-email@example.com
PLANKA_PASSWORD=your-password
```

**User Requirements:**
- Any registered Planka user can authenticate
- No special permissions or admin role required
- API access permissions match your Planka user permissions
- Admin users have full access; regular users can only access boards they're members of

### Setup

1. Clone the repo:
   ```
   git clone https://github.com/roelven/another-planka-mcp
   cd another-planka-mcp
   ```
2. Create environment:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy env file:
   ```
   cp .env.example .env
   ```
4. Fill in:
   - `PLANKA_BASE_URL`
   - `PLANKA_API_TOKEN` (recommended)
5. Start the server:
   ```
   python planka_mcp.py
   ```

   **Note**: For direct MCP protocol communication (recommended for Claude Desktop), you can also run:
   ```
   python mcp_server.py
   ```
   
   This provides better compatibility with MCP clients and includes proper protocol handling.

6. Add to Claude Desktop config:
   ```json
   {
     "mcpServers": {
       "planka": {
         "command": "/absolute/path/to/venv/bin/python",
         "args": ["mcp_server.py"],
         "env": {
           "PLANKA_BASE_URL": "https://your.domain",
           "PLANKA_API_TOKEN": "<token>"
         }
       }
     }
   }
   ```

   **Note**: Updated to use `mcp_server.py` for better MCP protocol compatibility.

### Remote Access (Claude.ai via HTTP + OAuth)

For remote access (e.g. Claude.ai through a Cloudflare Tunnel), the server supports streamable HTTP transport with OAuth 2.0 authentication. Only clients with valid credentials can connect.

#### 1. Generate OAuth client credentials

Generate a client ID and secret using Python:

```bash
python -c "import secrets; print(f'MCP_CLIENT_ID={secrets.token_urlsafe(16)}'); print(f'MCP_CLIENT_SECRET={secrets.token_urlsafe(32)}')"
```

This outputs two values. Save them — you'll need them for both the server config and the Claude.ai connector.

#### 2. Configure the server

Add to your `.env`:
```
MCP_TRANSPORT=streamable-http
MCP_SERVER_URL=https://planka-mcp.yourdomain.com
MCP_CLIENT_ID=<generated client ID>
MCP_CLIENT_SECRET=<generated client secret>
```

#### 3. Start the server

```bash
python mcp_server.py
```

The server starts on `0.0.0.0:8000` by default. Expose via Cloudflare Tunnel (or similar) pointing to `localhost:8000`.

#### 4. Configure Claude.ai

In the Claude.ai MCP connector settings:
- **URL**: `https://planka-mcp.yourdomain.com`
- **Client ID**: the `MCP_CLIENT_ID` value from step 1
- **Client Secret**: the `MCP_CLIENT_SECRET` value from step 1

Claude.ai will complete the OAuth authorization code flow and obtain a Bearer token automatically.

#### Rotating credentials

To rotate credentials, generate new values (step 1), update `.env` on the server, restart the container, and update the Claude.ai connector settings to match. Existing tokens are invalidated on restart.

#### Limitations

- **Single client**: The server supports one pre-registered OAuth client. This is sufficient for a single-user setup with one MCP connector (e.g. Claude.ai). Supporting multiple clients would require changes to the registration logic.
- **In-memory tokens**: Tokens are stored in memory. Server restarts invalidate all tokens — Claude.ai will re-authenticate automatically.
- **Auto-approved authorization**: The `/authorize` endpoint auto-approves requests for the registered client. Access control relies on the client credentials being secret. Keep `MCP_CLIENT_SECRET` confidential.

## Tools & Capabilities

| Tool                         | Type   | Purpose                                                |
|-----------------------------|--------|--------------------------------------------------------|
| `planka_get_workspace`      | Read   | Retrieve boards, lists, users, labels                  |
| `planka_list_cards`         | Read   | Filter and list cards with detail levels               |
| `planka_find_and_get_card`  | Read   | Search and fetch a specific card                       |
| `planka_get_card`           | Read   | Get detailed information about a specific card         |
| `planka_create_card`        | Write  | Create a new card                                      |
| `planka_update_card`        | Write  | Update an existing card                                |
| `planka_delete_card`        | Write  | Delete a card                                          |
| `planka_add_task`           | Write  | Add a task to a card                                   |
| `planka_update_task`        | Write  | Update a task's completion status                      |
| `planka_delete_task`        | Write  | Delete a task from a card                              |
| `planka_add_card_label`     | Write  | Add a label to a card                                  |
| `planka_remove_card_label`  | Write  | Remove a label from a card                             |

## Usage Examples
Ask your assistant:

- “List all my boards.”
- “Search for cards mentioning ‘invoice’.”
- “Create a card named ‘App release checklist’ with these subtasks…”
- “Move the ‘Integrate payment API’ card to ‘Done’.”

## Security & Permissions
- The MCP server accesses only what the authenticated Planka user can access.
- API token recommended over email/password.
- Use HTTPS when exposing Planka externally.
- Consider using a dedicated Planka service user with restricted permissions.

## Troubleshooting & FAQ
**401 Unauthorized**  
Check token validity and `.env` configuration.

**Client cannot connect to server**  
Verify:
- correct Python path
- firewall rules
- execution permissions

**No boards or cards returned**  
Confirm the Planka user has workspace access.

## Development Notes

**Editable Installation**: This project uses an editable installation (via `pip install -e .` or the equivalent in the virtual environment), which means the `src` directory is automatically added to your Python path. This eliminates the need to manually set `PYTHONPATH` when running tests or the server.

**Setting up editable mode**: If you need to reinstall the package in editable mode, you can run:
```bash
pip install -e .
```

This creates a `.pth` file in your virtual environment that points to the `src` directory, making all imports work seamlessly.

## Running Tests

The project includes a comprehensive test suite with >90% code coverage.

Since the package is installed in editable mode, you can run tests directly without setting PYTHONPATH:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest --cov=src/planka_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_cards.py -v

# View coverage report
open htmlcov/index.html
```

Alternatively, you can use the virtual environment's pytest directly:
```bash
venv/bin/pytest --cov=src/planka_mcp --cov-report=term-missing
```

### Test with MCP Inspector
```bash
npx @modelcontextprotocol/inspector python planka_mcp.py
```

### Run directly
```bash
python planka_mcp.py
```

## Acknowledgements
- Planka project: https://github.com/plankanban/planka
- Model Context Protocol: https://modelcontextprotocol.io/

## License
MIT License. See `LICENSE`.
