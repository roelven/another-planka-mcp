# Planka MCP Server - Implementation Guide for LLM Agents

## Overview

This guide breaks down the Planka MCP server implementation into discrete, self-contained tasks that can be executed by LLM agents independently. Each task is designed to be completable in a single session and produces verifiable artifacts.

## Project Structure

```
planka-mcp/
├── planka_mcp.py              # Main server implementation
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── .env                      # Actual environment variables (create this)
├── README.md                 # User documentation
├── evaluations.xml           # Evaluation test cases
├── IMPLEMENTATION_PLAN.md    # Detailed design document
├── TOKEN_EFFICIENCY_ANALYSIS.md  # Performance analysis
├── WORKFLOW_OPTIMIZATIONS.md # User-specific optimizations
└── IMPLEMENTATION_GUIDE.md   # This file - task breakdown
```

## Task Dependency Graph

```
[PHASE 1: Foundation]
├─ Task 1.1: Project Setup
├─ Task 1.2: Environment Configuration
└─ Task 1.3: API Client Base Implementation

[PHASE 2: Core Infrastructure] (depends on Phase 1)
├─ Task 2.1: Caching System Implementation
├─ Task 2.2: Input Validation Models (Pydantic)
└─ Task 2.3: Response Formatting Utilities

[PHASE 3: Tier 0 Tools - Critical] (depends on Phase 2)
└─ Task 3.1: planka_get_workspace (with caching)

[PHASE 4: Tier 1 Tools - Core Workflow] (depends on Phase 3)
├─ Task 4.1: planka_list_cards (with all optimizations)
├─ Task 4.2: planka_get_card
├─ Task 4.3: planka_find_and_get_card (composite)
├─ Task 4.4: planka_create_card
├─ Task 4.5: planka_update_card
├─ Task 4.6: planka_add_task
└─ Task 4.7: planka_update_task

[PHASE 5: Testing & Documentation] (depends on Phase 4)
├─ Task 5.1: Manual Testing with MCP Inspector
├─ Task 5.2: Create Evaluation Questions
└─ Task 5.3: Write README Documentation
```

---

## How to Use This Guide

### For Human Project Manager:
1. Assign tasks sequentially or in parallel (respecting dependencies)
2. Each task can be given to a fresh LLM agent
3. Agent reads task specification + relevant context
4. Agent implements task and marks as complete
5. Move to next task

### For LLM Agent:
1. You will be given a specific task number (e.g., "Task 2.1")
2. Read the task specification below
3. Review the specified context documents
4. Implement the task according to the specification
5. Verify completion criteria are met
6. Report completion

---

# PHASE 1: Foundation

## Task 1.1: Project Setup

**Objective:** Create basic project structure and install dependencies

**Prerequisites:** None (first task)

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` sections: "Project Structure" (2.1), "Core Dependencies" (2.2)

**Implementation Steps:**
1. Create project directory structure:
   ```
   planka-mcp/
   ├── planka_mcp.py (empty file)
   ├── requirements.txt
   ├── .env.example
   └── README.md (placeholder)
   ```

2. Create `requirements.txt`:
   ```
   mcp>=1.0.0
   pydantic>=2.0.0
   httpx>=0.27.0
   python-dotenv>=1.0.0
   ```

3. Create `.env.example`:
   ```bash
   # Planka MCP Server Configuration
   PLANKA_BASE_URL=https://planka.example.com
   PLANKA_API_TOKEN=your-access-token-here
   ```

4. Create basic `planka_mcp.py` skeleton:
   ```python
   #!/usr/bin/env python3
   """
   Planka MCP Server

   Token-optimized MCP server for Planka kanban boards.
   """

   from mcp.server.fastmcp import FastMCP

   # Initialize server
   mcp = FastMCP("planka_mcp")

   if __name__ == "__main__":
       mcp.run()
   ```

**Outputs:**
- [ ] `requirements.txt` exists with correct dependencies
- [ ] `.env.example` exists with configuration template
- [ ] `planka_mcp.py` exists with basic skeleton
- [ ] Running `python planka_mcp.py` doesn't crash (even if it does nothing)

**Validation:**
```bash
# Should not error
python -m py_compile planka_mcp.py
python planka_mcp.py --help
```

**Estimated Effort:** 15 minutes

---

## Task 1.2: Environment Configuration

**Objective:** Set up authentication configuration system

**Prerequisites:** Task 1.1 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` section "Configuration" (2.3)
- Review "Authentication Strategy" (3.2)

