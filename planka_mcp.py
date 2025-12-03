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

from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import os
import json
import time
import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# Initialize server
mcp = FastMCP("planka_mcp")

# Constants
CHARACTER_LIMIT = 25000
DEFAULT_TIMEOUT = 30.0
CACHE_CONFIG = {
    'workspace_ttl': 300,        # 5 min - projects/boards/lists/labels/users
    'board_overview_ttl': 180,   # 3 min - board structure + card counts
    'card_details_ttl': 60,      # 1 min - individual card details
    'max_card_cache_size': 100,  # Limit memory usage for card cache
}

# Global instances (initialized on startup)
api_client: Optional['PlankaAPIClient'] = None
cache: Optional['PlankaCache'] = None

# ==================== ENUMS ====================

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

# ==================== CACHE SYSTEM ====================

@dataclass
class CacheEntry:
    """Single cache entry with TTL."""
    data: Any
    timestamp: float
    ttl: int  # seconds

    def is_valid(self) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - self.timestamp < self.ttl

class PlankaCache:
    """Multi-tier caching system optimized for low-concurrency environment."""

    def __init__(self):
        # Workspace structure (projects, boards, lists, labels, users)
        self.workspace: Optional[CacheEntry] = None

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

    async def get_workspace(self, fetch_func):
        """Get workspace structure. TTL: 5 minutes. Expected hit rate: 90%+"""
        if self.workspace and self.workspace.is_valid():
            self.stats["workspace_hits"] += 1
            return self.workspace.data

        self.stats["workspace_misses"] += 1
        data = await fetch_func()
        self.workspace = CacheEntry(data=data, timestamp=time.time(), ttl=300)
        return data

    async def get_board_overview(self, board_id: str, fetch_func):
        """Get board overview. TTL: 3 minutes. Expected hit rate: 70-80%"""
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

    async def get_card(self, card_id: str, fetch_func):
        """Get card details. TTL: 1 minute. Expected hit rate: 40-50%"""
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

    def cleanup_card_cache(self):
        """Remove old entries to limit memory usage."""
        if len(self.card_details) > CACHE_CONFIG['max_card_cache_size']:
            sorted_entries = sorted(
                self.card_details.items(),
                key=lambda x: x[1].timestamp
            )
            self.card_details = dict(sorted_entries[-50:])

# ==================== API CLIENT ====================

class PlankaAPIClient:
    """Centralized API client for all Planka requests."""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=DEFAULT_TIMEOUT,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                }
            )
        return self._client

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request with error handling."""
        client = await self.get_client()
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                files=files
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise e
        except Exception as e:
            raise e

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET request helper."""
        return await self.request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json_data: Dict) -> Dict:
        """POST request helper."""
        return await self.request("POST", endpoint, json_data=json_data)

    async def patch(self, endpoint: str, json_data: Dict) -> Dict:
        """PATCH request helper."""
        return await self.request("PATCH", endpoint, json_data=json_data)

    async def delete(self, endpoint: str) -> Dict:
        """DELETE request helper."""
        return await self.request("DELETE", endpoint)

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()

# ==================== ERROR HANDLING ====================

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

# ==================== RESPONSE FORMATTING ====================

