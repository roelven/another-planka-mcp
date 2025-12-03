# Token Efficiency Analysis & Optimization Plan

## Current Plan - Token Usage Projection

### Scenario 1: "Create a card in the Backend project"

**Without Optimizations:**
```
Agent workflow:
1. planka_list_projects()           → ~500 tokens (returns all projects with details)
2. planka_list_boards(project_id)   → ~800 tokens (returns all boards with metadata)
3. planka_list_cards(board_id)      → ~2000 tokens (returns cards to find list IDs)
4. planka_create_card(list_id, ...) → ~200 tokens (confirmation)

Total: ~3,500 tokens just for discovery + 1 simple creation
Tool calls: 4
```

### Scenario 2: "Find a card and add a comment"

**Without Optimizations:**
```
Agent workflow:
1. planka_list_projects()           → ~500 tokens
2. planka_list_boards(project_id)   → ~800 tokens
3. planka_search_cards(query)       → ~1500 tokens (search results)
4. planka_get_card(card_id)         → ~2000 tokens (full card details)
5. planka_add_comment(card_id, ...) → ~200 tokens (confirmation)

Total: ~5,000 tokens
Tool calls: 5
```

### Scenario 3: "Show me all critical bugs"

**Without Optimizations:**
```
Agent workflow:
1. planka_list_projects()           → ~500 tokens
2. planka_list_boards(project_id)   → ~800 tokens
3. planka_list_labels(board_id)     → ~300 tokens (find "Critical" label ID)
4. planka_list_cards(board_id)      → ~3000+ tokens (all cards)
5. Filter client-side for label     → 0 tokens (done in agent memory)

Total: ~4,600 tokens
Tool calls: 4-5
```

### **Problem: High Discovery Overhead**

Every task requires 3-5 tool calls and 3,000-5,000 tokens just to navigate the workspace structure before doing actual work. This is expensive and slow.

---

## Optimization Strategy

### 1. **Bootstrap Tool - Massive Token Savings**

**New Tool: `planka_get_workspace`**

Returns the entire workspace structure in ONE call:

```python
@mcp.tool(name="planka_get_workspace")
async def planka_get_workspace(params: GetWorkspaceInput) -> str:
    '''Get complete workspace structure including projects, boards, lists, and labels.

    This tool provides a comprehensive overview of your Planka workspace in a single call.
    Use this at the start of a conversation to understand available projects, boards,
    and lists. The response is cached for 5 minutes to optimize performance.

    Returns:
        Complete workspace structure with:
        - All projects (id, name)
        - All boards per project (id, name, project_id)
        - All lists per board (id, name, board_id, position)
        - All labels per board (id, name, color, board_id)
        - User list (id, name, username)
    '''
    # Implementation with aggressive caching
    pass
```

**Example Response (Markdown):**
```markdown
# Planka Workspace Overview

## Projects (3)

### Backend Development (proj_123)
**Boards:**
- API Development (board_456)
  - Lists: Backlog (list_1), In Progress (list_2), Done (list_3)
  - Labels: Bug 🐛, Feature ✨, Critical 🔴
- Infrastructure (board_789)
  - Lists: To Do (list_4), Doing (list_5), Complete (list_6)
  - Labels: DevOps 🔧, Security 🔒

### Frontend Development (proj_234)
**Boards:**
- UI Components (board_101)
  - Lists: Design (list_7), Development (list_8), Review (list_9)
  - Labels: Design 🎨, Accessibility ♿

## Users (5)
- Alice Smith (@alice, user_1)
- Bob Jones (@bob, user_2)
- Carol White (@carol, user_3)
```

**Token Savings:**
- Before: 3-4 tool calls, ~2,000-3,000 tokens for discovery
- After: 1 tool call, ~1,000 tokens (includes everything)
- **Savings: 50-66% reduction in discovery tokens**
- **Round trips: Reduced from 3-4 to 1**

**Caching Strategy:**
```python
# In-memory cache with TTL
workspace_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 300  # 5 minutes
}

async def get_workspace_cached():
    """Return cached workspace or fetch fresh if expired."""
    now = time.time()
    if (workspace_cache['data'] is not None and
        workspace_cache['timestamp'] is not None and
        now - workspace_cache['timestamp'] < workspace_cache['ttl']):
        return workspace_cache['data']

    # Fetch fresh data
    data = await fetch_workspace_structure()
    workspace_cache['data'] = data
    workspace_cache['timestamp'] = now
    return data
```