**Implementation Steps:**

1. Add imports to `planka_mcp.py`:
   ```python
   import os
   from dotenv import load_dotenv
   ```

2. Implement authentication initialization function:
   ```python
   async def initialize_auth() -> str:
       """Initialize authentication and return access token.

       Supports three authentication methods:
       1. PLANKA_API_TOKEN (preferred)
       2. PLANKA_API_KEY
       3. PLANKA_EMAIL + PLANKA_PASSWORD

       Returns:
           str: Access token for API requests

       Raises:
           ValueError: If no valid authentication method configured
       """
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
   ```

3. Add startup hook:
   ```python
   @mcp.server.on_startup()
   async def on_startup():
       """Initialize on server startup."""
       global auth_token
       auth_token = await initialize_auth()
       print(f"✓ Authenticated with Planka at {os.getenv('PLANKA_BASE_URL')}")
   ```

4. Create your actual `.env` file (not tracked in git):
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

**Outputs:**
- [ ] `initialize_auth()` function implemented in `planka_mcp.py`
- [ ] Startup hook added with authentication
- [ ] `.env` file created with real credentials
- [ ] Server starts without errors and prints authentication success

**Validation:**
```bash
# Should print authentication success
python planka_mcp.py
# Press Ctrl+C to stop
```

**Estimated Effort:** 20 minutes

---

## Task 1.3: API Client Base Implementation

**Objective:** Create reusable HTTP client for Planka API requests

**Prerequisites:** Task 1.2 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` section "API Client Module" (2.4)
- Review "Error Handling" (2.4)

**Implementation Steps:**

1. Add imports at top of `planka_mcp.py`:
   ```python
   import httpx
   from typing import Optional, Dict, Any
   ```

2. Add constants after imports:
   ```python
   # Constants
   CHARACTER_LIMIT = 25000
   DEFAULT_TIMEOUT = 30.0
   ```

3. Implement `PlankaAPIClient` class:
   ```python
   class PlankaAPIClient:
       """Centralized API client for Planka requests."""

       def __init__(self, base_url: str, auth_token: str):
           self.base_url = base_url.rstrip('/')
           self.auth_token = auth_token
           self._client: Optional[httpx.AsyncClient] = None

       async def _get_client(self) -> httpx.AsyncClient:
           """Get or create HTTP client."""
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
       ) -> Dict[str, Any]:
           """Make authenticated API request.

           Args:
               method: HTTP method (GET, POST, PATCH, DELETE)
               endpoint: API endpoint (e.g., "api/boards/123")
               params: URL query parameters
               json_data: JSON request body

           Returns:
               Dict: JSON response from API

           Raises:
               httpx.HTTPStatusError: On HTTP error responses
           """
           client = await self._get_client()
           url = f"{self.base_url}/{endpoint.lstrip('/')}"

           response = await client.request(
               method=method,
               url=url,
               params=params,
               json=json_data
           )
           response.raise_for_status()
           return response.json()

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
           """Close HTTP client."""
           if self._client:
               await self._client.aclose()
   ```

4. Implement error handler function:
   ```python
   def handle_api_error(e: Exception) -> str:
       """Convert exceptions to actionable error messages.

       Args:
           e: Exception from API request

       Returns:
           str: User-friendly error message with guidance
       """
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