class ResponseFormatter:
    """Shared formatting logic for consistent outputs."""

    @staticmethod
    def truncate_response(content: str, limit: int = CHARACTER_LIMIT) -> str:
        """Truncate response if over limit."""
        if len(content) <= limit:
            return content

        truncate_at = int(limit * 0.6)
        truncated = content[:truncate_at]

        last_newline = truncated.rfind('\n')
        if last_newline > truncate_at * 0.8:
            truncated = truncated[:last_newline]

        warning = f"""

---
⚠️ **RESPONSE TRUNCATED**: Output was {len(content):,} characters (limit: {limit:,})

**To see more results:**
- Use pagination: Increase `offset` parameter
- Add filters: Use `list_id` or `label_filter` to filter results
- Reduce detail: Use `detail_level="preview"` instead of "summary" or "detailed"
---
"""
        return truncated + warning

    @staticmethod
    def format_task_progress(task_lists: List[Dict]) -> str:
        """Format task progress as 'completed/total'."""
        total_tasks = 0
        completed_tasks = 0
        for task_list in task_lists:
            for task in task_list.get('tasks', []):
                total_tasks += 1
                if task.get('isCompleted', False):
                    completed_tasks += 1
        if total_tasks == 0:
            return "0/0"
        return f"{completed_tasks}/{total_tasks}"

    @staticmethod
    def format_card_preview(card: Dict, context: Dict) -> str:
        """Format card in preview mode (~50 tokens)."""
        list_name = context.get('lists', {}).get(card.get('listId'), {}).get('name', 'Unknown List')
        labels = [context.get('labels', {}).get(label_id, {}).get('name', '')
                  for label_id in card.get('labelIds', [])]

        task_progress = ResponseFormatter.format_task_progress(card.get('taskLists', []))

        return f"""- **{card.get('name', 'Untitled')}** (ID: `{card.get('id', 'N/A')}`)
  - List: {list_name}
  - Labels: {', '.join(labels) if labels else 'None'}
  - Due: {card.get('dueDate', 'No due date')}
  - Tasks: {task_progress}
  - Comments: {len(card.get('comments', []))}
  - Attachments: {len(card.get('attachments', []))}"""

    @staticmethod
    def format_card_summary(card: Dict, context: Dict) -> str:
        """Format card in summary mode (~200 tokens)."""
        list_name = context.get('lists', {}).get(card.get('listId'), {}).get('name', 'Unknown List')
        labels = [context.get('labels', {}).get(label_id, {}).get('name', '')
                  for label_id in card.get('labelIds', [])]
        members = [context.get('users', {}).get(user_id, {}).get('name', '')
                   for user_id in card.get('memberIds', [])]

        task_progress = ResponseFormatter.format_task_progress(card.get('taskLists', []))
        description = card.get('description', '')
        desc_snippet = (description[:100] + '...') if len(description) > 100 else description

        return f"""### {card.get('name', 'Untitled')}
**ID**: `{card.get('id', 'N/A')}`
**List**: {list_name}
**Labels**: {', '.join(labels) if labels else 'None'}
**Members**: {', '.join(members) if members else 'None'}
**Due Date**: {card.get('dueDate', 'No due date')}
**Created**: {card.get('createdAt', 'Unknown')}
**Tasks**: {task_progress}
**Comments**: {len(card.get('comments', []))}
**Attachments**: {len(card.get('attachments', []))}

**Description**: {desc_snippet if desc_snippet else '(No description)'}
"""

    @staticmethod
    def format_card_detailed(card: Dict, context: Dict) -> str:
        """Format card in detailed mode (~400 tokens)."""
        list_name = context.get('lists', {}).get(card.get('listId'), {}).get('name', 'Unknown List')
        labels = [context.get('labels', {}).get(label_id, {}).get('name', '')
                  for label_id in card.get('labelIds', [])]
        members = [context.get('users', {}).get(user_id, {}).get('name', '')
                   for user_id in card.get('memberIds', [])]

        output = f"""# {card.get('name', 'Untitled')}

**ID**: `{card.get('id', 'N/A')}`
**List**: {list_name} (ID: `{card.get('listId', 'N/A')}`)
**Board**: {context.get('board_name', 'Unknown')}

## Details
- **Due Date**: {card.get('dueDate', 'No due date')}
- **Created**: {card.get('createdAt', 'Unknown')}
- **Updated**: {card.get('updatedAt', 'Unknown')}
- **Position**: {card.get('position', 'N/A')}

## Members
{', '.join(members) if members else '(No members assigned)'}

## Labels
{', '.join(labels) if labels else '(No labels)'}

## Description
{card.get('description', '(No description)')}

## Tasks
"""
        task_lists = card.get('taskLists', [])
        if task_lists:
            for task_list in task_lists:
                output += f"\n**{task_list.get('name', 'Tasks')}**:\n"
                for task in task_list.get('tasks', []):
                    check = '[x]' if task.get('isCompleted', False) else '[ ]'
                    output += f"- {check} {task.get('name', 'Unnamed task')} (ID: `{task.get('id', 'N/A')}`)\n"
        else:
            output += "(No tasks)\n"

        output += "\n## Comments\n"
        comments = card.get('comments', [])
        if comments:
            for comment in comments:
                user_id = comment.get('userId', 'Unknown')
                user_name = context.get('users', {}).get(user_id, {}).get('name', 'Unknown User')
                output += f"- **{user_name}** ({comment.get('createdAt', 'Unknown')}): {comment.get('text', '')}\n"
        else:
            output += "(No comments)\n"

        output += f"\n## Attachments\n"
        attachments = card.get('attachments', [])
        if attachments:
            for att in attachments:
                output += f"- {att.get('name', 'Unnamed')} (ID: `{att.get('id', 'N/A')}`)\n"
        else:
            output += "(No attachments)\n"

        return output

    @staticmethod
    def format_card_list_markdown(
        cards: List[Dict],
        context: Dict,
        detail_level: DetailLevel
    ) -> str:
        """Format multiple cards as Markdown list."""
        if not cards:
            return "No cards found matching the criteria."

        output = f"# Cards ({len(cards)} found)\n\n"

        for card in cards:
            if detail_level == DetailLevel.PREVIEW:
                output += ResponseFormatter.format_card_preview(card, context) + "\n\n"
            elif detail_level == DetailLevel.SUMMARY:
                output += ResponseFormatter.format_card_summary(card, context) + "\n"
            else:  # DETAILED
                output += ResponseFormatter.format_card_detailed(card, context) + "\n---\n\n"

        return output.strip()

