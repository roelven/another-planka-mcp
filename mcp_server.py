#!/usr/bin/env python3
"""
Planka MCP Server - Direct MCP Protocol Entry Point

This is a simplified entry point specifically for MCP protocol communication.
It bypasses the FastAPI layer and connects directly to the MCP protocol.
"""
import os
import sys
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from planka_mcp.api_client import PlankaAPIClient, initialize_auth
from planka_mcp.cache import PlankaCache
from planka_mcp.handlers import (
    planka_get_workspace, planka_list_cards, planka_find_and_get_card,
    planka_get_card, planka_create_card, planka_update_card,
    planka_add_task, planka_update_task, planka_add_card_label,
    planka_remove_card_label
)
from planka_mcp.models import (
    GetWorkspaceInput, ListCardsInput, GetCardInput, CreateCardInput,
    UpdateCardInput, FindAndGetCardInput, AddTaskInput, UpdateTaskInput,
    AddCardLabelInput, RemoveCardLabelInput
)
from mcp.server.fastmcp import FastMCP

# Global instances
api_client = None
cache = None

# Create FastMCP instance
mcp = FastMCP("planka_mcp")

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

async def initialize_server():
    """Initialize the server components."""
    global api_client, cache
    
    try:
        # Initialize authentication
        token = await initialize_auth()
        base_url = os.getenv("PLANKA_BASE_URL")
        
        # Create API client and cache
        api_client = PlankaAPIClient(base_url, token)
        cache = PlankaCache()
        
        # Inject instances into the handlers module
        import planka_mcp.instances
        planka_mcp.instances.api_client = api_client
        planka_mcp.instances.cache = cache
        
        print(f"Planka MCP Server initialized successfully", file=sys.stderr, flush=True)
        print(f"Connected to: {base_url}", file=sys.stderr, flush=True)
        print("Waiting for MCP protocol messages...", file=sys.stderr, flush=True)
        
    except Exception as e:
        print(f"Failed to initialize server: {e}", file=sys.stderr, flush=True)
        raise

async def cleanup_server():
    """Clean up server resources."""
    global api_client
    
    if api_client:
        await api_client.close()
        print("Planka MCP Server shut down successfully", file=sys.stderr, flush=True)

async def main():
    """Main entry point for MCP server."""
    try:
        await initialize_server()
        await mcp.run_stdio_async()
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr, flush=True)
        raise
    finally:
        await cleanup_server()

if __name__ == "__main__":
    asyncio.run(main())