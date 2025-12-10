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

from . import instances # Import the instances module itself
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, APIRouter, Body

mcp = FastMCP("planka_mcp")

# Create an API Router for your tools
router = APIRouter()

# Expose FastMCP tools as FastAPI endpoints
@router.post("/planka_get_workspace")
async def get_workspace_endpoint(params: GetWorkspaceInput = Body(...)):
    """Get complete workspace structure (projects, boards, lists, labels, users)."""
    return await planka_get_workspace(params)

# Expose the FastMCP app as an ASGI application
mcp_asgi_app = mcp.streamable_http_app()

# Create a FastAPI application
app = FastAPI(
    title="Planka MCP Server",
    description="A FastAPI application serving the Planka MCP server.",
    version="1.0.0",
)

# Mount the FastMCP ASGI application onto the FastAPI app

app.include_router(router)

# ==================== SERVER LIFECYCLE ====================

@app.on_event("startup")
async def startup_event():
    """Initialize API client and cache system on server startup."""
    try:
        token = await initialize_auth()
        base_url = os.getenv("PLANKA_BASE_URL")

        instances.api_client = PlankaAPIClient(base_url, token)
        instances.cache = PlankaCache()

        print(f"Planka MCP Server initialized successfully", file=sys.stderr, flush=True)
        print(f"Connected to: {base_url}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"Failed to initialize server: {e}", file=sys.stderr, flush=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on server shutdown."""
    if instances.api_client:
        await instances.api_client.close()
        print("Planka MCP Server shut down successfully", file=sys.stderr, flush=True)
