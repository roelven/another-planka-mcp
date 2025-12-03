# Planka MCP Server - Implementation Plan

## Overview

This document outlines the comprehensive plan for building a high-quality MCP server for the Planka kanban project management platform. The server will enable LLMs to interact with your self-hosted Planka instance at `https://planka.w22.io/` through well-designed workflow-oriented tools.

**Implementation Language**: Python (using FastMCP)
**Target Planka Instance**: https://planka.w22.io/
**Server Name**: `planka_mcp`

### Token Efficiency Focus

This implementation prioritizes **token efficiency** for AI agents through:
- **Workspace caching**: Single call to get complete workspace structure (50-66% token reduction)
- **Smart detail levels**: Preview/summary/detailed modes (60-88% reduction for browsing)
- **Response context modes**: Minimal/standard/full (30-60% reduction on repeated calls)
- **Composite tools**: Combined operations to reduce round trips (30-40% reduction)
- **Aggressive caching**: Low-concurrency environment enables 60-70% reduction in API calls

**Expected Results**: 50-60% token reduction, 60-70% fewer API calls compared to naive implementation.

See `TOKEN_EFFICIENCY_ANALYSIS.md` for detailed projections.

---

## Phase 1: Deep Research and Planning

### 1.1 Planka API Overview

Planka is an open-source kanban board project management tool (similar to Trello). The API provides comprehensive endpoints for managing:

- **Authentication**: Access tokens, OIDC integration, API keys
- **Users**: User management, profiles, avatars
- **Projects**: Project creation, managers, background images, custom field groups
- **Boards**: Board creation, memberships, labels, activity tracking
- **Lists**: List management, card organization, sorting
- **Cards**: Core entity with descriptions, members, labels, tasks, attachments, comments
- **Tasks**: Task lists and individual tasks within cards
- **Attachments**: File uploads and downloads
- **Comments**: Card discussions
- **Notifications**: User notifications and notification services
- **Webhooks**: External integrations
- **Custom Fields**: Flexible metadata for boards and cards

### 1.2 Tool Selection Strategy

Following the principle of "Build for Workflows, Not Just API Endpoints," we'll focus on tools that enable complete tasks rather than simple API wrappers. The tools are organized into priority tiers, with token efficiency as a primary design consideration.

#### **Tier 0: Context & Discovery Tools** (CRITICAL - Implement First)
These tools provide massive token savings by reducing discovery overhead:

1. **`planka_get_workspace`** ⭐ **[NEW - CRITICAL]** - Get complete workspace structure
   - **Token Impact**: Replaces 3-4 calls, saves 50-66% on discovery
   - Returns: All projects, boards, lists, labels, and users in one call
   - Cached: 5 minutes (90%+ hit rate in conversations)
   - Workflow: "What's available?" → Agent now has all IDs and structure
   - Example: Creating a card drops from 3,500 tokens (4 calls) → 1,200 tokens (2 calls)

#### **Tier 1: Core Workflow Tools** (High Priority)
Essential tools with token optimization built-in:

2. **`planka_list_cards`** - List cards with smart detail levels and cross-list filtering
   - **Token Optimization**: Supports `detail_level` (preview/summary/detailed) and `response_context` (minimal/standard/full)
   - **Token Impact**: 60-88% reduction when using preview mode for browsing
   - **Cross-list support**: `list_id=None` returns cards from ALL lists in one call
   - **Label filtering**: `label_filter` parameter to filter by label name (e.g., "In Progress")
   - Enables: Card discovery, status overview, finding all cards with specific labels
   - Workflow: "Show me all In Progress cards" (across all lists) → ONE efficient call
   - Supports: Filtering by list, label filtering, pagination, flexible detail control

3. **`planka_find_and_get_card`** ⭐ **[NEW - Composite Tool]** - Combined search + get details
   - **Token Impact**: Saves 37% tokens, eliminates 1 round trip
   - Combines: Search for card + get full details in one operation
   - Workflow: "Find the login bug card and show details" → Single call instead of 2
   - Returns: Complete card details if unique match, or list of options if ambiguous

4. **`planka_get_card`** - Get complete card details with context control
   - **Token Optimization**: Supports `response_context` parameter
   - Enables: Deep card inspection including tasks, members, labels, attachments, comments
   - Workflow: "Show me everything about this card"
   - Returns: Full card data with related entities (context-aware)

5. **`planka_create_card`** - Create a new card
   - Enables: Task creation workflow
   - Workflow: "Create a card for this new task"
   - Supports: Name, description, position, due date
   - Returns: Minimal confirmation (reduces response tokens)

6. **`planka_update_card`** - Update card details
   - Enables: Card modification (name, description, due date, position, list movement)
   - Workflow: "Update this card's description" or "Move card to different list"
   - Returns: Minimal confirmation (reduces response tokens)

