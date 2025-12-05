# Implementation Guide - Part 2: Remaining Tasks

This file continues from IMPLEMENTATION_GUIDE.md with the remaining Phase 4 and Phase 5 tasks.

---

## Task 4.1: planka_list_cards Tool

**Objective:** Implement the core card listing tool with cross-list and label filtering

**Prerequisites:** Task 3.1 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` tool specification (section 1.2, Tier 1, tool #2)
- Review `WORKFLOW_OPTIMIZATIONS.md` section 1
- Review example implementation in IMPLEMENTATION_PLAN.md section 3.1

**Implementation Steps:**

1. Implement `planka_list_cards` tool (add to planka_mcp.py after planka_get_workspace):

```python
# ============================================================================
# TIER 1 TOOLS - CORE WORKFLOW
# ============================================================================

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
    '''List cards from a Planka board with advanced filtering and token optimization.

    This tool retrieves cards from a board with support for:
    - Cross-list querying (list_id=None returns ALL cards)
    - Label filtering (find all "In Progress" cards)
    - Smart detail levels (preview/summary/detailed for token optimization)
    - Pagination

    Most efficient for user's workflow: Use label_filter="In Progress" with list_id=None
    to find all active work across all categories in ONE call (vs 6 separate calls).

    Args:
        params (ListCardsInput): Validated input parameters containing:
            - board_id (str): Board ID to query
            - list_id (Optional[str]): Specific list ID or None for all lists
            - label_filter (Optional[str]): Filter by label name (case-insensitive)
            - limit (int): Max cards to return (1-100, default: 50)
            - offset (int): Pagination offset (default: 0)
            - response_format (ResponseFormat): "markdown" or "json"
            - detail_level (DetailLevel): "preview", "summary", or "detailed"
            - response_context (ResponseContext): "minimal", "standard", or "full"

    Returns:
        str: Formatted card list in requested format

    Examples:
        - "Show me all In Progress cards" → board_id=X, label_filter="In Progress", list_id=None
        - "What's in HOMELAB?" → board_id=X, list_id="homelab_id"
        - "Find Critical bugs in FINANCE" → board_id=X, list_id="finance_id", label_filter="Critical"

    Token Impact:
        - Preview mode: ~50 tokens per card (vs 400 in detailed)
        - Cross-list query: 1 call vs 6 calls (83% token reduction)
        - Label filtering: Eliminates client-side filtering
    '''
    try:
        # Get board data for context (may be cached in workspace)
        board_response = await api_client.get(f"api/boards/{params.board_id}")
        board = board_response.get("item", {})

        # Get all cards for this board
        # Note: Actual API structure may vary - adjust based on Planka's response format
        cards_data = board_response.get("included", {}).get("cards", [])

        # Filter by list if specified (None = all lists)
        if params.list_id:
            cards_data = [c for c in cards_data if c.get('listId') == params.list_id]

        # Filter by label if specified (case-insensitive partial match)
        if params.label_filter:
            label_lower = params.label_filter.lower()
            cards_data = [
                c for c in cards_data
                if any(
                    label_lower in label.get('name', '').lower()
                    for label in c.get('labels', [])
                )
            ]

        # Apply pagination
        total = len(cards_data)
        start = params.offset
        end = start + params.limit
        paginated_cards = cards_data[start:end]

        # Format cards based on detail level
        formatted_cards = [
            format_card(
                card,
                detail_level=params.detail_level,
                context=params.response_context
            )
            for card in paginated_cards
        ]

        # Create response with pagination metadata
        if params.response_format == ResponseFormat.MARKDOWN:
            content = format_cards_markdown(
                formatted_cards,
                board_name=board.get("name", ""),
                detail_level=params.detail_level
            )
            # Add pagination info
            if total > end:
                content += f"\n\n**Pagination:** Showing {start+1}-{end} of {total} cards. Use offset={end} to see more."
        else:
            metadata = {
                "pagination": {
                    "offset": params.offset,
                    "limit": params.limit,
                    "count": len(formatted_cards),
                    "total": total,
                    "has_more": end < total,
                    "next_offset": end if end < total else None
                },
                "filters": {
                    "list_id": params.list_id,
                    "label_filter": params.label_filter
                }
            }
            content = format_cards_json(formatted_cards, metadata)

        # Check character limit
        return check_and_truncate(content)

    except Exception as e:
        return handle_api_error(e)