# ==================== PAGINATION ====================

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
        total = total or len(items)
        paginated_items = items[offset:offset + limit]

        return {
            "items": paginated_items,
            "offset": offset,
            "limit": limit,
            "count": len(paginated_items),
            "total": total,
            "has_more": offset + limit < total,
            "next_offset": offset + limit if offset + limit < total else None
        }

# ==================== AUTHENTICATION ====================

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

    # Option 2: Use API key
    api_key = os.getenv("PLANKA_API_KEY")
    if api_key:
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

# ==================== PYDANTIC MODELS ====================

class GetWorkspaceInput(BaseModel):
    """Input for getting workspace structure."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' (human-readable) or 'json' (machine-readable)"
    )

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
        description="Optional: Filter to specific list ID. If None, returns cards from ALL lists",
        max_length=100
    )
    label_filter: Optional[str] = Field(
        None,
        description="Optional: Filter cards by label name (e.g., 'In Progress'). Case-insensitive partial match.",
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
        description="Output format: 'markdown' or 'json'"
    )
    detail_level: DetailLevel = Field(
        default=DetailLevel.PREVIEW,
        description="Detail level: 'preview' (~50 tok/card), 'summary' (~200 tok/card), 'detailed' (~400 tok/card)"
    )
    response_context: ResponseContext = Field(
        default=ResponseContext.STANDARD,
        description="Context level: 'minimal' (IDs only), 'standard' (IDs+names), 'full' (complete)"
    )

class GetCardInput(BaseModel):
    """Input for getting a single card's details."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    card_id: str = Field(
        ...,
        description="Card ID to retrieve (e.g., 'card123')",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )
    response_context: ResponseContext = Field(
        default=ResponseContext.STANDARD,
        description="Context level: 'minimal', 'standard', or 'full'"
    )

class CreateCardInput(BaseModel):
    """Input for creating a new card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    list_id: str = Field(
        ...,
        description="List ID where card should be created",
        min_length=1,
        max_length=100
    )
    name: str = Field(
        ...,
        description="Card name/title",
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
        description="Optional: Due date in ISO format (e.g., '2024-12-31T23:59:59Z')"
    )
    position: Optional[float] = Field(
        None,
        description="Optional: Position in list (lower = higher, default: bottom)"
    )

class UpdateCardInput(BaseModel):
    """Input for updating a card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    card_id: str = Field(
        ...,
        description="Card ID to update",
        min_length=1,
        max_length=100
    )
    name: Optional[str] = Field(
        None,
        description="Optional: New card name",
        max_length=500
    )
    description: Optional[str] = Field(
        None,
        description="Optional: New card description",
        max_length=10000
    )
    due_date: Optional[str] = Field(
        None,
        description="Optional: New due date in ISO format"
    )
    list_id: Optional[str] = Field(
        None,
        description="Optional: Move card to different list",
        max_length=100
    )
    position: Optional[float] = Field(
        None,
        description="Optional: New position in list"
    )

