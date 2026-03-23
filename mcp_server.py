#!/usr/bin/env python3
"""
Planka MCP Server

Supports both stdio (for local Claude Code) and streamable-http (for remote access)
transport modes, controlled by the MCP_TRANSPORT environment variable.
"""
import os
import sys
from contextlib import asynccontextmanager

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from planka_mcp.api_client import PlankaAPIClient, initialize_auth
from planka_mcp.cache import PlankaCache
from planka_mcp.handlers import (
    planka_get_workspace, planka_list_cards, planka_find_and_get_card,
    planka_get_card, planka_create_card, planka_update_card, planka_delete_card,
    planka_add_task, planka_update_task, planka_add_card_label,
    planka_remove_card_label, planka_delete_task
)
from planka_mcp.models import (
    GetWorkspaceInput, ListCardsInput, GetCardInput, CreateCardInput,
    UpdateCardInput, FindAndGetCardInput, AddTaskInput, UpdateTaskInput,
    AddCardLabelInput, RemoveCardLabelInput, DeleteCardInput, DeleteTaskInput
)
from mcp.server.fastmcp import FastMCP


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Initialize and clean up server resources."""
    import planka_mcp.instances as instances
    try:
        token = await initialize_auth()
        base_url = os.getenv("PLANKA_BASE_URL")
        instances.api_client = PlankaAPIClient(base_url, token)
        instances.cache = PlankaCache()
        print(f"Planka MCP Server initialized, connected to: {base_url}", file=sys.stderr, flush=True)
        yield {}
    except Exception as e:
        print(f"Failed to initialize server: {e}", file=sys.stderr, flush=True)
        raise
    finally:
        if instances.api_client:
            await instances.api_client.close()
        print("Planka MCP Server shut down", file=sys.stderr, flush=True)


# Create FastMCP instance with dual transport support
mcp = FastMCP(
    "planka_mcp",
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
    streamable_http_path="/",
    lifespan=server_lifespan,
)


# Register MCP tools
@mcp.tool("planka_get_workspace")
async def mcp_get_workspace(params: GetWorkspaceInput):
    """Get complete workspace structure (projects, boards, lists, labels, users)."""
    return await planka_get_workspace(params)

@mcp.tool("planka_list_cards")
async def mcp_list_cards(params: ListCardsInput):
    """List cards with filtering and pagination options."""
    return await planka_list_cards(params)

@mcp.tool("planka_find_and_get_card")
async def mcp_find_and_get_card(params: FindAndGetCardInput):
    """Find and get card details by search query."""
    return await planka_find_and_get_card(params)

@mcp.tool("planka_get_card")
async def mcp_get_card(params: GetCardInput):
    """Get detailed information about a specific card."""
    return await planka_get_card(params)

@mcp.tool("planka_create_card")
async def mcp_create_card(params: CreateCardInput):
    """Create a new card in a specified list."""
    return await planka_create_card(params)

@mcp.tool("planka_update_card")
async def mcp_update_card(params: UpdateCardInput):
    """Update an existing card's properties."""
    return await planka_update_card(params)

@mcp.tool("planka_add_task")
async def mcp_add_task(params: AddTaskInput):
    """Add a task to a card."""
    return await planka_add_task(params)

@mcp.tool("planka_update_task")
async def mcp_update_task(params: UpdateTaskInput):
    """Update a task's completion status."""
    return await planka_update_task(params)

@mcp.tool("planka_add_card_label")
async def mcp_add_card_label(params: AddCardLabelInput):
    """Add a label to a card."""
    return await planka_add_card_label(params)

@mcp.tool("planka_remove_card_label")
async def mcp_remove_card_label(params: RemoveCardLabelInput):
    """Remove a label from a card."""
    return await planka_remove_card_label(params)

@mcp.tool("planka_delete_card")
async def mcp_delete_card(params: DeleteCardInput):
    """Delete a card from Planka."""
    return await planka_delete_card(params)

@mcp.tool("planka_delete_task")
async def mcp_delete_task(params: DeleteTaskInput):
    """Delete a task from a card."""
    return await planka_delete_task(params)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