5. Update startup hook to create global API client:
   ```python
   # Global API client
   api_client: Optional[PlankaAPIClient] = None

   @mcp.server.on_startup()
   async def on_startup():
       """Initialize API client on server startup."""
       global api_client
       token = await initialize_auth()
       base_url = os.getenv("PLANKA_BASE_URL")
       api_client = PlankaAPIClient(base_url, token)
       print(f"✓ API client initialized for {base_url}")
   ```

**Outputs:**
- [ ] `PlankaAPIClient` class implemented
- [ ] `handle_api_error()` function implemented
- [ ] Global `api_client` instance created in startup
- [ ] Server starts and initializes API client

**Validation:**
```bash
# Should initialize without errors
python planka_mcp.py
# Press Ctrl+C to stop
```

**Estimated Effort:** 30 minutes

---

# PHASE 2: Core Infrastructure

## Task 2.1: Caching System Implementation

**Objective:** Implement multi-tier caching system for token optimization

**Prerequisites:** Task 1.3 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` section "Caching Architecture" (3.3)
- Review `TOKEN_EFFICIENCY_ANALYSIS.md` for cache TTL decisions

**Implementation Steps:**

1. Add imports:
   ```python
   import time
   from dataclasses import dataclass
   ```

2. Implement `CacheEntry` dataclass:
   ```python
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
   ```

3. Implement `PlankaCache` class:
   ```python
   class PlankaCache:
       """Multi-tier caching system optimized for low-concurrency environment."""

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

           Args:
               fetch_func: Async function to fetch fresh data if cache miss

           Returns:
               Dict: Workspace structure
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
   ```

4. Update startup hook to create cache:
   ```python
   # Global cache instance
   cache: Optional[PlankaCache] = None

   @mcp.server.on_startup()
   async def on_startup():
       """Initialize API client and cache on server startup."""
       global api_client, cache
       token = await initialize_auth()
       base_url = os.getenv("PLANKA_BASE_URL")
       api_client = PlankaAPIClient(base_url, token)
       cache = PlankaCache()
       print(f"✓ API client initialized for {base_url}")
       print(f"✓ Cache system initialized")
   ```

**Outputs:**
- [ ] `CacheEntry` dataclass implemented
- [ ] `PlankaCache` class implemented with all methods
- [ ] Global `cache` instance created in startup
- [ ] Server starts and initializes cache

**Validation:**
```python
# Manual test in Python REPL after starting server
cache.stats  # Should show all zeros initially
```

**Estimated Effort:** 40 minutes

---

## Task 2.2: Input Validation Models (Pydantic)

**Objective:** Create Pydantic models for all tool inputs

**Prerequisites:** Task 2.1 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` section "Input Validation Models" (2.5)
- Review tool specifications in section 1.2

**Implementation Steps:**

1. Add imports:
   ```python
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from enum import Enum
   from typing import Optional, List
   ```

2. Define enum types:
   ```python
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
   ```

3. Define input models (place after enums):
   ```python
   # ============================================================================
   # INPUT VALIDATION MODELS
   # ============================================================================

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

   class GetCardInput(BaseModel):
       """Input for getting single card details."""
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

   class FindAndGetCardInput(BaseModel):
       """Input for finding and getting card in one operation."""
       model_config = ConfigDict(
           str_strip_whitespace=True,
           validate_assignment=True,
           extra='forbid'
       )

       query: str = Field(
           ...,
           description="Search query to find card by name or description",
           min_length=2,
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

   class UpdateCardInput(BaseModel):
       """Input for updating card details."""
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
           description="New card name",
           min_length=1,
           max_length=500
       )
       description: Optional[str] = Field(
           None,
           description="New card description (Markdown supported)",
           max_length=10000
       )
       due_date: Optional[str] = Field(
           None,
           description="New due date in ISO format",
           pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
       )
       list_id: Optional[str] = Field(
           None,
           description="Move card to different list",
           max_length=100
       )
       position: Optional[float] = Field(
           None,
           description="New position in list"
       )

   class AddTaskInput(BaseModel):
       """Input for adding task to card."""
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
           description="Task name/description",
           min_length=1,
           max_length=500
       )
       task_list_id: Optional[str] = Field(
           None,
           description="Optional: Specific task list ID. If None, creates/uses default task list",
           max_length=100
       )

   class UpdateTaskInput(BaseModel):
       """Input for updating task status."""
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
       completed: bool = Field(
           ...,
           description="Task completion status: true (complete) or false (incomplete)"
       )
   ```

