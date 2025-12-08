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
import os
import sys
import json
from typing import Optional
from .models import GetWorkspaceInput, ListCardsInput, GetCardInput, CreateCardInput, UpdateCardInput, FindAndGetCardInput, AddTaskInput, UpdateTaskInput, AddCardLabelInput, RemoveCardLabelInput
from .cache import PlankaCache
from .api_client import PlankaAPIClient, initialize_auth
from .handlers import planka_get_workspace, planka_list_cards, planka_find_and_get_card, planka_get_card, planka_create_card, planka_update_card, planka_add_task, planka_update_task, planka_add_card_label, planka_remove_card_label, fetch_workspace_data
from .utils import handle_api_error, ResponseFormatter

from .instances import api_client, cache
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("planka_mcp")

# ==================== SERVER LIFECYCLE ====================

async def initialize_server():
    """Initialize API client and cache system on server startup."""
    global api_client, cache

    try:
        token = await initialize_auth()
        base_url = os.getenv("PLANKA_BASE_URL")

        api_client = PlankaAPIClient(base_url, token)
        cache = PlankaCache()

        print(f"Planka MCP Server initialized successfully", file=sys.stderr, flush=True)
        print(f"Connected to: {base_url}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"Failed to initialize server: {e}", file=sys.stderr, flush=True)
        raise

async def cleanup_server():
    """Clean up resources on server shutdown."""
    global api_client

    if api_client:
        await api_client.close()
        print("Planka MCP Server shut down successfully", file=sys.stderr, flush=True)

# ==================== MAIN ====================

if __name__ == "__main__":
    import asyncio

    # Initialize before running
    asyncio.run(initialize_server())

    try:
        mcp.run()
    finally:
        # Cleanup on exit
        asyncio.run(cleanup_server())