---

### 2. **Composite Tools - Reduce Round Trips**

#### **Tool: `planka_find_and_get_card`**

Combines search + get details in one call:

```python
@mcp.tool(name="planka_find_and_get_card")
async def planka_find_and_get_card(params: FindAndGetCardInput) -> str:
    '''Search for a card and return its complete details in one operation.

    This tool combines search and retrieval, saving a round trip. If multiple cards
    match, returns the most relevant one (or prompts for clarification).

    Args:
        query: Search term to find card
        board_id: Optional board filter to narrow search

    Returns:
        Complete card details if found, or list of matches if ambiguous
    '''
    pass
```

**Token Savings:**
- Before: search (1500 tokens) + get (2000 tokens) = 3500 tokens, 2 calls
- After: combined (2200 tokens) = 2200 tokens, 1 call
- **Savings: 37% reduction, 1 fewer tool call**

#### **Tool: `planka_get_board_overview`**

Get board with all lists and summary stats:

```python
@mcp.tool(name="planka_get_board_overview")
async def planka_get_board_overview(params: BoardOverviewInput) -> str:
    '''Get board details with all lists, labels, and card counts.

    Provides a comprehensive board overview without fetching all cards.
    Useful for understanding board structure before querying specific cards.
    '''
    pass
```

**Token Savings:**
- Before: get board + list cards = ~3000 tokens, 2 calls
- After: overview only = ~800 tokens, 1 call (when you don't need all cards)
- **Savings: 73% reduction when you just need structure**

---

### 3. **Smart Response Formats - Minimize Verbosity**

#### **Current Plan Issue:**
Every response includes full context (board name, project name, user details, etc.)

#### **Optimization: Context-Aware Responses**

```python
class ResponseContext(str, Enum):
    """How much context to include in responses."""
    MINIMAL = "minimal"      # IDs only, assume agent has context
    STANDARD = "standard"    # IDs + names (default)
    FULL = "full"           # Complete context with descriptions

class ListCardsInput(BaseModel):
    board_id: str
    response_context: ResponseContext = Field(
        default=ResponseContext.STANDARD,
        description="Context level: 'minimal' (IDs only), 'standard' (IDs+names), 'full' (everything)"
    )
```

**Example Responses:**

**MINIMAL (for agent with context):**
```json
{
  "cards": [
    {"id": "card_123", "name": "Fix login bug", "list": "list_2"},
    {"id": "card_456", "name": "Add OAuth", "list": "list_1"}
  ]
}
```
**~200 tokens**

**STANDARD (default):**
```json
{
  "cards": [
    {
      "id": "card_123",
      "name": "Fix login bug",
      "list": {"id": "list_2", "name": "In Progress"},
      "members": [{"id": "u1", "name": "Alice"}]
    }
  ]
}
```
**~400 tokens**

**FULL (first call or when context needed):**
```json
{
  "board": {"id": "board_456", "name": "API Development", "project": "Backend"},
  "cards": [
    {
      "id": "card_123",
      "name": "Fix login bug",
      "description": "Users report 500 errors...",
      "list": {"id": "list_2", "name": "In Progress", "position": 2},
      "members": [{"id": "u1", "name": "Alice", "email": "alice@example.com"}],
      "labels": [{"id": "l1", "name": "Bug", "color": "red"}],
      "created_at": "2024-02-01T10:00:00Z"
    }
  ]
}
```
**~800 tokens**

**Token Savings:**
- Using MINIMAL after first call: 60-75% reduction on subsequent calls
- Smart agents can request MINIMAL after using `planka_get_workspace`

---

### 4. **Caching Strategy - Leveraging Low Concurrency**

Since you have low concurrent users, aggressive caching is highly effective:

```python
class PlankaCache:
    """Multi-tier caching for Planka data."""

    def __init__(self):
        self.workspace = CacheEntry(ttl=300)      # 5 min - projects/boards/lists
        self.labels = {}                          # Per-board, TTL 600s (10 min)
        self.users = CacheEntry(ttl=300)          # 5 min
        self.cards = {}                           # Per-card, TTL 60s (1 min)
        self.board_overviews = {}                 # Per-board, TTL 180s (3 min)

    async def get_workspace(self):
        """Get cached workspace or fetch if stale."""
        if self.workspace.is_valid():
            return self.workspace.data
        data = await api_client.fetch_workspace()
        self.workspace.set(data)
        return data

    async def get_board_labels(self, board_id: str):
        """Get cached labels for board."""
        if board_id in self.labels and self.labels[board_id].is_valid():
            return self.labels[board_id].data
        data = await api_client.fetch_labels(board_id)
        self.labels[board_id] = CacheEntry(ttl=600, data=data)
        return data

# Global cache instance
cache = PlankaCache()
```

**Cache Hit Rates (Projected):**
- Workspace structure: 90%+ hit rate (changes infrequently)
- Labels: 85%+ hit rate (rarely change)
- Users: 80%+ hit rate (occasional additions)
- Cards: 40-50% hit rate (more dynamic)

**Token Savings from Caching:**
- First conversation: No savings (cache miss)
- Subsequent conversations: 70-80% reduction in API calls
- Within same conversation: 90%+ hit rate on repeated context

---

### 5. **Batch Operations - Multiple Cards at Once**

#### **Tool: `planka_get_cards_batch`**

Get multiple cards in one call:

```python
@mcp.tool(name="planka_get_cards_batch")
async def planka_get_cards_batch(params: GetCardsBatchInput) -> str:
    '''Get details for multiple cards in a single request.

    More efficient than calling planka_get_card multiple times.

    Args:
        card_ids: List of card IDs to fetch (max 50)
        response_context: Context level for responses
    '''
    pass
```

**Token Savings:**
- Before: 5 cards × 2000 tokens = 10,000 tokens, 5 calls
- After: 1 batch call = ~6,000 tokens, 1 call
- **Savings: 40% reduction, 4 fewer tool calls**

---

### 6. **Incremental Card Loading - Lazy Details**

#### **List Cards with "Preview" Mode**

```python
class CardDetailLevel(str, Enum):
    """How much detail to include for cards."""
    PREVIEW = "preview"      # Name, ID, list, due date only
    SUMMARY = "summary"      # + description snippet, member count, task progress
    DETAILED = "detailed"    # Everything including tasks, comments, attachments

# Preview response (~50 tokens per card)
{
  "id": "card_123",
  "name": "Fix login bug",
  "list": "In Progress",
  "due": "2024-02-15",
  "members": 2,
  "tasks": "3/7"
}

# vs Detailed response (~400 tokens per card)
{
  "id": "card_123",
  "name": "Fix login bug",
  "description": "Long description...",
  "list": {"id": "list_2", "name": "In Progress"},
  "members": [{"id": "u1", "name": "Alice"}, ...],
  "tasks": [{"id": "t1", "name": "...", "completed": true}, ...],
  "comments": [...],
  "labels": [...]
}
```

**Token Savings:**
- Listing 50 cards in PREVIEW: ~2,500 tokens
- Listing 50 cards in DETAILED: ~20,000 tokens (would be truncated)
- **Savings: 88% reduction for browsing/scanning**

Agent can request full details only for cards of interest.

---

## Optimized Tool Set - Revised Plan

### **Tier 0: Context & Discovery (NEW)**
1. **`planka_get_workspace`** ⭐ - Complete workspace structure with caching
   - Replaces 3-4 separate discovery calls
   - Cached for 5 minutes
   - Reduces initial token cost by 50-66%

### **Tier 1: Core Workflow Tools (Optimized)**
2. **`planka_list_cards`** - List cards with smart detail levels
   - Add `detail_level: preview | summary | detailed`
   - Add `response_context: minimal | standard | full`
   - Default to `preview` + `standard` for efficiency

3. **`planka_find_and_get_card`** ⭐ - Combined search + get (NEW)
   - Reduces 2 calls to 1
   - 37% token reduction for search-then-get workflows

4. **`planka_get_card`** - Single card details (kept)
   - Add `response_context` parameter

5. **`planka_create_card`** - Create card (kept)

6. **`planka_update_card`** - Update card (kept)

### **Tier 2: Batch & Composite Operations (NEW)**
7. **`planka_get_cards_batch`** ⭐ - Get multiple cards at once
   - 40% token reduction for multi-card queries

8. **`planka_get_board_overview`** ⭐ - Board + lists + card counts
   - Cached for 3 minutes
   - 73% token reduction when you don't need all cards

### **Tier 3: Collaboration & Management**
9. `planka_add_card_member`
10. `planka_remove_card_member`
11. `planka_add_card_label`
12. `planka_remove_card_label`
13. `planka_add_comment`
14. `planka_list_comments` - with caching

### **Tier 4: Advanced**
15. Task management tools
16. Attachment tools
17. Activity tools

---

## Revised Token Usage Projections

### Scenario 1: "Create a card in the Backend project"

**With Optimizations:**
```
Agent workflow:
1. planka_get_workspace()           → ~1000 tokens (cached after first call)
   (Agent now has all project/board/list IDs)
2. planka_create_card(list_id, ...) → ~200 tokens (confirmation)

Total: ~1,200 tokens (vs 3,500 before)
Tool calls: 2 (vs 4 before)
Savings: 66% token reduction, 50% fewer calls
```

### Scenario 2: "Find a card and add a comment"

**With Optimizations:**
```
Agent workflow:
1. planka_get_workspace()               → ~1000 tokens (or 0 if cached in conversation)
2. planka_find_and_get_card(query)      → ~2000 tokens (combined search+get)
3. planka_add_comment(card_id, ...)     → ~200 tokens

Total: ~3,200 tokens (vs 5,000 before)
Tool calls: 3 (vs 5 before)
Savings: 36% token reduction, 40% fewer calls

If workspace cached in same conversation:
Total: ~2,200 tokens
Savings: 56% token reduction
```

### Scenario 3: "Show me all critical bugs"

**With Optimizations:**
```
Agent workflow:
1. planka_get_workspace()           → ~1000 tokens (includes label IDs)
   (Agent knows "Critical" label ID for relevant board)
2. planka_list_cards(
     board_id=...,
     detail_level="preview",
     response_context="minimal"
   )                                → ~1500 tokens (vs 3000+)
3. Filter by label client-side      → 0 tokens

Total: ~2,500 tokens (vs 4,600 before)
Tool calls: 2 (vs 4-5 before)
Savings: 46% token reduction, 50-60% fewer calls
```

### Scenario 4: "What's the status of cards assigned to Alice?"

**With Optimizations:**
```
1. planka_get_workspace()               → ~1000 tokens (cached)
   (Agent knows Alice's user ID)
2. planka_list_cards(
     board_id=...,
     detail_level="preview",
     response_context="minimal"
   )                                    → ~1500 tokens
3. Filter by member client-side         → 0 tokens

Total: ~2,500 tokens
Alternative: Could add member_id filter to API to reduce response
```

---

## Implementation Priority - Revised

### **Phase 1: Core + Optimization** (MVP)
1. ✅ `planka_get_workspace` - Critical for efficiency
2. ✅ `planka_list_cards` - With detail_level + response_context
3. ✅ `planka_get_card` - With response_context
4. ✅ `planka_find_and_get_card` - High-value composite
5. ✅ `planka_create_card`
6. ✅ `planka_update_card`
7. ✅ Implement caching system

### **Phase 2: Extended Efficiency**
8. `planka_get_board_overview` - Composite tool
9. `planka_get_cards_batch` - Batch operations
10. Collaboration tools (members, labels, comments)

---

## Cache Configuration Recommendations

```python
# Optimal cache TTLs for low-concurrency environment
CACHE_CONFIG = {
    'workspace_structure': 300,      # 5 min (projects/boards/lists rarely change)
    'board_labels': 600,             # 10 min (labels rarely change)
    'users': 300,                    # 5 min (user changes infrequent)
    'board_overview': 180,           # 3 min (moderate change rate)
    'card_details': 60,              # 1 min (cards change frequently)
    'card_list': 30,                 # 30 sec (very dynamic)
}

# Cache invalidation triggers
# - Manual: Provide tool to clear cache if needed
# - Automatic: After write operations, invalidate related caches
# - Time-based: TTL expiration

# Example: After creating a card, invalidate card_list cache for that board
@mcp.tool(name="planka_create_card")
async def planka_create_card(...):
    card = await api_client.create_card(...)
    # Invalidate cache
    cache.invalidate_board_cards(card['board_id'])
    return format_card(card)
```

---

## Cost-Benefit Analysis

### **Token Cost Per Session**

**Without Optimizations:**
- Initial discovery: 2,000-3,000 tokens
- Average task: 5,000-6,000 tokens
- 10 tasks in one conversation: ~50,000 tokens

**With Full Optimizations:**
- Initial discovery: 1,000 tokens (workspace)
- Average task: 2,000-3,000 tokens (with caching)
- 10 tasks in one conversation: ~25,000 tokens

**Overall Savings: 50% reduction in token usage**

### **API Call Reduction**

**Before:**
- Discovery: 3-4 calls per task
- Average task: 5-7 API calls
- 10 tasks: 50-70 API calls

**After:**
- Discovery: 1 call (cached for 5 min)
- Average task: 2-3 API calls
- 10 tasks: 20-30 API calls (with caching)

**Overall Savings: 60% reduction in API calls**

---

## Recommendations

### **Must-Have Optimizations:**
1. ✅ **`planka_get_workspace`** - Single biggest impact
2. ✅ **Response detail levels** - Huge savings on list operations
3. ✅ **Workspace caching** - Essential for multi-turn conversations
4. ✅ **Response context modes** - Reduces redundant data

### **High-Value Optimizations:**
5. ✅ **`planka_find_and_get_card`** - Common workflow
6. ✅ **Board overview caching** - Frequently accessed
7. ✅ **Label/user caching** - Rarely changes

### **Nice-to-Have Optimizations:**
8. ⚠️ **Batch operations** - Useful but less common
9. ⚠️ **Card detail caching** - Dynamic data, lower hit rate

### **Development Effort vs. Impact:**

| Optimization | Effort | Token Savings | Call Reduction | Priority |
|--------------|--------|---------------|----------------|----------|
| `planka_get_workspace` | Medium | 50-66% | 50-60% | **CRITICAL** |
| Detail levels | Low | 60-88% | 0% | **CRITICAL** |
| Response context | Low | 30-60% | 0% | **HIGH** |
| Caching system | Medium | 40-70% | 50-80% | **HIGH** |
| `planka_find_and_get_card` | Low | 30-40% | 50% | **HIGH** |
| Batch operations | Medium | 30-40% | 80% | MEDIUM |
| Board overview | Low | 50-70% | 50% | MEDIUM |

---

## Final Recommendations

### **Implement These in Phase 1:**
1. **`planka_get_workspace`** with aggressive caching (5 min TTL)
2. **Detail level support** (`preview`, `summary`, `detailed`)
3. **Response context modes** (`minimal`, `standard`, `full`)
4. **Basic caching system** for workspace, labels, users
5. **`planka_find_and_get_card`** composite tool

### **Expected Results:**
- **50-60% reduction in token usage** compared to naive implementation
- **60-70% reduction in API calls** due to caching
- **Faster agent responses** (fewer round trips)
- **Lower costs** for LLM API usage
- **Better user experience** (quicker task completion)

### **Phase 2 Enhancements:**
- Add batch operations for power users
- Implement smart cache invalidation after write operations
- Add board overview caching
- Consider card preview caching for frequently accessed cards

---

## Conclusion

The optimizations outlined here will make your Planka MCP server **significantly more efficient** for AI agents:

- **Token usage**: 50-60% reduction
- **API calls**: 60-70% reduction
- **Round trips**: 50-60% fewer tool calls
- **Agent experience**: Much faster and cheaper

The key insight is that **workspace structure changes infrequently** in typical project management workflows, so aggressive caching of the project/board/list hierarchy provides massive benefits. Combined with smart response formatting and composite tools, agents can accomplish tasks with far fewer tokens and API calls.

**The optimizations are particularly valuable for:**
- Multi-turn conversations (caching pays off over time)
- Repetitive tasks (workspace structure reused)
- Low-concurrency environments (your use case) where cache hit rates are very high
- Cost-sensitive deployments where LLM token costs matter

I recommend implementing the **Phase 1 optimizations** as part of the MVP, as they provide the highest ROI and are relatively straightforward to implement.