**Outputs:**
- [ ] All enum types defined (ResponseFormat, DetailLevel, ResponseContext)
- [ ] All input models defined (8 models total)
- [ ] Models use Pydantic v2 syntax (model_config, Field with descriptions)
- [ ] No syntax errors

**Validation:**
```python
# Test models can be instantiated
test = ListCardsInput(board_id="test123")
print(test.model_dump())  # Should print valid dict
```

**Estimated Effort:** 45 minutes

---

## Task 2.3: Response Formatting Utilities

**Objective:** Create helper functions for formatting tool responses

**Prerequisites:** Task 2.2 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` section "Response Format Design" (2.7)
- Review detail level specifications

**Implementation Steps:**

1. Add import:
   ```python
   import json
   ```

2. Implement helper functions (place after input models, before tools):
   ```python
   # ============================================================================
   # RESPONSE FORMATTING UTILITIES
   # ============================================================================

   def format_card_preview(card: Dict, context: ResponseContext = ResponseContext.STANDARD) -> Dict:
       """Format card in preview mode (~50 tokens).

       Args:
           card: Raw card data from API
           context: How much context to include

       Returns:
           Dict with minimal card info
       """
       result = {
           "id": card["id"],
           "name": card["name"],
           "list": card.get("list", {}).get("name") if context != ResponseContext.MINIMAL else card.get("listId"),
           "labels": [
               label["name"] if context != ResponseContext.MINIMAL else label["id"]
               for label in card.get("labels", [])
           ],
           "due_date": card.get("dueDate"),
           "tasks": _format_task_progress(card.get("taskLists", [])),
           "comments": len(card.get("comments", [])),
           "attachments": len(card.get("attachments", []))
       }
       return result

   def format_card_summary(card: Dict, context: ResponseContext = ResponseContext.STANDARD) -> Dict:
       """Format card in summary mode (~200 tokens).

       Args:
           card: Raw card data from API
           context: How much context to include

       Returns:
           Dict with standard card info
       """
       result = format_card_preview(card, context)
       result.update({
           "description": _truncate_text(card.get("description", ""), 200),
           "members": [
               {"id": m["id"], "name": m.get("name", "Unknown")}
               for m in card.get("members", [])
           ] if context != ResponseContext.MINIMAL else [m["id"] for m in card.get("members", [])],
           "created_at": card.get("createdAt")
       })
       return result

   def format_card_detailed(card: Dict, context: ResponseContext = ResponseContext.STANDARD) -> Dict:
       """Format card in detailed mode (~400 tokens).

       Args:
           card: Raw card data from API
           context: How much context to include

       Returns:
           Dict with complete card info
       """
       result = format_card_summary(card, context)
       result["description"] = card.get("description", "")  # Full description
       result["updated_at"] = card.get("updatedAt")
       result["task_lists"] = [
           {
               "id": tl["id"],
               "name": tl.get("name", "Tasks"),
               "tasks": [
                   {
                       "id": t["id"],
                       "name": t["name"],
                       "completed": t.get("isCompleted", False)
                   }
                   for t in tl.get("tasks", [])
               ]
           }
           for tl in card.get("taskLists", [])
       ]
       result["comments"] = [
           {
               "id": c["id"],
               "text": c["text"],
               "user": {"id": c["user"]["id"], "name": c["user"].get("name", "Unknown")},
               "created_at": c.get("createdAt")
           }
           for c in card.get("comments", [])
       ]
       return result

   def format_card(
       card: Dict,
       detail_level: DetailLevel = DetailLevel.PREVIEW,
       context: ResponseContext = ResponseContext.STANDARD
   ) -> Dict:
       """Format card based on detail level.

       Args:
           card: Raw card data from API
           detail_level: Level of detail to include
           context: How much context to include

       Returns:
           Formatted card dict
       """
       if detail_level == DetailLevel.PREVIEW:
           return format_card_preview(card, context)
       elif detail_level == DetailLevel.SUMMARY:
           return format_card_summary(card, context)
       else:  # DETAILED
           return format_card_detailed(card, context)

   def format_cards_markdown(
       cards: List[Dict],
       board_name: str = "",
       detail_level: DetailLevel = DetailLevel.PREVIEW
   ) -> str:
       """Format multiple cards as Markdown.

       Args:
           cards: List of formatted card dicts
           board_name: Optional board name for header
           detail_level: Detail level used

       Returns:
           Markdown formatted string
       """
       lines = []

       if board_name:
           lines.append(f"# Cards in {board_name}")
           lines.append("")

       lines.append(f"**Total Cards:** {len(cards)}")
       lines.append("")

       for card in cards:
           lines.append(f"## {card['name']}")
           lines.append(f"**ID:** {card['id']}")
           lines.append(f"**List:** {card['list']}")

           if card.get('labels'):
               labels_str = ", ".join(card['labels']) if isinstance(card['labels'][0], str) else ", ".join([l['name'] for l in card['labels']])
               lines.append(f"**Labels:** {labels_str}")

           if card.get('tasks'):
               lines.append(f"**Tasks:** {card['tasks']}")

           if card.get('comments') or card.get('attachments'):
               indicators = []
               if card.get('comments'):
                   indicators.append(f"{card['comments']} comment(s)")
               if card.get('attachments'):
                   indicators.append(f"{card['attachments']} attachment(s)")
               lines.append(f"**Activity:** {', '.join(indicators)}")

           if detail_level != DetailLevel.PREVIEW:
               if card.get('description'):
                   lines.append("")
                   lines.append(card['description'])

           lines.append("")

       return "\n".join(lines)

   def format_cards_json(cards: List[Dict], metadata: Dict = None) -> str:
       """Format multiple cards as JSON.

       Args:
           cards: List of formatted card dicts
           metadata: Optional metadata (pagination, etc.)

       Returns:
           JSON formatted string
       """
       result = {
           "cards": cards,
           "count": len(cards)
       }
       if metadata:
           result.update(metadata)
       return json.dumps(result, indent=2)

   def _format_task_progress(task_lists: List[Dict]) -> str:
       """Format task progress as '3/5' string.

       Args:
           task_lists: List of task lists from card

       Returns:
           Progress string like "3/5" or empty string if no tasks
       """
       total = 0
       completed = 0
       for task_list in task_lists:
           for task in task_list.get("tasks", []):
               total += 1
               if task.get("isCompleted", False):
                   completed += 1

       return f"{completed}/{total}" if total > 0 else ""

   def _truncate_text(text: str, max_length: int) -> str:
       """Truncate text to max length with ellipsis.

       Args:
           text: Text to truncate
           max_length: Maximum length

       Returns:
           Truncated text
       """
       if len(text) <= max_length:
           return text
       return text[:max_length - 3] + "..."

   def check_and_truncate(content: str, limit: int = CHARACTER_LIMIT) -> str:
       """Truncate response if over character limit.

       Args:
           content: Response content
           limit: Character limit

       Returns:
           Truncated content with warning if needed
       """
       if len(content) <= limit:
           return content

       # Truncate at approximately 60% of limit to leave room for warning
       truncate_at = int(limit * 0.6)
       truncated = content[:truncate_at]

       # Try to truncate at a natural boundary (newline)
       last_newline = truncated.rfind('\n')
       if last_newline > truncate_at * 0.8:  # If within last 20%
           truncated = truncated[:last_newline]

       warning = f"""

---
⚠️ **RESPONSE TRUNCATED**: Output was {len(content):,} characters (limit: {limit:,})

**To see more results:**
- Use pagination: Increase `offset` parameter
- Add filters: Use `list_id` or `label_filter` to narrow results
- Reduce detail: Use `detail_level="preview"` instead of "detailed"
---
"""

       return truncated + warning
   ```

**Outputs:**
- [ ] All formatting functions implemented (10 functions)
- [ ] Functions handle preview/summary/detailed modes
- [ ] Markdown and JSON formatting supported
- [ ] Truncation logic implemented
- [ ] No syntax errors

**Validation:**
```python
# Test formatting functions
test_card = {"id": "123", "name": "Test", "labels": [], "comments": []}
preview = format_card_preview(test_card)
print(preview)  # Should print formatted dict
```

**Estimated Effort:** 60 minutes

---

# PHASE 3: Tier 0 Tools - Critical

## Task 3.1: planka_get_workspace Tool

**Objective:** Implement the most critical tool for token optimization

**Prerequisites:** All Phase 2 tasks complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` tool specification for `planka_get_workspace` (section 1.2, Tier 0)
- Review `TOKEN_EFFICIENCY_ANALYSIS.md` for why this is critical

