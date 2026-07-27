---
name: planka-mcp
description: >
  Skill for managing a Planka Kanban board via the planka-mcp MCP server.
  Use this when asked to create, update, move, or delete cards, tasks, or labels
  in Planka, or when asked about board/backlog/sprint status.
license: MIT
---

# Planka MCP — Skill Reference

## What is this?
Planka is an open-source Kanban project management tool. This skill enables an AI agent to interact with a Planka instance via the `planka-mcp` MCP server, which exposes tools for reading and managing boards, cards, tasks, and labels.

## Setup
- Install `planka-mcp` and register it in your AI harness as an MCP server
- Tools will be available with the prefix `planka-mcp-` (e.g. `planka-mcp-planka_get_workspace`)
- Requires a running Planka instance with valid credentials configured in the MCP server

---

## Mental Model

```
Workspace
└── Project (e.g. "Keystone")
    └── Board (e.g. "WS4 - Essential Eight ML1")
        ├── List (e.g. "BACKLOG", "IN PROGRESS", "DONE", "BLOCKER")
        │   └── Card (a task/ticket)
        │       ├── Description (markdown)
        │       ├── Due date
        │       ├── Labels
        │       └── Task Lists
        │           └── Tasks (checklist items)
        └── Labels (board-scoped, reusable across cards)
```

---

## Available Tools

### `planka_get_workspace`
Returns the full workspace structure: projects, boards, lists, labels, users.  
**Always call this first** in a new session to get IDs needed for other calls.

```json
{ "response_format": "markdown" }
```

---

### `planka_list_cards`
List cards on a board, optionally filtered by list or label.

```json
{
  "board_id": "<board_id>",
  "list_id": "<list_id>",
  "label_filter": "In Progress",
  "detail_level": "summary",
  "limit": 50
}
```

---

### `planka_find_and_get_card`
Search for a card by name or description text. Returns full card detail.

```json
{
  "query": "Test Card for Skill Verification",
  "board_id": "<board_id>"
}
```

---

### `planka_get_card`
Get full details for a known card ID.

```json
{
  "card_id": "<card_id>",
  "response_context": "full"
}
```

---

### `planka_create_card`
Create a new card in a list.

```json
{
  "list_id": "<list_id>",
  "name": "Card title",
  "description": "Markdown description",
  "due_date": "2026-12-31T23:59:59Z",
  "position": null
}
```

---

### `planka_update_card`
Update any combination of a card's name, description, due date, or list (move it).

```json
{
  "card_id": "<card_id>",
  "name": "New title",
  "description": "New description",
  "list_id": "<target_list_id>",
  "due_date": "2026-12-31T00:00:00Z"
}
```

---

### `planka_delete_card`
Permanently delete a card. Irreversible.

```json
{ "card_id": "<card_id>" }
```

---

### `planka_add_task`
Add a checklist task to a card.

```json
{
  "card_id": "<card_id>",
  "task_name": "Review pull request",
  "task_list_name": "Tasks"
}
```

---

### `planka_update_task`
Mark a task complete or incomplete.

```json
{
  "task_id": "<task_id>",
  "is_completed": true
}
```

---

### `planka_delete_task`
Delete a checklist task from a card.

```json
{ "task_id": "<task_id>" }
```

---

### `planka_add_card_label`
Apply an existing label to a card. Labels are board-scoped — get label IDs from `planka_get_workspace`.

```json
{
  "card_id": "<card_id>",
  "label_id": "<label_id>"
}
```

---

### `planka_remove_card_label`
Remove a label from a card.

```json
{
  "card_id": "<card_id>",
  "label_id": "<label_id>"
}
```

---

## Common Workflows

### Move a card to a different list
1. `planka_get_workspace` → get list IDs
2. `planka_find_and_get_card` → get card ID
3. `planka_update_card` with `list_id` set to the target list

### Create a card with tasks
1. `planka_get_workspace` → get target list ID
2. `planka_create_card` → get new card ID
3. `planka_add_task` (repeat for each task)

### Find all in-progress cards
1. `planka_get_workspace` → get board ID and IN PROGRESS list ID
2. `planka_list_cards` with `list_id` = IN PROGRESS list ID

### Label a card
1. `planka_get_workspace` → get label IDs for the board
2. `planka_find_and_get_card` → get card ID
3. `planka_add_card_label`

---

## Agent Instructions (paste into system prompt / custom instructions)

```
You have access to a Planka Kanban board via tools prefixed with `planka-mcp-`.

Rules:
- Always call planka_get_workspace at the start of a session to get current IDs.
  Never hardcode or guess board/list/label IDs.
- Use planka_find_and_get_card to locate a card by name before updating it.
- When moving a card, pass list_id to planka_update_card.
- IDs are large integers as strings — pass them exactly as returned.
- Prefer planka_list_cards over planka_find_and_get_card when you already know the board/list.

Trigger phrases → tools to use:
- "move card to ..."         → planka_update_card (list_id)
- "create a card for ..."    → planka_create_card
- "what's in backlog?"       → planka_list_cards (list_id = BACKLOG list)
- "add a task to ..."        → planka_add_task
- "mark task done"           → planka_update_task (is_completed: true)
- "show me the board"        → planka_get_workspace + planka_list_cards
```

---

## Notes
- All IDs are large integer strings — always pass them as strings, not numbers
- `response_format: "json"` is useful for programmatic parsing; `"markdown"` is better for display
- Labels are board-scoped — a label on one board won't appear on another
- Card positions use floating point numbers; lower = higher in the list
