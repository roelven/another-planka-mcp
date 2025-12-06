# Another Planka MCP
A Model Context Protocol (MCP) server that enables AI Chat clients to read and update your Planka boards using the Planka REST API.

---

## Overview
Another Planka MCP Server provides you with a lightweight bridge between MCP clients and your self‑hosted Planka instance. It exposes projects, boards, lists, cards, tasks, and labels through MCP tools, allowing assistants to retrieve workspace data and perform write operations such as creating or updating cards.

---

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

---

## Requirements
- MCP client (Claude Desktop or similar).
- A running Planka instance (HTTP/HTTPS reachable).
- User account with appropriate permissions.
- Python 3.10+.

---

<<<<<<< Updated upstream
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
6. Add to Claude Desktop config:
   ```json
   {
     "mcpServers": {
       "planka": {
         "command": "/absolute/path/to/venv/bin/python",
         "args": ["planka_mcp.py"],
         "env": {
           "PLANKA_BASE_URL": "https://your.domain",
           "PLANKA_API_TOKEN": "<token>"
         }
       }
     }
   }
   ```

---

## Tools & Capabilities

| Tool                         | Type   | Purpose                                                |
|-----------------------------|--------|--------------------------------------------------------|
| `planka_get_workspace`      | Read   | Retrieve boards, lists, users, labels                  |
| `planka_list_cards`         | Read   | Filter and list cards with detail levels               |
| `planka_find_and_get_card`  | Read   | Search and fetch a specific card                       |
| `planka_create_card`        | Write  | Create a new card                                      |
| `planka_update_card`        | Write  | Update an existing card                                |

---

## Usage Examples
Ask your assistant:

- “List all my boards.”
- “Search for cards mentioning ‘invoice’.”
- “Create a card named ‘App release checklist’ with these subtasks…”
- “Move the ‘Integrate payment API’ card to ‘Done’.”

---

## Security & Permissions
- The MCP server accesses only what the authenticated Planka user can access.
- API token recommended over email/password.
- Use HTTPS when exposing Planka externally.
- Consider using a dedicated Planka service user with restricted permissions.

---

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

---

## Contributing
Contributions welcome.

1. Fork the repository
2. Create a feature branch
3. Install dev dependencies
4. Submit a pull request

---

## Running Tests

The project includes a comprehensive test suite with >90% code coverage.

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=planka_mcp --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Test Coverage:**
- 56+ comprehensive tests
- Unit tests for all infrastructure components
- Integration tests with mocked API calls
- Input validation tests for all Pydantic models
- Tests for all 9 tools covering happy paths, errors, and edge cases

### Test with MCP Inspector
```bash
npx @modelcontextprotocol/inspector python planka_mcp.py
```

### Run directly
```bash
python planka_mcp.py
```

## Troubleshooting

### "Cannot connect to Planka server"
- Verify `PLANKA_BASE_URL` is correct in `.env`
- Check network connectivity
- Ensure Planka instance is running

### "Invalid API credentials"
- Check your token/API key in `.env`
- Ensure token hasn't expired
- Try re-authenticating with email/password

### "Resource not found"
- Verify the ID is correct (use `planka_get_workspace` to see all IDs)
- Ensure the resource hasn't been deleted

## License
MIT License. See `LICENSE`.

---

## Acknowledgements
- Planka project: https://github.com/plankanban/planka
- Model Context Protocol: https://modelcontextprotocol.io/