**Implementation Steps:**

1. Implement workspace fetching function:
   ```python
   async def fetch_workspace_structure() -> Dict:
       """Fetch complete workspace structure from Planka API.

       Returns:
           Dict containing:
           - projects: List of all projects
           - boards: List of all boards (with project_id)
           - lists: List of all lists (with board_id)
           - labels: List of all labels (with board_id)
           - users: List of all users
       """
       # Fetch projects
       projects_response = await api_client.get("api/projects")
       projects = projects_response.get("items", [])

       # Fetch boards for each project
       all_boards = []
       all_lists = []
       all_labels = []

       for project in projects:
           # Get project details which includes boards
           project_details = await api_client.get(f"api/projects/{project['id']}")
           boards = project_details.get("included", {}).get("boards", [])

           for board in boards:
               board["project_id"] = project["id"]
               board["project_name"] = project["name"]
               all_boards.append(board)

               # Get board details which includes lists and labels
               board_details = await api_client.get(f"api/boards/{board['id']}")
               lists = board_details.get("included", {}).get("lists", [])
               labels = board_details.get("included", {}).get("labels", [])

               for lst in lists:
                   lst["board_id"] = board["id"]
                   lst["board_name"] = board["name"]
                   all_lists.append(lst)

               for label in labels:
                   label["board_id"] = board["id"]
                   label["board_name"] = board["name"]
                   all_labels.append(label)

       # Fetch users
       users_response = await api_client.get("api/users")
       users = users_response.get("items", [])

       return {
           "projects": projects,
           "boards": all_boards,
           "lists": all_lists,
           "labels": all_labels,
           "users": users
       }
   ```