7. **`planka_add_task`** - Add task to a card's checklist
   - Enables: Quick task addition to existing or new task lists
   - Workflow: "Add a task to track progress"
   - Common pattern: Cards with subtasks (seen frequently in user's workflow)

8. **`planka_update_task`** - Update task status (complete/incomplete)
   - Enables: Checking off tasks, tracking progress
   - Workflow: "Mark this task as complete"
   - Returns: Updated task list progress (e.g., "3/5 complete")

#### **Tier 2: Batch & Composite Operations** (Medium Priority - High Efficiency)
Tools for efficient multi-item operations:

9. **`planka_get_board_overview`** ⭐ **[NEW - Composite Tool]** - Board + lists + card counts
   - **Token Impact**: 73% reduction when you just need structure (vs fetching all cards)
   - Returns: Board details, all lists, label definitions, card counts per list
   - Cached: 3 minutes
   - Workflow: "What lists exist and how many cards in each?" → Single efficient call
   - **Use case**: Perfect for user's workflow of seeing category summaries

10. **`planka_get_cards_batch`** ⭐ **[NEW - Batch Tool]** - Get multiple cards at once
    - **Token Impact**: 40% reduction, eliminates 4 round trips when fetching 5 cards
    - Takes: List of card IDs (max 50)
    - Returns: Details for all requested cards
    - Workflow: "Get details for these 5 cards" → 1 call instead of 5

#### **Tier 3: Collaboration & Organization Tools**
Tools for team collaboration and card organization:

11. **`planka_add_card_member`** - Assign user to a card
12. **`planka_remove_card_member`** - Unassign user from a card
13. **`planka_add_card_label`** - Add label to a card
14. **`planka_remove_card_label`** - Remove label from a card
15. **`planka_add_comment`** - Add comment to a card
16. **`planka_list_comments`** - List comments on a card (with caching)

#### **Tier 4: Extended Task Management Tools**
Additional task management capabilities:

17. **`planka_add_task_list`** - Create a task list (checklist) on a card
18. **`planka_delete_task`** - Delete a task from checklist

#### **Tier 5: Advanced Tools** (Lower Priority)
Tools for power users and advanced workflows:

19. **`planka_add_attachment`** - Upload attachment to a card
20. **`planka_create_board`** - Create a new board in a project
21. **`planka_create_list`** - Create a new list in a board
22. **`planka_get_board_activity`** - Get recent activity on a board
23. **`planka_get_card_activity`** - Get activity history for a card

### 1.3 Agent-Centric Design Principles Applied

**1. Workflow-Oriented Tools:**
- `planka_get_workspace` eliminates 3-4 discovery calls, providing complete context upfront
- `planka_find_and_get_card` combines search + retrieval in one operation
- `planka_get_board_overview` provides structure without fetching all cards
- `planka_get_cards_batch` fetches multiple cards efficiently
- Composite tools designed around common agent workflows, not just API structure

**2. Optimized for Limited Context (Token Efficiency as Core Design Principle):**
- **Workspace caching**: Complete structure cached for 5 min (90%+ hit rate)
- **Smart detail levels**:
  - `preview` (50 tokens/card): name, list, labels, due date, task progress, comment/attachment counts
  - `summary` (200 tokens/card): + description snippet, member list, creation date
  - `detailed` (400 tokens/card): Everything including full tasks, comments, attachments
- **Cross-list filtering**: Query all lists at once with `list_id=None`
- **Label filtering**: Find all cards with specific label (e.g., "In Progress") across all lists
- **Response context modes**: `minimal` (IDs only), `standard` (IDs + names), `full` (complete)
- **Default response format**: Markdown (human-readable)
- **Optional JSON format**: For programmatic processing
- **Default to names over IDs**: Where practical for human readability
- **Pagination**: Reasonable defaults (20-50 items)
- **Character limit**: 25,000 characters with graceful truncation and actionable guidance

**3. Actionable Error Messages:**
- Authentication errors: "Error: Invalid API credentials. Check your access token or API key in the .env file."
- Not found errors: "Error: Card with ID 'xyz' not found. Verify the card ID is correct and the card exists."
- Permission errors: "Error: You don't have permission to modify this card. You may need to be added as a board member."
- Rate limit errors: "Error: Rate limit exceeded. Wait a moment before trying again."
- All errors guide agents toward resolution

**4. Natural Task Subdivisions:**
- Tool names follow pattern: `planka_{action}_{resource}`
- Grouped by resource type for discoverability
- Action verbs match user intent (get, list, find, create, update, add, remove)
- Composite tools use descriptive names (get_workspace, find_and_get_card)

---

## Phase 2: Implementation Architecture

### 2.1 Project Structure

```
planka-mcp/
├── planka_mcp.py           # Main server implementation
├── README.md               # Setup and usage documentation
├── .env.example            # Example environment variables
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration (optional)
└── evaluations.xml        # Evaluation test cases
```

### 2.2 Core Dependencies

```python
# requirements.txt
mcp[cli]>=1.0.0
pydantic>=2.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
```

### 2.3 Configuration

Environment variables for authentication and configuration:

```bash
# .env
PLANKA_BASE_URL=https://planka.w22.io
PLANKA_API_TOKEN=<access_token>          # Option 1: Access token
# OR
PLANKA_API_KEY=<api_key>                 # Option 2: API key
PLANKA_EMAIL=<email>                      # Required if using API key
PLANKA_PASSWORD=<password>                # Required if using API key
```

Authentication strategy:
1. **Preferred**: Use existing access token (if user has one)
2. **Alternative**: Use API key (generated per-user in Planka)
3. **Fallback**: Email/password authentication (create token on startup)

### 2.4 Shared Utilities & Helpers

#### **API Client Module**

```python
class PlankaAPIClient:
    """Centralized API client for all Planka requests."""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.auth_token = auth_token
        self._client: Optional[httpx.AsyncClient] = None

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request with error handling."""
        pass

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET request helper."""
        pass

    async def post(self, endpoint: str, json_data: Dict) -> Dict:
        """POST request helper."""
        pass

    async def patch(self, endpoint: str, json_data: Dict) -> Dict:
        """PATCH request helper."""
        pass

    async def delete(self, endpoint: str) -> Dict:
        """DELETE request helper."""
        pass
```

#### **Response Formatting Utilities**

```python
class ResponseFormatter:
    """Shared formatting logic for consistent outputs."""

    @staticmethod
    def format_card_markdown(card: Dict, detail_level: str = "summary") -> str:
        """Format card data as readable Markdown."""
        pass

    @staticmethod
    def format_card_json(card: Dict, detail_level: str = "summary") -> str:
        """Format card data as JSON."""
        pass

    @staticmethod
    def format_cards_list_markdown(cards: List[Dict], board_context: Dict) -> str:
        """Format multiple cards as Markdown list."""
        pass

    @staticmethod
    def format_project_markdown(project: Dict) -> str:
        """Format project data as Markdown."""
        pass

    @staticmethod
    def truncate_response(content: str, limit: int = 25000) -> str:
        """Truncate response with helpful message."""
        pass
```

#### **Pagination Helper**

```python
class PaginationHelper:
    """Handles pagination logic consistently."""

    @staticmethod
    def paginate_results(
        items: List[Dict],
        offset: int,
        limit: int,
        total: Optional[int] = None
    ) -> Dict:
        """Return paginated results with metadata."""
        return {
            "items": items[offset:offset + limit],
            "offset": offset,
            "limit": limit,
            "count": len(items[offset:offset + limit]),
            "total": total or len(items),
            "has_more": offset + limit < (total or len(items)),
            "next_offset": offset + limit if offset + limit < (total or len(items)) else None
        }
```

#### **Error Handling**

```python
def handle_api_error(e: Exception) -> str:
    """Consistent, actionable error messages."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return "Error: Invalid API credentials. Check your access token or API key in the .env file."
        elif status == 403:
            return "Error: You don't have permission to access this resource. You may need board membership."
        elif status == 404:
            return "Error: Resource not found. Check that the ID is correct and the resource exists."
        elif status == 429:
            return "Error: Rate limit exceeded. Wait a moment before trying again."
        else:
            return f"Error: API request failed (HTTP {status}). Please try again."
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. The Planka server may be slow or unreachable."
    elif isinstance(e, httpx.ConnectError):
        return "Error: Cannot connect to Planka server. Check the PLANKA_BASE_URL in your .env file."
    return f"Error: Unexpected error - {type(e).__name__}: {str(e)}"
```

### 2.5 Input Validation Models

Using Pydantic v2 for all input validation:

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
from typing import Optional, List
from datetime import datetime

class ResponseFormat(str, Enum):
    """Output format options."""
    MARKDOWN = "markdown"
    JSON = "json"

class DetailLevel(str, Enum):
    """Level of detail in card responses (token optimization)."""
    PREVIEW = "preview"      # Minimal: ID, name, list, due date only (~50 tokens/card)
    SUMMARY = "summary"      # Standard: + members, labels, task progress (~200 tokens/card)
    DETAILED = "detailed"    # Complete: Everything including full tasks, comments (~400 tokens/card)

class ResponseContext(str, Enum):
    """How much context to include in responses (token optimization)."""
    MINIMAL = "minimal"      # IDs only, assume agent has context from workspace
    STANDARD = "standard"    # IDs + names (default, good balance)
    FULL = "full"           # Complete context with all metadata

# Example: Card listing input
class ListCardsInput(BaseModel):
    """Input for listing cards with cross-list and label filtering support."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    board_id: str = Field(
        ...,
        description="Board ID to list cards from (e.g., 'abc123')",
        min_length=1,
        max_length=100
    )
    list_id: Optional[str] = Field(
        None,
        description="Optional: Filter to specific list ID. If None, returns cards from ALL lists (e.g., 'list456')",
        max_length=100
    )
    label_filter: Optional[str] = Field(
        None,
        description="Optional: Filter cards by label name (e.g., 'In Progress', 'Critical'). Case-insensitive partial match.",
        max_length=100
    )
    limit: int = Field(
        default=50,
        description="Maximum number of cards to return (1-100)",
        ge=1,
        le=100
    )
    offset: int = Field(
        default=0,
        description="Number of cards to skip for pagination",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' (human-readable) or 'json' (machine-readable)"
    )
    detail_level: DetailLevel = Field(
        default=DetailLevel.PREVIEW,
        description="Detail level: 'preview' (~50 tok/card), 'summary' (~200 tok/card), 'detailed' (~400 tok/card)"
    )
    response_context: ResponseContext = Field(
        default=ResponseContext.STANDARD,
        description="Context level: 'minimal' (IDs only), 'standard' (IDs+names), 'full' (complete metadata)"
    )

# Example: Card creation input
class CreateCardInput(BaseModel):
    """Input for creating a new card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    list_id: str = Field(
        ...,
        description="List ID where card should be created (e.g., 'list123')",
        min_length=1,
        max_length=100
    )
    name: str = Field(
        ...,
        description="Card name/title (e.g., 'Fix login bug', 'Update documentation')",
        min_length=1,
        max_length=500
    )
    description: Optional[str] = Field(
        None,
        description="Optional: Card description (supports Markdown)",
        max_length=10000
    )
    due_date: Optional[str] = Field(
        None,
        description="Optional: Due date in ISO format (e.g., '2024-12-31T23:59:59Z')",
        pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
    )
    position: Optional[float] = Field(
        None,
        description="Optional: Position in list (lower = higher in list, default: bottom)"
    )

# Similar models for other tools...
```

### 2.6 Tool Annotations

All tools will include proper annotations:

```python
# Read-only tools (list, get, search)
@mcp.tool(
    name="planka_list_cards",
    annotations={
        "title": "List Planka Cards",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)

# Creation tools (create)
@mcp.tool(
    name="planka_create_card",
    annotations={
        "title": "Create Planka Card",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)

# Modification tools (update, add, remove)
@mcp.tool(
    name="planka_update_card",
    annotations={
        "title": "Update Planka Card",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
```

### 2.7 Response Format Design

#### **Detail Levels - Token Optimization**

Three detail levels optimized for different use cases:

**PREVIEW Mode (~50 tokens/card)** - For browsing and filtering:
```json
{
  "id": "card_abc123",
  "name": "Soly / PV anmeldung fixen",
  "list": "W22 TODO'S",
  "labels": ["In Progress"],
  "due_date": null,
  "tasks": "1/2",           // Task progress shown inline
  "comments": 1,            // Comment count (NEW)
  "attachments": 0          // Attachment count (NEW)
}
```

**SUMMARY Mode (~200 tokens/card)** - Standard detail level:
```json
{
  "id": "card_abc123",
  "name": "Soly / PV anmeldung fixen",
  "description": "Need to fix PV registration with Soly...",
  "list": {"id": "list_xyz", "name": "W22 TODO'S"},
  "labels": [{"id": "label1", "name": "In Progress", "color": "orange"}],
  "members": [{"id": "user1", "name": "Roel"}],
  "due_date": null,
  "created_at": "2024-02-01T10:00:00Z",
  "tasks": "1/2",
  "comments": 1,
  "attachments": 0
}
```

**DETAILED Mode (~400 tokens/card)** - Complete information:
```json
{
  "id": "card_abc123",
  "name": "Soly / PV anmeldung fixen",
  "description": "Need to fix PV registration with Soly...",
  "list": {"id": "list_xyz", "name": "W22 TODO'S"},
  "labels": [{"id": "label1", "name": "In Progress", "color": "orange"}],
  "members": [{"id": "user1", "name": "Roel", "email": "roel@example.com"}],
  "due_date": null,
  "created_at": "2024-02-01T10:00:00Z",
  "updated_at": "2024-02-04T15:30:00Z",
  "task_lists": [
    {
      "id": "tasklist1",
      "tasks": [
        {"id": "task1", "name": "Contact Soly", "completed": true},
        {"id": "task2", "name": "Submit forms", "completed": false}
      ]
    }
  ],
  "comments": [
    {
      "id": "comment1",
      "text": "Contacted Soly support, waiting for response",
      "user": {"id": "user1", "name": "Roel"},
      "created_at": "2024-02-03T14:20:00Z"
    }
  ],
  "attachments": []
}
```

**Token Impact:**
- Browsing 50 cards: Preview = 2,500 tokens vs Detailed = 20,000+ tokens (88% reduction)
- User's workflow ("show In Progress"): Preview mode perfect for initial scan

#### **Markdown Format (Default)**
Human-readable, optimized for agent context:

```markdown
# Card: Fix Authentication Bug

**ID**: card_abc123
**List**: In Progress (list_xyz789)
**Board**: Backend Development

## Details
- **Status**: In Progress
- **Due Date**: 2024-02-15
- **Created**: 2024-02-01 by @john.doe
- **Members**: @alice, @bob

## Description
The authentication endpoint is returning 500 errors when users try to log in with OAuth. Need to investigate the token validation logic.

## Tasks (2/5 completed)
- [x] Reproduce the bug
- [x] Check server logs
- [ ] Fix token validation
- [ ] Write tests
- [ ] Deploy fix

## Comments (3)
- **@alice** (2024-02-02): I can reproduce this consistently with Google OAuth
- **@bob** (2024-02-03): Looking at the logs, seems like token expiry issue
- **@john.doe** (2024-02-04): Working on fix in PR #123

## Labels
🔴 Critical, 🐛 Bug, 🔧 Backend
```

#### **JSON Format**
Machine-readable for programmatic processing:

```json
{
  "card": {
    "id": "card_abc123",
    "name": "Fix Authentication Bug",
    "description": "The authentication endpoint is returning 500 errors...",
    "position": 1024.5,
    "due_date": "2024-02-15T23:59:59Z",
    "created_at": "2024-02-01T10:30:00Z",
    "updated_at": "2024-02-04T15:45:00Z",
    "list": {
      "id": "list_xyz789",
      "name": "In Progress"
    },
    "board": {
      "id": "board_123",
      "name": "Backend Development"
    },
    "members": [
      {"id": "user1", "name": "Alice Smith", "username": "alice"},
      {"id": "user2", "name": "Bob Jones", "username": "bob"}
    ],
    "labels": [
      {"id": "label1", "name": "Critical", "color": "red"},
      {"id": "label2", "name": "Bug", "color": "orange"},
      {"id": "label3", "name": "Backend", "color": "blue"}
    ],
    "task_lists": [
      {
        "id": "tasklist1",
        "name": "Tasks",
        "tasks": [
          {"id": "task1", "name": "Reproduce the bug", "completed": true},
          {"id": "task2", "name": "Check server logs", "completed": true},
          {"id": "task3", "name": "Fix token validation", "completed": false},
          {"id": "task4", "name": "Write tests", "completed": false},
          {"id": "task5", "name": "Deploy fix", "completed": false}
        ]
      }
    ],
    "comments": [
      {
        "id": "comment1",
        "text": "I can reproduce this consistently with Google OAuth",
        "user": {"id": "user1", "name": "Alice Smith"},
        "created_at": "2024-02-02T14:20:00Z"
      }
    ],
    "attachments_count": 2
  }
}
```

### 2.8 Character Limits & Truncation

```python
CHARACTER_LIMIT = 25000

def check_and_truncate(content: str) -> str:
    """Truncate response if over limit."""
    if len(content) <= CHARACTER_LIMIT:
        return content

    # Truncate at approximately 60% of limit to leave room for truncation message
    truncate_at = int(CHARACTER_LIMIT * 0.6)
    truncated = content[:truncate_at]

    # Try to truncate at a natural boundary (newline)
    last_newline = truncated.rfind('\n')
    if last_newline > truncate_at * 0.8:  # If within last 20%
        truncated = truncated[:last_newline]

    warning = f"""

---
⚠️ **RESPONSE TRUNCATED**: Output was {len(content):,} characters (limit: {CHARACTER_LIMIT:,})

**To see more results:**
- Use pagination: Increase `offset` parameter
- Add filters: Use `list_id` to filter to specific list
- Reduce detail: Use `detail_level="summary"` instead of "detailed"
---
"""

    return truncated + warning
```

---

## Phase 3: Implementation Details

### 3.1 Core Tool Implementations

#### Example: `planka_list_cards`

```python
@mcp.tool(
    name="planka_list_cards",
    annotations={
        "title": "List Planka Cards",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def planka_list_cards(params: ListCardsInput) -> str:
    '''List cards from a Planka board, optionally filtered by list.

    This tool retrieves cards from a specific board in your Planka instance. You can filter
    to a specific list within the board, control pagination, and choose the response format
    and detail level. Use this to see what cards exist, their current status, and basic information.

    Args:
        params (ListCardsInput): Validated input parameters containing:
            - board_id (str): The board ID to query (required)
            - list_id (Optional[str]): Optional list ID filter
            - limit (int): Max cards to return (1-100, default: 50)
            - offset (int): Pagination offset (default: 0)
            - response_format (ResponseFormat): "markdown" or "json" (default: "markdown")
            - detail_level (DetailLevel): "summary" or "detailed" (default: "summary")

    Returns:
        str: Formatted card list in requested format (Markdown or JSON)

    Examples:
        - "Show me all In Progress cards" → Use board_id="board_123", label_filter="In Progress", list_id=None
        - "What cards are in the HOMELAB list?" → Use board_id="board_123", list_id="homelab_list_id"
        - "Show all cards across all lists" → Use board_id="board_123", list_id=None
        - "Find Critical bugs in FINANCE" → Use board_id="board_123", list_id="finance_list_id", label_filter="Critical"
        - "List the next 50 cards" → Use offset=50, limit=50

    Error Handling:
        - Returns clear error if board_id not found
        - Returns empty result message if no cards match filters
        - Label filtering is case-insensitive partial match
        - Automatically truncates if response exceeds character limit
    '''
    try:
        # Get board data first for context
        board = await api_client.get(f"boards/{params.board_id}")

        # Get all lists for this board
        # Note: Planka API structure may require fetching board data which includes lists and cards
        # Adjust based on actual API response structure

        # Get cards (implementation depends on API structure)
        cards = await api_client.get(f"boards/{params.board_id}/cards")

        # Filter by list if specified (None = all lists)
        if params.list_id:
            cards = [c for c in cards if c.get('list_id') == params.list_id]

        # Filter by label if specified (case-insensitive partial match)
        if params.label_filter:
            label_lower = params.label_filter.lower()
            cards = [
                c for c in cards
                if any(label_lower in label.get('name', '').lower()
                       for label in c.get('labels', []))
            ]

        # Paginate
        paginated = PaginationHelper.paginate_results(
            cards,
            params.offset,
            params.limit
        )

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            content = ResponseFormatter.format_cards_list_markdown(
                paginated["items"],
                board,
                params.detail_level
            )
        else:
            content = json.dumps({
                "board": {
                    "id": board["id"],
                    "name": board["name"]
                },
                "cards": paginated["items"],
                "pagination": {
                    "offset": paginated["offset"],
                    "limit": paginated["limit"],
                    "count": paginated["count"],
                    "total": paginated["total"],
                    "has_more": paginated["has_more"],
                    "next_offset": paginated["next_offset"]
                }
            }, indent=2)

        # Check character limit
        return check_and_truncate(content)

    except Exception as e:
        return handle_api_error(e)
```

### 3.2 Authentication Strategy

```python
async def initialize_auth() -> str:
    """Initialize authentication and return access token."""
    load_dotenv()

    base_url = os.getenv("PLANKA_BASE_URL")
    if not base_url:
        raise ValueError("PLANKA_BASE_URL not set in environment")

    # Option 1: Use existing access token
    token = os.getenv("PLANKA_API_TOKEN")
    if token:
        return token

    # Option 2: Use API key (if user has generated one)
    api_key = os.getenv("PLANKA_API_KEY")
    if api_key:
        # API key can be used directly as Bearer token
        return api_key

    # Option 3: Authenticate with email/password
    email = os.getenv("PLANKA_EMAIL")
    password = os.getenv("PLANKA_PASSWORD")
    if email and password:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/access-tokens",
                json={"emailOrUsername": email, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            return data["item"]["accessToken"]

    raise ValueError(
        "No authentication method configured. Set one of: "
        "PLANKA_API_TOKEN, PLANKA_API_KEY, or PLANKA_EMAIL+PLANKA_PASSWORD"
    )
```

### 3.3 Caching Architecture

**Critical for token efficiency** - Aggressive caching leverages low-concurrency environment:

```python
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CacheEntry:
    """Single cache entry with TTL."""
    data: Any
    timestamp: float
    ttl: int  # seconds

    def is_valid(self) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - self.timestamp < self.ttl

    def is_stale(self) -> bool:
        """Check if cache should be refreshed (80% of TTL)."""
        age = time.time() - self.timestamp
        return age > (self.ttl * 0.8)

class PlankaCache:
    """Multi-tier caching system optimized for low-concurrency environment.

    Cache TTLs optimized for typical Planka usage patterns:
    - Workspace structure changes infrequently (5 min)
    - Labels rarely change (10 min)
    - Users added occasionally (5 min)
    - Board overviews moderately dynamic (3 min)
    - Card details highly dynamic (1 min)
    """

    def __init__(self):
        # Workspace structure (projects, boards, lists, labels, users)
        self.workspace: Optional[CacheEntry] = None

        # Per-board label caches {board_id: CacheEntry}
        self.board_labels: Dict[str, CacheEntry] = {}

        # User list cache
        self.users: Optional[CacheEntry] = None

        # Board overview caches {board_id: CacheEntry}
        self.board_overviews: Dict[str, CacheEntry] = {}

        # Per-card detail caches {card_id: CacheEntry}
        self.card_details: Dict[str, CacheEntry] = {}

        # Statistics for monitoring
        self.stats = {
            "workspace_hits": 0,
            "workspace_misses": 0,
            "board_overview_hits": 0,
            "board_overview_misses": 0,
            "card_hits": 0,
            "card_misses": 0,
        }

    async def get_workspace(self, fetch_func) -> Dict:
        """Get workspace structure (projects, boards, lists, labels, users).

        TTL: 5 minutes (workspace structure changes infrequently)
        Expected hit rate: 90%+
        """
        if self.workspace and self.workspace.is_valid():
            self.stats["workspace_hits"] += 1
            return self.workspace.data

        self.stats["workspace_misses"] += 1
        data = await fetch_func()
        self.workspace = CacheEntry(data=data, timestamp=time.time(), ttl=300)
        return data

    async def get_board_overview(self, board_id: str, fetch_func) -> Dict:
        """Get board overview (board + lists + label defs + card counts).

        TTL: 3 minutes (moderate change rate)
        Expected hit rate: 70-80%
        """
        if board_id in self.board_overviews:
            entry = self.board_overviews[board_id]
            if entry.is_valid():
                self.stats["board_overview_hits"] += 1
                return entry.data

        self.stats["board_overview_misses"] += 1
        data = await fetch_func()
        self.board_overviews[board_id] = CacheEntry(
            data=data, timestamp=time.time(), ttl=180
        )
        return data

    async def get_card(self, card_id: str, fetch_func) -> Dict:
        """Get card details with short TTL.

        TTL: 1 minute (cards change frequently)
        Expected hit rate: 40-50%
        """
        if card_id in self.card_details:
            entry = self.card_details[card_id]
            if entry.is_valid():
                self.stats["card_hits"] += 1
                return entry.data

        self.stats["card_misses"] += 1
        data = await fetch_func()
        self.card_details[card_id] = CacheEntry(
            data=data, timestamp=time.time(), ttl=60
        )
        return data

    def invalidate_workspace(self):
        """Invalidate workspace cache (call after structural changes)."""
        self.workspace = None

    def invalidate_board(self, board_id: str):
        """Invalidate board overview cache (call after board changes)."""
        if board_id in self.board_overviews:
            del self.board_overviews[board_id]

    def invalidate_card(self, card_id: str):
        """Invalidate card cache (call after card updates)."""
        if card_id in self.card_details:
            del self.card_details[card_id]

    def get_stats(self) -> Dict:
        """Get cache statistics for monitoring."""
        total_workspace = self.stats["workspace_hits"] + self.stats["workspace_misses"]
        total_board = self.stats["board_overview_hits"] + self.stats["board_overview_misses"]
        total_card = self.stats["card_hits"] + self.stats["card_misses"]

        return {
            "workspace": {
                "hits": self.stats["workspace_hits"],
                "misses": self.stats["workspace_misses"],
                "hit_rate": self.stats["workspace_hits"] / total_workspace if total_workspace > 0 else 0,
            },
            "board_overview": {
                "hits": self.stats["board_overview_hits"],
                "misses": self.stats["board_overview_misses"],
                "hit_rate": self.stats["board_overview_hits"] / total_board if total_board > 0 else 0,
            },
            "card": {
                "hits": self.stats["card_hits"],
                "misses": self.stats["card_misses"],
                "hit_rate": self.stats["card_hits"] / total_card if total_card > 0 else 0,
            },
        }

# Global cache instance
cache = PlankaCache()
```

**Cache Invalidation Strategy:**

```python
# After write operations, invalidate related caches
@mcp.tool(name="planka_create_card")
async def planka_create_card(params: CreateCardInput) -> str:
    # Create card via API
    card = await api_client.post("/api/lists/{params.list_id}/cards", ...)

    # Invalidate related caches
    cache.invalidate_board(card['board_id'])  # Board overview has changed
    # Workspace cache doesn't need invalidation (structure unchanged)

    return format_card_minimal(card)

@mcp.tool(name="planka_update_card")
async def planka_update_card(params: UpdateCardInput) -> str:
    # Update card via API
    card = await api_client.patch(f"/api/cards/{params.card_id}", ...)

    # Invalidate card cache
    cache.invalidate_card(params.card_id)

    # If card moved to different list, invalidate board
    if params.list_id:
        cache.invalidate_board(card['board_id'])

    return format_card_minimal(card)
```

**Cache Configuration:**

```python
# Module-level cache configuration constants
CACHE_CONFIG = {
    'workspace_ttl': 300,        # 5 min - projects/boards/lists/labels/users
    'board_overview_ttl': 180,   # 3 min - board structure + card counts
    'card_details_ttl': 60,      # 1 min - individual card details
    'users_ttl': 300,            # 5 min - user list (rarely changes)
    'max_card_cache_size': 100,  # Limit memory usage for card cache
}

# Clean up old card cache entries periodically
def cleanup_card_cache():
    """Remove stale entries from card cache to limit memory usage."""
    if len(cache.card_details) > CACHE_CONFIG['max_card_cache_size']:
        # Remove oldest entries
        sorted_entries = sorted(
            cache.card_details.items(),
            key=lambda x: x[1].timestamp
        )
        # Keep only most recent 50
        cache.card_details = dict(sorted_entries[-50:])
```

### 3.4 Module Structure

```python
#!/usr/bin/env python3
"""
Planka MCP Server

Provides tools to interact with Planka kanban boards, enabling LLMs to:
- List and search cards, boards, and projects
- Create and update cards
- Manage card members, labels, tasks, and comments
- View activity and track progress

Optimized for token efficiency with aggressive caching and smart response formatting.

Requires: PLANKA_BASE_URL and authentication credentials in environment.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
import os
import json
import time
import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

# Initialize server
mcp = FastMCP("planka_mcp")

# Constants
CHARACTER_LIMIT = 25000
DEFAULT_TIMEOUT = 30.0
CACHE_CONFIG = {
    'workspace_ttl': 300,
    'board_overview_ttl': 180,
    'card_details_ttl': 60,
    'max_card_cache_size': 100,
}

# Global instances (initialized on startup)
api_client: Optional['PlankaAPIClient'] = None
cache: Optional['PlankaCache'] = None

# [Enums, Models, Utilities, Caching, Tools defined here...]

@mcp.server.on_startup()
async def on_startup():
    """Initialize API client and cache system on server startup."""
    global api_client, cache
    token = await initialize_auth()
    base_url = os.getenv("PLANKA_BASE_URL")
    api_client = PlankaAPIClient(base_url, token)
    cache = PlankaCache()

if __name__ == "__main__":
    mcp.run()
```

---

## Phase 4: Evaluation Strategy

### 4.1 Evaluation Questions (10 Complex, Realistic Scenarios)

Create `evaluations.xml` with questions that test the MCP server's effectiveness:

```xml
<evaluation>
  <qa_pair>
    <question>List all projects in the Planka instance and find the project named "Backend Development". What is the project ID?</question>
    <answer>[PROJECT_ID]</answer>
  </qa_pair>

  <qa_pair>
    <question>In the "Backend Development" project, list all boards. How many boards are there?</question>
    <answer>[NUMBER]</answer>
  </qa_pair>

  <qa_pair>
    <question>Find all cards in the "Sprint Planning" board that are in the "In Progress" list. What is the name of the card with the earliest due date?</question>
    <answer>[CARD_NAME]</answer>
  </qa_pair>

  <qa_pair>
    <question>Search for all cards with "authentication" in their name or description across all boards. How many cards match this search?</question>
    <answer>[NUMBER]</answer>
  </qa_pair>

  <qa_pair>
    <question>Find the card named "Fix Login Bug" and list all its task items. How many tasks are marked as completed?</question>
    <answer>[NUMBER]</answer>
  </qa_pair>

  <qa_pair>
    <question>Look at the "API Development" board and identify which list has the most cards. What is the name of that list?</question>
    <answer>[LIST_NAME]</answer>
  </qa_pair>

  <qa_pair>
    <question>Find the card with the most comments in the "Customer Feedback" board. What is the card's name?</question>
    <answer>[CARD_NAME]</answer>
  </qa_pair>

  <qa_pair>
    <question>List all cards assigned to user "alice" in the "Q1 Planning" board. How many cards is alice assigned to?</question>
    <answer>[NUMBER]</answer>
  </qa_pair>

  <qa_pair>
    <question>Find all cards with the "Critical" label in the "Bug Tracker" board. What is the total number of critical bugs?</question>
    <answer>[NUMBER]</answer>
  </qa_pair>

  <qa_pair>
    <question>In the "Infrastructure" board, find the card with the longest description (most characters). What is the name of that card?</question>
    <answer>[CARD_NAME]</answer>
  </qa_pair>
</evaluation>
```

Note: Actual answers will be determined after implementation by running these queries against the real Planka instance.

### 4.2 Evaluation Requirements

Each evaluation question:
- ✅ Is independent (doesn't depend on other questions)
- ✅ Uses read-only operations only (no destructive changes)
- ✅ Requires multiple tool calls (complex exploration)
- ✅ Is realistic (based on real use cases)
- ✅ Has verifiable answer (can be checked programmatically)
- ✅ Should be stable (answer won't change frequently)

---

## Phase 5: Documentation & Setup

### 5.1 README.md Structure

```markdown
# Planka MCP Server

Model Context Protocol (MCP) server for interacting with Planka kanban boards.

## Features

- 📋 List and search cards, boards, and projects
- ✏️ Create and update cards
- 👥 Manage card members and assignments
- 🏷️ Add and remove labels
- ✅ Manage tasks and checklists
- 💬 View and add comments
- 📎 List attachments
- 🔍 Search across boards

## Installation

### Prerequisites
- Python 3.10+
- Access to a Planka instance
- Planka API credentials (token, API key, or email/password)

### Setup

1. Clone this repository or download the files

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Planka instance URL and credentials
   ```

4. Test the server:
   ```bash
   python planka_mcp.py --help
   ```

## Configuration

Create a `.env` file with your Planka instance details:

```bash
# Required
PLANKA_BASE_URL=https://planka.example.com

# Authentication (choose one method)

# Option 1: Access Token (recommended)
PLANKA_API_TOKEN=your-access-token-here

# Option 2: API Key
PLANKA_API_KEY=your-api-key-here

# Option 3: Email/Password (least secure, will generate token)
PLANKA_EMAIL=your-email@example.com
PLANKA_PASSWORD=your-password
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP settings:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "planka": {
      "command": "python",
      "args": ["/absolute/path/to/planka_mcp.py"],
      "env": {
        "PLANKA_BASE_URL": "https://planka.w22.io",
        "PLANKA_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Available Tools

### Read-Only Tools
- `planka_list_projects` - List all accessible projects
- `planka_list_boards` - List boards in a project
- `planka_list_cards` - List cards with filtering and pagination
- `planka_get_card` - Get complete card details
- `planka_search_cards` - Search for cards by name/description
- `planka_list_labels` - List available labels for a board
- `planka_list_comments` - List comments on a card
- `planka_list_users` - List all users

### Write Tools
- `planka_create_card` - Create a new card
- `planka_update_card` - Update card details
- `planka_add_card_member` - Assign user to card
- `planka_remove_card_member` - Unassign user from card
- `planka_add_card_label` - Add label to card
- `planka_remove_card_label` - Remove label from card
- `planka_add_comment` - Add comment to card
- `planka_add_task_list` - Create task list on card
- `planka_add_task` - Add task to task list
- `planka_update_task` - Update task (complete/incomplete)

## Examples

### Example 1: Find and update a card
```
User: "Find the card about fixing the login bug and add a comment saying I'm working on it"

Assistant uses:
1. planka_search_cards(query="login bug")
2. planka_add_comment(card_id="...", text="I'm working on it")
```

### Example 2: Create a new task
```
User: "Create a new card in the 'To Do' list called 'Update API documentation'"

Assistant uses:
1. planka_list_boards() to find board
2. planka_list_cards(board_id="...") to find "To Do" list
3. planka_create_card(list_id="...", name="Update API documentation")
```

## Development

Run the MCP Inspector for testing:

```bash
npx @modelcontextprotocol/inspector python planka_mcp.py
```

## Troubleshooting

### Authentication Errors
- Verify your credentials in `.env`
- Check that your Planka instance is accessible
- Ensure your API token hasn't expired

### Connection Errors
- Verify `PLANKA_BASE_URL` is correct
- Check network connectivity to Planka instance
- Ensure Planka instance is running

## License

MIT License - see LICENSE file
```

---

## Implementation Priority & Scope

### Phase 1 (MVP) - Token-Optimized Core Tools
Focus on the most impactful tools with built-in token optimizations:

**Tier 0 - Critical (MUST IMPLEMENT FIRST):**
1. ✅ **`planka_get_workspace`** - Single biggest token saver (50-66% reduction)
2. ✅ **Caching system** - Infrastructure for workspace, labels, users (60-70% API call reduction)

**Tier 1 - Core Workflow:**
3. ✅ **`planka_list_cards`** - With detail_level (preview/summary/detailed), response_context, label_filter, and cross-list support
4. ✅ **`planka_find_and_get_card`** - Composite search + get (37% token savings)
5. ✅ **`planka_get_card`** - With response_context parameter
6. ✅ **`planka_create_card`** - Minimal response
7. ✅ **`planka_update_card`** - Minimal response
8. ✅ **`planka_add_task`** - Add tasks to checklist (heavily used in user's workflow)
9. ✅ **`planka_update_task`** - Mark tasks complete/incomplete

**MVP Capabilities:**
- Complete workspace discovery in 1 call (instead of 3-4)
- Efficient card browsing with preview mode (60-88% token reduction)
- Cross-list queries: Find all "In Progress" cards in one call
- Label filtering: Filter by label name across all lists
- Search and retrieve in single operation (37% savings)
- Full CRUD operations on cards
- Task management (add/update tasks on cards)
- Smart caching reduces repeated API calls by 60-70%

**Expected MVP Performance:**
- Create a card: 1,200 tokens (vs 3,500 naive)
- Find all "In Progress" cards: ~800 tokens preview mode (vs 6,000+ querying each list)
- Find and comment on card: 2,200-3,200 tokens (vs 5,000 naive)
- Browse 50 cards: ~2,500 tokens preview mode (vs 20,000+ detailed)
- **Overall: 50-60% token reduction compared to naive implementation**

### Phase 2 (Efficiency Boost) - Add Tier 2 Composite Tools
8. `planka_get_board_overview` - Board structure without all cards (73% reduction)
9. `planka_get_cards_batch` - Multi-card retrieval (40% reduction, 80% fewer calls)

### Phase 3 (Extended) - Add Tier 3 & 4 Tools
Add collaboration, organization, and task management tools once core MVP is proven.

### Phase 4 (Complete) - Add Tier 5 Tools
Add advanced features for power users.

---

## Success Criteria

The Planka MCP server will be considered successful when:

### **Core Functionality**
1. ✅ All Phase 1 tools are implemented and working (Tier 0 + Tier 1)
2. ✅ Tools follow agent-centric design principles
3. ✅ Comprehensive docstrings with explicit type information
4. ✅ Proper error handling with actionable messages
5. ✅ All Pydantic models use proper v2 syntax with Field() descriptions
6. ✅ Tool annotations correctly set for all tools

### **Token Efficiency** (Critical Differentiator)
7. ✅ `planka_get_workspace` returns complete workspace structure in one call
8. ✅ Caching system implemented with 5min workspace cache, 3min board cache, 1min card cache
9. ✅ Smart detail levels: `preview`, `summary`, `detailed` with documented token usage
10. ✅ Response context modes: `minimal`, `standard`, `full`
11. ✅ Composite tools: `planka_find_and_get_card` combines operations
12. ✅ Cache invalidation after write operations

### **Response Quality**
13. ✅ Support for both Markdown and JSON response formats
14. ✅ Pagination implemented for list operations
15. ✅ Character limit enforcement (25,000) with graceful truncation
16. ✅ Actionable truncation messages guide agents to use filters/pagination

### **Testing & Documentation**
17. ✅ README documentation is complete with token efficiency benefits highlighted
18. ✅ Evaluation questions defined and answers verified
19. ✅ Server runs successfully and can be tested with MCP Inspector
20. ✅ Cache statistics available for monitoring performance

### **Performance Targets** (vs naive implementation)
21. ✅ 50-60% reduction in token usage for typical workflows
22. ✅ 60-70% reduction in API calls due to caching
23. ✅ 90%+ cache hit rate for workspace queries in multi-turn conversations
24. ✅ <1,500 tokens for card creation workflow (vs 3,500 naive)

---

## Next Steps

1. Review this plan and confirm approach
2. Begin Phase 1 implementation (Tier 1 tools only)
3. Test each tool incrementally with MCP Inspector
4. Create evaluation questions based on real data
5. Iterate based on evaluation results
6. Expand to Phase 2 (Tier 2 & 3 tools) if needed

---

## References

- [Planka API Routes](https://github.com/plankanban/planka/blob/master/server/config/routes.js)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/llms-full.txt)
- [MCP Best Practices](mcp-builder skill reference)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md)

---

**Sources:**
- [GitHub - plankanban/planka](https://github.com/plankanban/planka)
- [Planka API Routes Config](https://github.com/plankanban/planka/blob/master/server/config/routes.js)
- [PHP | PLANKA Docs](https://docs.planka.cloud/docs/api-reference/php/)
- [Creating a new card by REST API · Issue #266](https://github.com/plankanban/planka/issues/266)