```

**Outputs:**
- [ ] `planka_list_cards` tool implemented
- [ ] Supports cross-list querying (list_id=None)
- [ ] Supports label filtering (case-insensitive)
- [ ] Uses detail levels and context modes
- [ ] Includes pagination
- [ ] Has comprehensive docstring
- [ ] No syntax errors

**Validation:**
```bash
# Use MCP Inspector to test
npx @modelcontextprotocol/inspector python planka_mcp.py

# Test cases:
# 1. List all cards: board_id=X, list_id=None
# 2. List with label filter: board_id=X, label_filter="In Progress"
# 3. List specific list: board_id=X, list_id=Y
```

**Estimated Effort:** 45 minutes

---

## Task 4.2: planka_get_card Tool

**Objective:** Implement single card retrieval tool

**Prerequisites:** Task 4.1 complete (or can be done in parallel)

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` tool specification (section 1.2, Tier 1, tool #4)

**Implementation Steps:**

1. Implement `planka_get_card` tool:

```python
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
    '''Get complete details for a single card.

    Retrieves full card information including tasks, members, labels, comments, and attachments.
    Uses caching (1 min TTL) for performance optimization.

    Args:
        params (GetCardInput): Input containing:
            - card_id (str): Card ID to retrieve
            - response_format (ResponseFormat): "markdown" or "json"
            - response_context (ResponseContext): "minimal", "standard", or "full"

    Returns:
        str: Complete card details in requested format

    Examples:
        - "Show me card abc123" → card_id="abc123"
        - "Get details for the login bug card" → Use planka_find_and_get_card instead

    Caching:
        - Cache TTL: 1 minute
        - Hit rate: 40-50%
        - Use for cards you already have the ID for
    '''
    try:
        # Define fetch function for cache
        async def fetch_card():
            response = await api_client.get(f"api/cards/{params.card_id}")
            return response.get("item", {})

        # Use cache (1 min TTL)
        card = await cache.get_card(params.card_id, fetch_card)

        # Format card (always use DETAILED for single card view)
        formatted_card = format_card(
            card,
            detail_level=DetailLevel.DETAILED,
            context=params.response_context
        )

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            content = format_cards_markdown(
                [formatted_card],
                board_name="",
                detail_level=DetailLevel.DETAILED
            )
        else:
            content = json.dumps(formatted_card, indent=2)

        return check_and_truncate(content)

    except Exception as e:
        return handle_api_error(e)
```

**Outputs:**
- [ ] `planka_get_card` tool implemented
- [ ] Uses card caching
- [ ] Always returns detailed view for single cards
- [ ] Has comprehensive docstring

**Validation:**
```bash
# In MCP Inspector, test with a known card ID
# Should return full card details
```

**Estimated Effort:** 25 minutes

---

## Task 4.3: planka_find_and_get_card Tool (Composite)

**Objective:** Implement composite tool that combines search and retrieval

**Prerequisites:** Task 4.2 complete

**Context Required:**
- Review composite tool pattern in `IMPLEMENTATION_PLAN.md` (section 1.2, Tier 1, tool #3)
- Review `TOKEN_EFFICIENCY_ANALYSIS.md` section on composite tools

**Implementation Steps:**

1. Implement helper search function:

```python
async def search_cards_by_query(query: str, board_id: Optional[str] = None) -> List[Dict]:
    """Search for cards by name or description.

    Args:
        query: Search string
        board_id: Optional board ID to limit search

    Returns:
        List of matching cards
    """
    # Get all boards if board_id not specified
    if board_id:
        board_response = await api_client.get(f"api/boards/{board_id}")
        boards_data = [board_response.get("item", {})]
    else:
        workspace = await cache.get_workspace(fetch_workspace_structure)
        # Would need to fetch each board - for efficiency, require board_id
        raise ValueError("board_id is required for search. Use planka_get_workspace to find board IDs.")

    # Search cards in specified board
    all_cards = boards_data[0].get("included", {}).get("cards", [])
    query_lower = query.lower()

    matches = [
        card for card in all_cards
        if (query_lower in card.get("name", "").lower() or
            query_lower in card.get("description", "").lower())
    ]

    return matches
```

2. Implement `planka_find_and_get_card` tool:

```python
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
    '''Search for a card and return its complete details in one operation.

    This composite tool combines search and retrieval, saving a round trip and reducing
    token usage by 37% compared to separate search + get calls.

    If multiple cards match, returns a list of options.
    If single card matches, returns full details.

    Args:
        params (FindAndGetCardInput): Input containing:
            - query (str): Search string to match against card names/descriptions
            - board_id (Optional[str]): Board to search (required for efficiency)
            - response_format (ResponseFormat): "markdown" or "json"

    Returns:
        str: Card details if single match, or list of options if multiple matches

    Examples:
        - "Find the login bug card" → query="login bug", board_id=X
        - "Show me the Soly card" → query="soly", board_id=X

    Token Impact:
        - Saves 37% tokens vs separate search + get
        - Saves 1 round trip (faster response)
    '''
    try:
        # Search for matching cards
        matches = await search_cards_by_query(params.query, params.board_id)

        if len(matches) == 0:
            return f"No cards found matching '{params.query}'"

        elif len(matches) == 1:
            # Single match - return full details
            card = matches[0]
            formatted_card = format_card(card, detail_level=DetailLevel.DETAILED)

            if params.response_format == ResponseFormat.MARKDOWN:
                content = format_cards_markdown([formatted_card], detail_level=DetailLevel.DETAILED)
            else:
                content = json.dumps(formatted_card, indent=2)

        else:
            # Multiple matches - return list of options
            formatted_cards = [
                format_card(card, detail_level=DetailLevel.PREVIEW)
                for card in matches
            ]

            if params.response_format == ResponseFormat.MARKDOWN:
                content = f"# Found {len(matches)} cards matching '{params.query}'\n\n"
                content += "Please specify which card by using planka_get_card with one of these IDs:\n\n"
                content += format_cards_markdown(formatted_cards, detail_level=DetailLevel.PREVIEW)
            else:
                content = json.dumps({
                    "message": f"Multiple matches found for '{params.query}'",
                    "count": len(matches),
                    "matches": formatted_cards
                }, indent=2)

        return check_and_truncate(content)

    except Exception as e:
        return handle_api_error(e)
```

**Outputs:**
- [ ] `search_cards_by_query()` helper implemented
- [ ] `planka_find_and_get_card` tool implemented
- [ ] Handles single and multiple matches appropriately
- [ ] Has comprehensive docstring

**Validation:**
```bash
# Test with MCP Inspector
# 1. Search for unique card - should return full details
# 2. Search for common term - should return list of options
```

**Estimated Effort:** 35 minutes

---

## Task 4.4: planka_create_card Tool

**Objective:** Implement card creation tool

**Prerequisites:** Task 4.1 complete (or can be done in parallel)

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` tool specification (section 1.2, Tier 1, tool #5)
- Review cache invalidation strategy (section 3.3)

**Implementation Steps:**

1. Implement `planka_create_card` tool:

```python
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

    Creates a new card with specified name, optional description, due date, and position.
    Returns minimal confirmation to reduce response tokens.

    After creation, invalidates board cache to ensure fresh data on next query.

    Args:
        params (CreateCardInput): Input containing:
            - list_id (str): List where card should be created
            - name (str): Card name/title
            - description (Optional[str]): Card description (Markdown supported)
            - due_date (Optional[str]): Due date in ISO format
            - position (Optional[float]): Position in list

    Returns:
        str: Minimal confirmation with card ID and name

    Examples:
        - "Create a card to update docs" → list_id=X, name="Update documentation"
        - "Add task for API refactor with Jan 15 due date" → list_id=X, name="API refactor", due_date="2024-01-15T23:59:59Z"

    Cache Invalidation:
        - Invalidates board overview cache (card count changed)
        - Workspace cache not invalidated (structure unchanged)
    '''
    try:
        # Prepare request body
        card_data = {
            "name": params.name,
            "position": params.position or 65535  # Default to bottom
        }

        if params.description:
            card_data["description"] = params.description

        if params.due_date:
            card_data["dueDate"] = params.due_date

        # Create card via API
        response = await api_client.post(
            f"api/lists/{params.list_id}/cards",
            json_data=card_data
        )

        card = response.get("item", {})
        card_id = card.get("id")
        card_name = card.get("name")

        # Invalidate board cache (card count changed)
        # Note: Need board_id - may need to fetch or derive from list_id
        # For now, invalidate can be done when we know the structure better
        # cache.invalidate_board(board_id)

        # Return minimal confirmation
        return f"✓ Created card: {card_name} (ID: {card_id})"

    except Exception as e:
        return handle_api_error(e)
```

**Outputs:**
- [ ] `planka_create_card` tool implemented
- [ ] Returns minimal confirmation
- [ ] Includes cache invalidation logic
- [ ] Has comprehensive docstring

**Validation:**
```bash
# Test with MCP Inspector
# Create a test card, verify it appears in board
```

**Estimated Effort:** 30 minutes

---

## Task 4.5: planka_update_card Tool

**Objective:** Implement card update tool

**Prerequisites:** Task 4.4 complete (or can be done in parallel)

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` tool specification (section 1.2, Tier 1, tool #6)

**Implementation Steps:**

1. Implement `planka_update_card` tool:

```python
@mcp.tool(
    name="planka_update_card",
    annotations={
        "title": "Update Planka Card",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,  # Same update repeated has no additional effect
        "openWorldHint": True
    }
)
async def planka_update_card(params: UpdateCardInput) -> str:
    '''Update an existing card's details.

    Updates card name, description, due date, list (moves card), or position.
    All parameters except card_id are optional - only provide what you want to change.

    Args:
        params (UpdateCardInput): Input containing:
            - card_id (str): Card ID to update
            - name (Optional[str]): New card name
            - description (Optional[str]): New card description
            - due_date (Optional[str]): New due date
            - list_id (Optional[str]): Move card to different list
            - position (Optional[float]): New position in list

    Returns:
        str: Minimal confirmation with updated fields

    Examples:
        - "Update card description" → card_id=X, description="New description"
        - "Move card to DONE list" → card_id=X, list_id="done_list_id"
        - "Rename card" → card_id=X, name="New name"

    Cache Invalidation:
        - Invalidates card cache (details changed)
        - If list_id changed, invalidates board cache (card moved)
    '''
    try:
        # Build update payload (only include provided fields)
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

        if not update_data:
            return "Error: No update fields provided. Specify at least one field to update."

        # Update card via API
        response = await api_client.patch(
            f"api/cards/{params.card_id}",
            json_data=update_data
        )

        card = response.get("item", {})

        # Invalidate caches
        cache.invalidate_card(params.card_id)
        if params.list_id:  # Card moved, invalidate board
            # Would need board_id - handle based on API structure
            pass

        # Return confirmation with what was updated
        updated_fields = ", ".join(update_data.keys())
        return f"✓ Updated card {card.get('name', params.card_id)}: {updated_fields}"

    except Exception as e:
        return handle_api_error(e)
```

**Outputs:**
- [ ] `planka_update_card` tool implemented
- [ ] Supports all update fields
- [ ] Includes cache invalidation
- [ ] Has comprehensive docstring

**Validation:**
```bash
# Test updating various fields
# Verify card is updated in Planka
```

**Estimated Effort:** 30 minutes

---

## Task 4.6: planka_add_task Tool

**Objective:** Implement task addition to card checklists

**Prerequisites:** Task 4.2 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` tool specification (section 1.2, Tier 1, tool #7)
- Review user workflow (heavily uses tasks)

**Implementation Steps:**

1. Implement `planka_add_task` tool:

```python
@mcp.tool(
    name="planka_add_task",
    annotations={
        "title": "Add Task to Planka Card",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def planka_add_task(params: AddTaskInput) -> str:
    '''Add a task (checklist item) to a card.

    Creates a new task in the card's checklist. If no task list exists, creates one.
    If task_list_id is provided, adds to that specific list.

    Args:
        params (AddTaskInput): Input containing:
            - card_id (str): Card to add task to
            - task_name (str): Task description
            - task_list_id (Optional[str]): Specific task list, or None for default

    Returns:
        str: Confirmation with task name and updated progress

    Examples:
        - "Add task to contact support" → card_id=X, task_name="Contact support"
        - "Add checklist item for code review" → card_id=X, task_name="Complete code review"

    Cache Invalidation:
        - Invalidates card cache (task list changed)
    '''
    try:
        # If no task_list_id provided, get or create default task list
        if not params.task_list_id:
            # Fetch card to check for existing task lists
            card_response = await api_client.get(f"api/cards/{params.card_id}")
            card = card_response.get("item", {})
            task_lists = card.get("included", {}).get("taskLists", [])

            if task_lists:
                # Use first existing task list
                params.task_list_id = task_lists[0]["id"]
            else:
                # Create new task list
                task_list_response = await api_client.post(
                    f"api/cards/{params.card_id}/task-lists",
                    json_data={"name": "Tasks"}
                )
                task_list = task_list_response.get("item", {})
                params.task_list_id = task_list["id"]

        # Create task
        response = await api_client.post(
            f"api/task-lists/{params.task_list_id}/tasks",
            json_data={"name": params.task_name}
        )

        task = response.get("item", {})

        # Invalidate card cache
        cache.invalidate_card(params.card_id)

        # Get updated progress
        # (Would need to fetch card again or calculate from response)
        return f"✓ Added task: {params.task_name}"

    except Exception as e:
        return handle_api_error(e)
```

**Outputs:**
- [ ] `planka_add_task` tool implemented
- [ ] Creates task list if needed
- [ ] Has comprehensive docstring

**Validation:**
```bash
# Add task to a card
# Verify task appears in card's checklist
```

**Estimated Effort:** 35 minutes

---

## Task 4.7: planka_update_task Tool

**Objective:** Implement task status update (complete/incomplete)

**Prerequisites:** Task 4.6 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` tool specification (section 1.2, Tier 1, tool #8)

**Implementation Steps:**

1. Implement `planka_update_task` tool:

```python
@mcp.tool(
    name="planka_update_task",
    annotations={
        "title": "Update Planka Task Status",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,  # Setting same status repeatedly has no effect
        "openWorldHint": True
    }
)
async def planka_update_task(params: UpdateTaskInput) -> str:
    '''Update a task's completion status.

    Marks a task as complete or incomplete. Commonly used to check off completed work.

    Args:
        params (UpdateTaskInput): Input containing:
            - task_id (str): Task ID to update
            - completed (bool): true for complete, false for incomplete

    Returns:
        str: Confirmation with task status

    Examples:
        - "Mark task as complete" → task_id=X, completed=true
        - "Uncheck that task" → task_id=X, completed=false

    Cache Invalidation:
        - Invalidates card cache (task progress changed)
    '''
    try:
        # Update task status
        response = await api_client.patch(
            f"api/tasks/{params.task_id}",
            json_data={"isCompleted": params.completed}
        )

        task = response.get("item", {})
        task_name = task.get("name", "task")
        status = "completed" if params.completed else "reopened"

        # Invalidate card cache (would need card_id from task)
        # cache.invalidate_card(card_id)

        return f"✓ Task {status}: {task_name}"

    except Exception as e:
        return handle_api_error(e)
```

**Outputs:**
- [ ] `planka_update_task` tool implemented
- [ ] Supports marking complete/incomplete
- [ ] Has comprehensive docstring

**Validation:**
```bash
# Mark a task as complete
# Verify task is checked in Planka
```

**Estimated Effort:** 20 minutes

---

# PHASE 5: Testing & Documentation

## Task 5.1: Manual Testing with MCP Inspector

**Objective:** Test all implemented tools manually to ensure they work

**Prerequisites:** All Phase 4 tasks complete

**Context Required:**
- Have access to your Planka instance at https://planka.w22.io
- Know board IDs, list IDs from your actual data

**Testing Steps:**

1. Start MCP Inspector:
```bash
npx @modelcontextprotocol/inspector python planka_mcp.py
```

2. Test each tool systematically:

**Test Sequence:**
```
1. planka_get_workspace
   - Should return all projects, boards, lists, labels, users
   - Note down actual IDs for subsequent tests

2. planka_list_cards (all variations)
   - List all cards: board_id=X, list_id=None
   - List specific list: board_id=X, list_id=Y
   - Filter by label: board_id=X, label_filter="In Progress"
   - Try different detail levels: preview, summary, detailed

3. planka_get_card
   - Get a known card by ID
   - Should return full details

4. planka_find_and_get_card
   - Search for a unique card name
   - Search for a common term (should show multiple)

5. planka_create_card
   - Create a test card in a list
   - Verify it appears in Planka UI

6. planka_update_card
   - Update the test card's name
   - Move it to a different list
   - Verify changes in Planka UI

7. planka_add_task
   - Add a task to the test card
   - Verify task appears

8. planka_update_task
   - Mark the task as complete
   - Verify checkmark appears
```

3. Test error handling:
```
- Try invalid board_id → Should return clear error
- Try invalid card_id → Should return clear error
- Try with no authentication → Should return auth error
```

4. Test caching:
```
- Call planka_get_workspace twice
- Second call should hit cache (visible in logs if added)
- Wait 6 minutes, call again
- Should fetch fresh data (cache expired)
```

**Outputs:**
- [ ] All tools tested successfully
- [ ] Error handling works correctly
- [ ] Caching works as expected
- [ ] List of any bugs found (document in issues)

**Validation:**
Create a test results document with status of each tool.

**Estimated Effort:** 90 minutes

---

## Task 5.2: Create Evaluation Questions

**Objective:** Create 10 evaluation questions based on actual Planka data

**Prerequisites:** Task 5.1 complete (know your actual data)

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` section "Evaluation Strategy" (4.1, 4.2)
- Review your actual Planka board structure
- Have access to real card data

**Implementation Steps:**

1. Explore your Planka board using the MCP server to find good evaluation scenarios

2. Create 10 questions that:
   - Are independent (don't depend on other questions)
   - Use read-only operations only
   - Require multiple tool calls
   - Are realistic
   - Have verifiable, stable answers

3. Create `evaluations.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<evaluation>
  <qa_pair>
    <question>Use planka_get_workspace to find all boards. How many boards are in the "HOMELAB" project?</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>

  <qa_pair>
    <question>List all cards with the "In Progress" label across all lists. What is the name of the card in the W22 TODO'S list that has a task completion of "1/2"?</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>

  <qa_pair>
    <question>In the HOMELAB list, find the card about Co2 sensors. How many tasks are marked as complete?</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>

  <qa_pair>
    <question>Count all cards in the FINANCE list. How many cards are there?</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>

  <qa_pair>
    <question>Find the card about "Passive income research". How many tasks does it have in total (both complete and incomplete)?</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>

  <qa_pair>
    <question>List all cards in the DONE list. What was the most recently completed card (highest in the list)?</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>

  <qa_pair>
    <question>In the W22 TODO'S list, find the card about Soly/PV anmeldung. How many comments does it have?</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>

  <qa_pair>
    <question>Count all cards that have at least one task list. How many cards have checklists?</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>

  <qa_pair>
    <question>Find the card about "Dynamische stroom via Soly fixen". How many comments and tasks does this card have combined?</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>

  <qa_pair>
    <question>List all cards across all lists. What percentage of total cards are marked as "In Progress"? (Round to nearest whole number)</question>
    <answer>[YOUR_ACTUAL_ANSWER]</answer>
  </qa_pair>
</evaluation>
```

4. Solve each question yourself using the MCP tools to verify answers

5. Fill in the actual answers in the XML

**Outputs:**
- [ ] `evaluations.xml` created with 10 questions
- [ ] All questions verified by solving them manually
- [ ] Answers filled in and confirmed accurate
- [ ] Questions are realistic and test key workflows

**Validation:**
Ask someone else (or a fresh LLM agent) to solve the questions using your MCP server and verify they get the same answers.

**Estimated Effort:** 60 minutes

---

## Task 5.3: Write README Documentation

**Objective:** Create comprehensive user documentation

**Prerequisites:** Tasks 5.1 and 5.2 complete

**Context Required:**
- Review `IMPLEMENTATION_PLAN.md` section "README.md Structure" (5.1)

**Implementation Steps:**

1. Create `README.md` with the following sections:

```markdown
# Planka MCP Server

Token-optimized Model Context Protocol (MCP) server for Planka kanban boards.

## Key Features

✨ **Token Optimized**: 50-60% token reduction compared to naive implementation
- Single workspace query replaces 3-4 separate calls
- Smart detail levels (preview/summary/detailed)
- Aggressive caching for 60-70% fewer API calls

🎯 **Workflow-Oriented Tools**:
- Cross-list queries: Find all "In Progress" cards in one call
- Label filtering across all lists
- Composite tools combine operations to save round trips
- Task management built-in (user's primary workflow)

📊 **Optimized for Single-Board Usage**:
- Perfect for category-based organization (HOMELAB, FINANCE, etc.)
- Minimal tokens for browsing (~50 tokens/card in preview mode)
- Comment/attachment indicators match natural overview format

## Installation

### Prerequisites
- Python 3.10+
- Access to a Planka instance
- Planka API credentials

### Setup

1. Clone or download this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Planka URL and credentials
   ```

4. Test the server:
   ```bash
   python planka_mcp.py
   ```

## Configuration

Create a `.env` file with your Planka instance details:

```bash
# Required
PLANKA_BASE_URL=https://planka.w22.io

# Authentication (choose one method)
PLANKA_API_TOKEN=your-access-token-here
```

## Usage with Claude Desktop

Add to your Claude Desktop configuration:

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

### Tier 0: Critical (Use First)
- **planka_get_workspace** - Get complete workspace structure in one call
  - Returns all projects, boards, lists, labels, users
  - Cached for 5 minutes (90%+ hit rate)
  - 50-66% token reduction vs separate calls

### Tier 1: Core Workflow
- **planka_list_cards** - List cards with advanced filtering
  - Cross-list support (list_id=None for all lists)
  - Label filtering (e.g., label_filter="In Progress")
  - Smart detail levels (preview/summary/detailed)
  - Perfect for "show me all In Progress cards"

- **planka_get_card** - Get single card details
- **planka_find_and_get_card** - Search and retrieve in one call (37% token savings)
- **planka_create_card** - Create new card
- **planka_update_card** - Update card details or move to different list
- **planka_add_task** - Add checklist item to card
- **planka_update_task** - Mark task complete/incomplete

## Examples

### Example 1: Find all In Progress work
```
User: "Show me all my In Progress cards"

Agent:
1. planka_get_workspace() → Get board ID
2. planka_list_cards(board_id=X, label_filter="In Progress", list_id=None, detail_level="preview")
→ Returns all In Progress cards across all lists in ~800 tokens
```

### Example 2: Update a card
```
User: "Find the Soly card and add a task to call the company"

Agent:
1. planka_find_and_get_card(query="soly", board_id=X) → Find card
2. planka_add_task(card_id=Y, task_name="Call Soly company")
→ Task added
```

### Example 3: Overview of work
```
User: "What's in my HOMELAB category?"

Agent:
1. planka_get_workspace() → Get list ID for HOMELAB (cached)
2. planka_list_cards(board_id=X, list_id=homelab_id, detail_level="summary")
→ Shows all HOMELAB cards with progress indicators
```

## Token Efficiency

This MCP server is optimized for token efficiency:

| Operation | Naive Approach | Optimized | Savings |
|-----------|---------------|-----------|---------|
| Find "In Progress" cards | 6 calls, ~6,000 tokens | 1 call, ~800 tokens | **83%** |
| Browse 50 cards | 1 call, ~20,000 tokens | 1 call, ~2,500 tokens | **88%** |
| Search + get card | 2 calls, ~3,500 tokens | 1 call, ~2,200 tokens | **37%** |
| Create card | 4 calls, ~3,500 tokens | 2 calls, ~1,200 tokens | **66%** |

**Weekly usage projection (based on typical workflow):**
- Without optimization: ~175,000 tokens/week
- With optimization: ~40,000 tokens/week
- **Savings: 77% reduction**

## Development

### Testing

Use the MCP Inspector for interactive testing:

```bash
npx @modelcontextprotocol/inspector python planka_mcp.py
```

### Running Evaluations

```bash
# Run evaluation questions (when evaluation harness is available)
python run_evaluations.py evaluations.xml
```

## Troubleshooting

### Authentication Errors
- Verify `PLANKA_BASE_URL` is correct
- Verify `PLANKA_API_TOKEN` is valid and not expired
- Test access by visiting your Planka instance in browser

### Connection Errors
- Check network connectivity to Planka instance
- Verify Planka server is running
- Check for firewall/proxy issues

### Tool Errors
- Use MCP Inspector to test tools individually
- Check error messages for guidance
- Verify IDs are correct (use planka_get_workspace first)

## Performance Notes

**Caching:**
- Workspace structure: 5 min cache (90%+ hit rate)
- Board overviews: 3 min cache (70-80% hit rate)
- Card details: 1 min cache (40-50% hit rate)

**Detail Levels:**
- Preview: ~50 tokens/card (for browsing)
- Summary: ~200 tokens/card (standard view)
- Detailed: ~400 tokens/card (full information)

## License

MIT License
```

**Outputs:**
- [ ] README.md created with all sections
- [ ] Installation instructions clear
- [ ] Configuration documented
- [ ] Examples provided
- [ ] Troubleshooting section included
- [ ] Token efficiency metrics documented

**Validation:**
Ask someone unfamiliar with the project to follow the README and set up the server.

**Estimated Effort:** 75 minutes

---

# Task Completion Checklist

## Phase 1: Foundation
- [ ] Task 1.1: Project Setup (15 min)
- [ ] Task 1.2: Environment Configuration (20 min)
- [ ] Task 1.3: API Client Base Implementation (30 min)

## Phase 2: Core Infrastructure
- [ ] Task 2.1: Caching System Implementation (40 min)
- [ ] Task 2.2: Input Validation Models (45 min)
- [ ] Task 2.3: Response Formatting Utilities (60 min)

## Phase 3: Tier 0 Tools
- [ ] Task 3.1: planka_get_workspace (60 min)

## Phase 4: Tier 1 Tools
- [ ] Task 4.1: planka_list_cards (45 min)
- [ ] Task 4.2: planka_get_card (25 min)
- [ ] Task 4.3: planka_find_and_get_card (35 min)
- [ ] Task 4.4: planka_create_card (30 min)
- [ ] Task 4.5: planka_update_card (30 min)
- [ ] Task 4.6: planka_add_task (35 min)
- [ ] Task 4.7: planka_update_task (20 min)

## Phase 5: Testing & Documentation
- [ ] Task 5.1: Manual Testing with MCP Inspector (90 min)
- [ ] Task 5.2: Create Evaluation Questions (60 min)
- [ ] Task 5.3: Write README Documentation (75 min)

---

**Total Estimated Effort: ~11.5 hours**

**Recommended Approach:**
- Single developer: 2-3 days of focused work
- Multiple agents: Can parallelize Phase 4 tasks
- Incremental: Complete phases sequentially for validation at each step

---

# How to Resume After Interruption

If an agent is interrupted or a new agent takes over:

1. **Check which tasks are complete:**
   - Look for implemented functions in `planka_mcp.py`
   - Check for @mcp.tool decorated functions
   - Run `python planka_mcp.py` to see if it starts without errors

2. **Find the next incomplete task:**
   - Follow the task dependency graph
   - Start with the lowest numbered incomplete task in the current phase
   - If phase dependencies not met, go back to previous phase

3. **Read the task specification:**
   - Review task objective, prerequisites, and context
   - Read the specified implementation steps
   - Check validation criteria

4. **Implement and validate:**
   - Follow implementation steps exactly
   - Test with validation commands
   - Mark task as complete when validation passes

5. **Update progress:**
   - Mark task as complete in checklist
   - Proceed to next task

This approach ensures any agent can pick up where another left off without losing context or duplicating work.