2. Implement workspace formatting functions:
   ```python
   def format_workspace_markdown(workspace: Dict) -> str:
       """Format workspace structure as Markdown.

       Args:
           workspace: Workspace structure dict

       Returns:
           Markdown formatted workspace overview
       """
       lines = ["# Planka Workspace Overview", ""]

       # Projects section
       projects = workspace["projects"]
       lines.append(f"## Projects ({len(projects)})")
       lines.append("")

       for project in projects:
           project_id = project["id"]
           project_name = project["name"]
           lines.append(f"### {project_name} ({project_id})")

           # Boards in this project
           project_boards = [b for b in workspace["boards"] if b.get("project_id") == project_id]
           if project_boards:
               lines.append("**Boards:**")
               for board in project_boards:
                   board_id = board["id"]
                   board_name = board["name"]
                   lines.append(f"- {board_name} ({board_id})")

                   # Lists in this board
                   board_lists = [l for l in workspace["lists"] if l.get("board_id") == board_id]
                   if board_lists:
                       lines.append(f"  - Lists: {', '.join([l['name'] for l in board_lists])}")

                   # Labels in this board
                   board_labels = [lb for lb in workspace["labels"] if lb.get("board_id") == board_id]
                   if board_labels:
                       lines.append(f"  - Labels: {', '.join([lb['name'] for lb in board_labels])}")
           lines.append("")

       # Users section
       users = workspace["users"]
       lines.append(f"## Users ({len(users)})")
       lines.append("")
       for user in users[:10]:  # Show first 10 users
           lines.append(f"- {user.get('name', 'Unknown')} (@{user.get('username', 'unknown')}, {user['id']})")
       if len(users) > 10:
           lines.append(f"- ... and {len(users) - 10} more users")

       return "\n".join(lines)

   def format_workspace_json(workspace: Dict) -> str:
       """Format workspace structure as JSON.

       Args:
           workspace: Workspace structure dict

       Returns:
           JSON formatted workspace
       """
       return json.dumps(workspace, indent=2)
   ```