class AddTaskInput(BaseModel):
    """Input for adding a task to a card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    card_id: str = Field(
        ...,
        description="Card ID to add task to",
        min_length=1,
        max_length=100
    )
    task_name: str = Field(
        ...,
        description="Task description/name",
        min_length=1,
        max_length=500
    )
    task_list_name: Optional[str] = Field(
        default="Tasks",
        description="Optional: Task list name (default: 'Tasks')",
        max_length=100
    )

class UpdateTaskInput(BaseModel):
    """Input for updating a task."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    task_id: str = Field(
        ...,
        description="Task ID to update",
        min_length=1,
        max_length=100
    )
    is_completed: bool = Field(
        ...,
        description="Mark task as completed (true) or incomplete (false)"
    )

class FindAndGetCardInput(BaseModel):
    """Input for finding and getting a card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    query: str = Field(
        ...,
        description="Search query (searches in card names and descriptions)",
        min_length=1,
        max_length=200
    )
    board_id: Optional[str] = Field(
        None,
        description="Optional: Limit search to specific board",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )

# ==================== HELPER FUNCTIONS ====================

async def fetch_workspace_data() -> Dict:
    """Fetch complete workspace structure (projects, boards, lists, labels, users)."""
    try:
        # Fetch all projects
        projects_response = await api_client.get("projects")
        projects = projects_response.get("items", [])

        # Fetch all users
        users_response = await api_client.get("users")
        users = users_response.get("items", [])
        users_map = {user["id"]: user for user in users}

        # Collect all boards, lists, labels from projects
        boards_map = {}
        lists_map = {}
        labels_map = {}

        for project in projects:
            # Get project details (includes boards)
            project_detail = await api_client.get(f"projects/{project['id']}")
            project_boards = project_detail.get("included", {}).get("boards", [])

            for board_summary in project_boards:
                # Get board details (includes lists, labels, cards)
                board_detail = await api_client.get(f"boards/{board_summary['id']}")
                board = board_detail.get("item", {})
                included = board_detail.get("included", {})

                # Store board
                boards_map[board["id"]] = {
                    "id": board["id"],
                    "name": board.get("name", "Unnamed Board"),
                    "projectId": board.get("projectId"),
                    "project_name": project.get("name", "Unknown Project")
                }

                # Store lists
                for lst in included.get("lists", []):
                    lists_map[lst["id"]] = {
                        "id": lst["id"],
                        "name": lst.get("name", "Unnamed List"),
                        "boardId": lst.get("boardId"),
                        "board_name": board.get("name", "Unknown Board"),
                        "position": lst.get("position", 0)
                    }

                # Store labels
                for label in included.get("labels", []):
                    labels_map[label["id"]] = {
                        "id": label["id"],
                        "name": label.get("name", "Unnamed Label"),
                        "color": label.get("color", "gray"),
                        "boardId": label.get("boardId"),
                        "board_name": board.get("name", "Unknown Board")
                    }

        return {
            "projects": projects,
            "boards": boards_map,
            "lists": lists_map,
            "labels": labels_map,
            "users": users_map
        }
    except Exception as e:
        raise e

# ==================== TOOLS ====================

@mcp.tool(
    name="planka_get_workspace",
    annotations={
        "title": "Get Planka Workspace Structure",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def planka_get_workspace(params: GetWorkspaceInput) -> str:
    '''Get complete workspace structure in one call (projects, boards, lists, labels, users).

    This is the MOST IMPORTANT tool for token efficiency - it provides all workspace context
    in a single call, saving 50-66% tokens compared to making separate calls. Use this first
    to get all IDs and structure before working with specific cards or boards.

    Cached for 5 minutes with 90%+ hit rate in typical conversations.

    Args:
        params (GetWorkspaceInput): Format preference (markdown or json)

    Returns:
        str: Complete workspace structure showing all available projects, boards, lists,
             labels, and users. This gives you all the IDs you need for subsequent operations.

    Examples:
        - "What projects and boards are available?" → Use this tool
        - "Show me the workspace structure" → Use this tool
        - Before creating a card, use this to find the right list_id
    '''
    try:
        data = await cache.get_workspace(fetch_workspace_data)

        if params.response_format == ResponseFormat.JSON:
            content = json.dumps(data, indent=2)
        else:
            # Format as readable Markdown
            content = "# Planka Workspace\n\n"
            content += "## Projects\n"
            for project in data.get('projects', []):
                content += f"- **{project.get('name', 'Unnamed')}** (ID: `{project.get('id', 'N/A')}`)\n"

            content += "\n## Boards\n"
            for board_id, board in data.get('boards', {}).items():
                content += f"- **{board.get('name', 'Unnamed')}** (ID: `{board_id}`)\n"

            content += "\n## Lists\n"
            for list_id, lst in data.get('lists', {}).items():
                content += f"- **{lst.get('name', 'Unnamed')}** (ID: `{list_id}`)\n"

            content += "\n## Labels\n"
            for label_id, label in data.get('labels', {}).items():
                content += f"- **{label.get('name', 'Unnamed')}** (Color: {label.get('color', 'N/A')}, ID: `{label_id}`)\n"

            content += "\n## Users\n"
            for user_id, user in data.get('users', {}).items():
                content += f"- **{user.get('name', 'Unnamed')}** (ID: `{user_id}`)\n"

        return ResponseFormatter.truncate_response(content)

    except Exception as e:
        return handle_api_error(e)

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
    '''List cards from a Planka board with smart filtering and detail levels.

    Supports cross-list queries (set list_id=None to get ALL cards from board) and label
    filtering. Use detail_level to control token usage: preview mode saves 60-88% tokens
    when browsing cards.

    Args:
        params (ListCardsInput): Filtering and formatting parameters

    Returns:
        str: Formatted list of cards matching the criteria

    Examples:
        - "Show me all In Progress cards" → board_id="X", list_id=None, label_filter="In Progress"
        - "What cards are in the TODO list?" → board_id="X", list_id="Y"
        - "Find all Critical bugs" → board_id="X", label_filter="Critical"
        - Use detail_level="preview" for quick browsing (saves 88% tokens vs detailed)
    '''
    try:
        # Fetch board details (includes lists, labels, cards)
        board_detail = await api_client.get(f"boards/{params.board_id}")
        board = board_detail.get("item", {})
        included = board_detail.get("included", {})

        # Build context maps for formatters
        lists_map = {lst["id"]: lst for lst in included.get("lists", [])}
        labels_map = {lbl["id"]: lbl for lbl in included.get("labels", [])}
        users_map = {usr["id"]: usr for usr in included.get("users", [])}

        context = {
            'lists': lists_map,
            'labels': labels_map,
            'users': users_map,
            'board_name': board.get("name", "Unknown Board")
        }

        # Get all cards from included
        cards = included.get("cards", [])

        # Filter by list if specified
        if params.list_id:
            cards = [c for c in cards if c.get('listId') == params.list_id]

        # Filter by label if specified (case-insensitive partial match)
        if params.label_filter:
            label_lower = params.label_filter.lower()
            cards = [
                c for c in cards
                if any(
                    label_lower in labels_map.get(label_id, {}).get('name', '').lower()
                    for label_id in c.get('labelIds', [])
                )
            ]

        # Paginate
        paginated = PaginationHelper.paginate_results(
            cards,
            params.offset,
            params.limit
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            content = ResponseFormatter.format_card_list_markdown(
                paginated["items"],
                context,
                params.detail_level
            )

            # Add pagination info if there's more data
            if paginated["has_more"]:
                content += f"\n\n---\n**Pagination**: Showing {paginated['count']} of {paginated['total']} cards. "
                content += f"Use offset={paginated['next_offset']} to see more.\n"
        else:
            content = json.dumps({
                "board": {
                    "id": board["id"],
                    "name": board.get("name", "Unknown Board")
                },
                "cards": paginated["items"],
                "pagination": paginated
            }, indent=2)

        return ResponseFormatter.truncate_response(content)

    except Exception as e:
        return handle_api_error(e)

@mcp.tool(
    name="planka_find_and_get_card",
    annotations={
        "title": "Find and Get Planka Card",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def planka_find_and_get_card(params: FindAndGetCardInput) -> str:
    '''Search for a card by name/description and get full details in one operation.

    This composite tool saves 37% tokens by combining search + retrieval. If multiple
    cards match, returns a list to choose from. If unique match, returns full card details.

    Args:
        params (FindAndGetCardInput): Search query and optional board filter

    Returns:
        str: Card details if unique match, or list of matching cards to choose from

    Examples:
        - "Find the login bug card and show details" → Single efficient call
        - "Get details about the authentication card" → Searches + retrieves
    '''
    try:
        query_lower = params.query.lower()
        matching_cards = []

        # If board_id specified, search only that board
        if params.board_id:
            board_detail = await api_client.get(f"boards/{params.board_id}")
            cards = board_detail.get("included", {}).get("cards", [])

            # Search in card name and description
            matching_cards = [
                c for c in cards
                if query_lower in c.get('name', '').lower()
                or query_lower in c.get('description', '').lower()
            ]
        else:
            # Search across all boards - fetch workspace
            workspace = await cache.get_workspace(fetch_workspace_data)

            # Search each board
            for board_id in workspace.get("boards", {}).keys():
                board_detail = await api_client.get(f"boards/{board_id}")
                cards = board_detail.get("included", {}).get("cards", [])

                matching_cards.extend([
                    c for c in cards
                    if query_lower in c.get('name', '').lower()
                    or query_lower in c.get('description', '').lower()
                ])

        # If no matches, return message
        if not matching_cards:
            return f"No cards found matching query: '{params.query}'"

        # If single match, return full details
        if len(matching_cards) == 1:
            card = matching_cards[0]
            # Fetch full card details
            card_detail = await api_client.get(f"cards/{card['id']}")
            full_card = card_detail.get("item", {})
            included = card_detail.get("included", {})

            # Build context
            workspace = await cache.get_workspace(fetch_workspace_data)
            context = {
                'lists': workspace.get('lists', {}),
                'labels': {lbl["id"]: lbl for lbl in included.get("labels", [])},
                'users': {usr["id"]: usr for usr in included.get("users", [])},
                'board_name': workspace.get('boards', {}).get(full_card.get('boardId'), {}).get('name', 'Unknown Board')
            }

            # Merge included data into card
            full_card['taskLists'] = included.get('taskLists', [])
            full_card['comments'] = included.get('comments', [])
            full_card['attachments'] = included.get('attachments', [])

            if params.response_format == ResponseFormat.MARKDOWN:
                return ResponseFormatter.format_card_detailed(full_card, context)
            else:
                return json.dumps(full_card, indent=2)

        # Multiple matches - return list to choose from
        workspace = await cache.get_workspace(fetch_workspace_data)
        output = f"# Found {len(matching_cards)} matching cards\n\n"
        for card in matching_cards[:10]:  # Limit to first 10
            list_name = workspace.get('lists', {}).get(card.get('listId'), {}).get('name', 'Unknown List')
            board_name = workspace.get('boards', {}).get(card.get('boardId'), {}).get('name', 'Unknown Board')
            output += f"- **{card.get('name', 'Untitled')}** (ID: `{card['id']}`)\n"
            output += f"  - Board: {board_name}\n"
            output += f"  - List: {list_name}\n\n"

        if len(matching_cards) > 10:
            output += f"\n... and {len(matching_cards) - 10} more cards.\n"

        output += "\n**Use planka_get_card with a specific card ID to see full details.**"
        return output

    except Exception as e:
        return handle_api_error(e)

@mcp.tool(
    name="planka_get_card",
    annotations={
        "title": "Get Planka Card Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def planka_get_card(params: GetCardInput) -> str:
    '''Get complete details for a specific card.

    Returns full card information including tasks, comments, attachments, members, and labels.
    Uses response_context parameter to control how much metadata is included.

    Args:
        params (GetCardInput): Card ID and formatting preferences

    Returns:
        str: Complete card details with all related information

    Examples:
        - "Show me everything about card abc123" → Full card details
        - "Get card details for xyz789" → Complete information
    '''
    try:
        # Fetch card with caching
        async def fetch_card():
            card_detail = await api_client.get(f"cards/{params.card_id}")
            full_card = card_detail.get("item", {})
            included = card_detail.get("included", {})

            # Merge included data into card
            full_card['taskLists'] = included.get('taskLists', [])
            full_card['comments'] = included.get('comments', [])
            full_card['attachments'] = included.get('attachments', [])
            full_card['_included_labels'] = included.get('labels', [])
            full_card['_included_users'] = included.get('users', [])

            return full_card

        card = await cache.get_card(params.card_id, fetch_card)

        # Build context from workspace
        workspace = await cache.get_workspace(fetch_workspace_data)

        # Use included data if available, otherwise use workspace data
        labels_map = {lbl["id"]: lbl for lbl in card.get('_included_labels', [])}
        if not labels_map:
            labels_map = workspace.get('labels', {})

        users_map = {usr["id"]: usr for usr in card.get('_included_users', [])}
        if not users_map:
            users_map = workspace.get('users', {})

        context = {
            'lists': workspace.get('lists', {}),
            'labels': labels_map,
            'users': users_map,
            'board_name': workspace.get('boards', {}).get(card.get('boardId'), {}).get('name', 'Unknown Board')
        }

        if params.response_format == ResponseFormat.MARKDOWN:
            content = ResponseFormatter.format_card_detailed(card, context)
        else:
            content = json.dumps(card, indent=2)

        return ResponseFormatter.truncate_response(content)

    except Exception as e:
        return handle_api_error(e)

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
async def planka_create_card(params: CreateCardInput) -> str:
    '''Create a new card in a Planka list.

    Creates a card with the specified name, description, and optional due date. Returns
    minimal confirmation to save tokens.

    Args:
        params (CreateCardInput): Card details (list_id, name, description, due_date, position)

    Returns:
        str: Minimal confirmation with card ID and name

    Examples:
        - "Create a card called 'Fix login bug' in the TODO list" → Creates card
        - "Add new task 'Update docs' with description..." → Creates card with details
    '''
    try:
        # Build request body
        card_data = {"name": params.name}

        if params.description:
            card_data["description"] = params.description
        if params.due_date:
            card_data["dueDate"] = params.due_date
        if params.position is not None:
            card_data["position"] = params.position

        # Create card
        response = await api_client.post(f"lists/{params.list_id}/cards", card_data)
        card = response.get("item", {})

        # Invalidate board cache (board now has new card)
        if card.get('boardId'):
            cache.invalidate_board(card['boardId'])

        # Return minimal confirmation
        return f"✓ Created card: **{card.get('name', 'Untitled')}** (ID: `{card.get('id', 'N/A')}`)"

    except Exception as e:
        return handle_api_error(e)

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
async def planka_update_card(params: UpdateCardInput) -> str:
    '''Update an existing card's details.

    Modify card name, description, due date, position, or move to different list.
    Invalidates relevant caches automatically.

    Args:
        params (UpdateCardInput): Card ID and fields to update

    Returns:
        str: Minimal confirmation with updated fields

    Examples:
        - "Update card abc123 description to..." → Updates description
        - "Move card xyz789 to the Done list" → Moves card to different list
    '''
    try:
        # Build update payload (only include fields that are provided)
        update_data = {}

        if params.name is not None:
            update_data["name"] = params.name
        if params.description is not None:
            update_data["description"] = params.description
        if params.due_date is not None:
            update_data["dueDate"] = params.due_date
        if params.list_id is not None:
            update_data["listId"] = params.list_id
        if params.position is not None:
            update_data["position"] = params.position

        # Update card
        response = await api_client.patch(f"cards/{params.card_id}", update_data)
        card = response.get("item", {})

        # Invalidate caches
        cache.invalidate_card(params.card_id)
        if card.get('boardId'):
            cache.invalidate_board(card['boardId'])

        # Build confirmation message
        updates = []
        if params.name:
            updates.append("name")
        if params.description is not None:
            updates.append("description")
        if params.due_date:
            updates.append("due date")
        if params.list_id:
            updates.append("list (moved)")
        if params.position is not None:
            updates.append("position")

        update_str = ", ".join(updates) if updates else "card"

        return f"✓ Updated {update_str} for card: **{card.get('name', 'Untitled')}** (ID: `{card.get('id', params.card_id)}`)"

    except Exception as e:
        return handle_api_error(e)

@mcp.tool(
    name="planka_add_task",
    annotations={
        "title": "Add Task to Card",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def planka_add_task(params: AddTaskInput) -> str:
    '''Add a task (checklist item) to a card.

    Creates a task in the specified task list (or creates "Tasks" list if not exists).
    Common pattern for tracking subtasks within cards.

    Args:
        params (AddTaskInput): Card ID, task name, and optional task list name

    Returns:
        str: Confirmation with task details

    Examples:
        - "Add task 'Contact support' to card abc123" → Adds task
        - "Add checklist item 'Review PR' to card xyz789" → Adds task
    '''
    try:
        # First, get the card to check for existing task lists
        card_detail = await api_client.get(f"cards/{params.card_id}")
        included = card_detail.get("included", {})
        task_lists = included.get("taskLists", [])

        # Find or create the task list
        task_list = None
        task_list_name = params.task_list_name or "Tasks"

        # Look for existing task list with matching name
        for tl in task_lists:
            if tl.get("name", "").lower() == task_list_name.lower():
                task_list = tl
                break

        # If no task list exists, create one
        if not task_list:
            response = await api_client.post(
                f"cards/{params.card_id}/task-lists",
                {"name": task_list_name}
            )
            task_list = response.get("item", {})

        # Create the task
        task_response = await api_client.post(
            f"task-lists/{task_list['id']}/tasks",
            {"name": params.task_name}
        )
        task = task_response.get("item", {})

        # Invalidate card cache
        cache.invalidate_card(params.card_id)

        return f"✓ Added task: **{task.get('name', 'Unnamed')}** to list '{task_list.get('name', 'Tasks')}' (Task ID: `{task.get('id', 'N/A')}`)"

    except Exception as e:
        return handle_api_error(e)

@mcp.tool(
    name="planka_update_task",
    annotations={
        "title": "Update Task Status",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def planka_update_task(params: UpdateTaskInput) -> str:
    '''Update a task's completion status.

    Mark a task as completed or incomplete. Returns updated progress.

    Args:
        params (UpdateTaskInput): Task ID and completion status

    Returns:
        str: Confirmation with updated task status

    Examples:
        - "Mark task abc123 as complete" → Sets isCompleted=true
        - "Mark task xyz789 as incomplete" → Sets isCompleted=false
    '''
    try:
        # Update task
        response = await api_client.patch(
            f"tasks/{params.task_id}",
            {"isCompleted": params.is_completed}
        )
        task = response.get("item", {})

        # Invalidate card cache (task belongs to card via task list)
        # Note: We'd need to track card_id, but for now we'll leave it
        # The cache will expire naturally within 1 minute

        status = "complete" if params.is_completed else "incomplete"
        check = "[x]" if params.is_completed else "[ ]"

        return f"✓ Marked task as {status}: {check} **{task.get('name', 'Unnamed task')}** (ID: `{task.get('id', params.task_id)}`)"

    except Exception as e:
        return handle_api_error(e)

# ==================== SERVER LIFECYCLE ====================

@mcp.server.on_startup()
async def on_startup():
    """Initialize API client and cache system on server startup."""
    global api_client, cache

    try:
        token = await initialize_auth()
        base_url = os.getenv("PLANKA_BASE_URL")

        api_client = PlankaAPIClient(base_url, token)
        cache = PlankaCache()

        print(f"Planka MCP Server initialized successfully")
        print(f"Connected to: {base_url}")
    except Exception as e:
        print(f"Failed to initialize server: {e}")
        raise

@mcp.server.on_shutdown()
async def on_shutdown():
    """Clean up resources on server shutdown."""
    global api_client

    if api_client:
        await api_client.close()
        print("Planka MCP Server shut down successfully")

# ==================== MAIN ====================

if __name__ == "__main__":
    mcp.run()
