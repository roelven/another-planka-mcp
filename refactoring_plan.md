# Planka MCP Refactoring Plan

## Current State Analysis

**File:** `planka_mcp.py` (1588 lines)
**Current Structure:**
- Single monolithic file with mixed concerns
- 9 MCP tool functions
- 9 Pydantic input models
- 3 Enum classes
- Cache system (`CacheEntry`, `PlankaCache`)
- API client (`PlankaAPIClient`)
- Response formatting (`ResponseFormatter`)
- Pagination helper (`PaginationHelper`)
- Error handling (`handle_api_error`)
- Authentication (`initialize_auth`)
- Server lifecycle (`initialize_server`, `cleanup_server`)
- Main entry point

**Tests:** Comprehensive test suite in `tests/` directory (4208 total lines)

## Proposed Modular Structure

```
planka_mcp/
├── __init__.py                 # Package exports
├── models.py                   # Data models, enums, schemas
├── cache.py                    # Cache system classes
├── api_client.py               # API client and authentication
├── utils.py                    # ResponseFormatter, PaginationHelper, error handling
├── handlers/                   # Tool implementations
│   ├── __init__.py
│   ├── workspace.py            # planka_get_workspace
│   ├── cards.py                # planka_list_cards, planka_get_card, planka_create_card, planka_update_card
│   ├── search.py               # planka_find_and_get_card
│   └── tasks_labels.py         # planka_add_task, planka_update_task, planka_add_card_label, planka_remove_card_label
└── server.py                   # Main entry point and MCP initialization
```

## Migration Steps

### Phase 1: Extract Core Components (Models, Cache, API Client)
1. **Create `models.py`** - Move enums (`ResponseFormat`, `DetailLevel`, `ResponseContext`) and Pydantic models
2. **Create `cache.py`** - Move `CacheEntry` and `PlankaCache` classes
3. **Create `api_client.py`** - Move `PlankaAPIClient` and `initialize_auth` function
4. **Create `utils.py`** - Move `ResponseFormatter`, `PaginationHelper`, `handle_api_error`

### Phase 2: Extract Tool Handlers
5. **Create handlers directory structure**
6. **Create `handlers/workspace.py`** - Move `planka_get_workspace` and `fetch_workspace_data`
7. **Create `handlers/cards.py`** - Move card-related tools
8. **Create `handlers/search.py`** - Move `planka_find_and_get_card`
9. **Create `handlers/tasks_labels.py`** - Move task and label tools

### Phase 3: Refactor Main File
10. **Create `server.py`** - Move MCP initialization, server lifecycle, main entry point
11. **Update original `planka_mcp.py`** to import from new modules (temporary bridge)
12. **Update test imports** to use new module structure

### Phase 4: Cleanup and Testing
13. **Remove original `planka_mcp.py`** once everything works
14. **Run tests** to verify functionality
15. **Update documentation** if needed

## Detailed Module Responsibilities

### `models.py`
- Enums: `ResponseFormat`, `DetailLevel`, `ResponseContext`
- Pydantic input models (9 classes):
  - `GetWorkspaceInput`
  - `ListCardsInput`
  - `GetCardInput`
  - `CreateCardInput`
  - `UpdateCardInput`
  - `FindAndGetCardInput`
  - `AddTaskInput`
  - `UpdateTaskInput`
  - `AddCardLabelInput`
  - `RemoveCardLabelInput`

### `cache.py`
- `CacheEntry` dataclass
- `PlankaCache` class with multi-tier caching
- Cache statistics and cleanup methods

### `api_client.py`
- `PlankaAPIClient` class for HTTP operations
- `initialize_auth()` function for authentication
- Environment variable reading

### `utils.py`
- `ResponseFormatter` class with static methods for formatting
- `PaginationHelper` class with static pagination methods
- `handle_api_error()` function for error handling

### `handlers/workspace.py`
- `planka_get_workspace()` tool
- `fetch_workspace_data()` helper function

### `handlers/cards.py`
- `planka_list_cards()`
- `planka_get_card()`
- `planka_create_card()`
- `planka_update_card()`

### `handlers/search.py`
- `planka_find_and_get_card()`

### `handlers/tasks_labels.py`
- `planka_add_task()`
- `planka_update_task()`
- `planka_add_card_label()`
- `planka_remove_card_label()`

### `server.py`
- MCP server initialization (`mcp = FastMCP("planka_mcp")`)
- Global instances (`api_client`, `cache`)
- `initialize_server()` and `cleanup_server()`
- Main entry point with `if __name__ == "__main__":`

## Dependency Flow

```
server.py → api_client.py, cache.py
handlers/* → models.py, api_client.py, cache.py, utils.py
utils.py → models.py
api_client.py → models.py (for type hints)
```

## Import Strategy

- Use absolute imports within package
- No circular dependencies (unidirectional flow)
- Type-only imports for TYPE_CHECKING where needed
- `__init__.py` files to expose public APIs

## Evaluation Criteria Against Rubric

### 1. Module Decomposition (Target: 22-25/25)
- Clear separation of concerns ✓
- Each module has single responsibility ✓
- Dependencies flow in one direction ✓
- Logical file structure ✓

### 2. Preserved Functionality (Target: 27-30/30)
- All existing tests must pass ✓
- All MCP tools remain registered and callable ✓
- Error handling logic preserved ✓
- Caching behavior unchanged ✓

### 3. Import Management (Target: 13-15/15)
- Clean `__init__.py` exports ✓
- No `import *` usage ✓
- Absolute imports preferred ✓
- No circular dependencies ✓

### 4. Configuration & Constants (Target: 9-10/10)
- Extract magic numbers to `constants.py` or module-level ✓
- Centralize environment variable reading ✓
- Single source of truth for configuration ✓

### 5. Type Safety & Documentation (Target: 9-10/10)
- Preserve existing type hints ✓
- Maintain existing docstrings ✓
- Add module-level docstrings ✓
- Keep inline comments explaining "why" ✓

### 6. Dependency Injection & Testability (Target: 9-10/10)
- Dependencies passed as parameters (already done) ✓
- Global `api_client` and `cache` injected via `initialize_server()` ✓
- Easy to mock for testing ✓

## Git Commit Strategy

Each phase will be committed separately:
1. Commit 1: Create module files with extracted code
2. Commit 2: Update imports in main file
3. Commit 3: Update test imports
4. Commit 4: Remove old monolithic file
5. Commit 5: Final cleanup and documentation

## Risk Mitigation

1. **Preserve functionality**: Run tests after each phase
2. **Avoid circular imports**: Careful dependency planning
3. **Maintain backwards compatibility**: Keep original API surface
4. **Test thoroughly**: Run existing test suite frequently
5. **Incremental migration**: Use temporary bridge imports

## Success Criteria

- [ ] All existing tests pass
- [ ] No runtime errors on startup
- [ ] All MCP tools functional
- [ ] Codebase easier to navigate
- [ ] No circular dependencies
- [ ] Clear module responsibilities
- [ ] Maintained type safety and documentation

## Timeline

Each phase should take approximately:
1. Phase 1: 30 minutes
2. Phase 2: 45 minutes
3. Phase 3: 30 minutes
4. Phase 4: 15 minutes

Total estimated time: 2 hours