3. Implement the tool:
   ```python
   # ============================================================================
   # TIER 0 TOOLS - CRITICAL FOR TOKEN OPTIMIZATION
   # ============================================================================

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
       '''Get complete workspace structure including all projects, boards, lists, labels, and users.

       This is the MOST IMPORTANT tool for token efficiency. It returns the entire workspace
       structure in a single call, replacing 3-4 separate API requests. The response is cached
       for 5 minutes, providing 50-66% token reduction on discovery workflows.

       Use this tool at the start of conversations to understand available projects, boards,
       lists, and labels. Once you have this structure, you can reference IDs directly in
       other tools without additional lookups.

       Args:
           params (GetWorkspaceInput): Input parameters containing:
               - response_format (ResponseFormat): "markdown" or "json" (default: "markdown")

       Returns:
           str: Complete workspace structure in requested format

       Token Impact:
           - Without caching: ~1,000 tokens (vs 2,000-3,000 for separate calls)
           - With caching (90%+ hit rate): 0 tokens (cached response)
           - Enables agents to have all IDs needed for subsequent operations

       Examples:
           - "What projects and boards are available?" → Use this tool first
           - "Show me the workspace structure" → This tool
           - "What lists are in the HOMELAB board?" → Get board_id from this tool first

       Caching:
           - Cache TTL: 5 minutes
           - Cache hit rate: 90%+ in conversations
           - Invalidated by: Structural changes (rare)
       '''
       try:
           # Use cache for workspace structure (5 min TTL)
           workspace = await cache.get_workspace(fetch_workspace_structure)

           # Format response
           if params.response_format == ResponseFormat.MARKDOWN:
               content = format_workspace_markdown(workspace)
           else:
               content = format_workspace_json(workspace)

           # Check character limit
           return check_and_truncate(content)

       except Exception as e:
           return handle_api_error(e)
   ```

**Outputs:**
- [ ] `fetch_workspace_structure()` function implemented
- [ ] `format_workspace_markdown()` and `format_workspace_json()` implemented
- [ ] `planka_get_workspace` tool decorated and implemented
- [ ] Tool uses cache system
- [ ] Tool has comprehensive docstring
- [ ] No syntax errors

**Validation:**
```bash
# Start server in one terminal
python planka_mcp.py

# In another terminal, use MCP Inspector
npx @modelcontextprotocol/inspector python planka_mcp.py

# In inspector, call planka_get_workspace
# Should return workspace structure
```

**Estimated Effort:** 60 minutes

---

# PHASE 4: Tier 1 Tools - Core Workflow

> **Note:** Phase 4 tasks can be done in parallel by different agents if needed. Each tool is independent.

## Task 4.1: planka_list_cards Tool

**Objective:** Implement the core card listing tool with all optimizations

**Prerequisites:** Task 3.1 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` tool specification (section 1.2, Tier 1, tool #2)
- Review `WORKFLOW_OPTIMIZATIONS.md` for user-specific requirements

**Implementation Steps:**

[CONTINUED IN NEXT SECTION DUE TO LENGTH...]

Would you like me to continue with the remaining Phase 4 tasks and testing phases? Each subsequent task will follow the same clear format with prerequisites, steps, outputs, validation, and effort estimates.

**Estimated Effort:** 90 minutes

---

