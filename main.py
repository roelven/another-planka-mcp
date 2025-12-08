#!/usr/bin/env python3
"""
Planka MCP Server - Bridge file for backward compatibility
"""
# Import all the tool functions from the new modular structure
# This file maintains the original API for backward compatibility
from planka_mcp.server import mcp, api_client, cache
from planka_mcp.handlers import (
    planka_get_workspace,
    planka_list_cards,
    planka_find_and_get_card,
    planka_get_card,
    planka_create_card,
    planka_update_card,
    planka_add_task,
    planka_update_task,
    planka_add_card_label,
    planka_remove_card_label,
    fetch_workspace_data
)

# Import models and enums for backward compatibility
from planka_mcp.models import (
    ResponseFormat,
    DetailLevel,
    ResponseContext,
    GetWorkspaceInput,
    ListCardsInput,
    GetCardInput,
    CreateCardInput,
    UpdateCardInput,
    FindAndGetCardInput,
    AddTaskInput,
    UpdateTaskInput,
    AddCardLabelInput,
    RemoveCardLabelInput
)

# Import cache for backward compatibility
from planka_mcp.cache import CacheEntry, PlankaCache

# Import utils for backward compatibility
from planka_mcp.utils import handle_api_error, ResponseFormatter, PaginationHelper

# Re-export all the tool functions with their original names so existing code keeps working
__all__ = [
    'mcp', 'api_client', 'cache',
    'planka_get_workspace',
    'planka_list_cards',
    'planka_find_and_get_card',
    'planka_get_card',
    'planka_create_card',
    'planka_update_card',
    'planka_add_task',
    'planka_update_task',
    'planka_add_card_label',
    'planka_remove_card_label',
    'fetch_workspace_data',
    'ResponseFormat',
    'DetailLevel',
    'ResponseContext',
    'GetWorkspaceInput',
    'ListCardsInput',
    'GetCardInput',
    'CreateCardInput',
    'UpdateCardInput',
    'FindAndGetCardInput',
    'AddTaskInput',
    'UpdateTaskInput',
    'AddCardLabelInput',
    'RemoveCardLabelInput',
    'CacheEntry',
    'PlankaCache',
    'handle_api_error',
    'ResponseFormatter',
    'PaginationHelper'
]

# This file serves as a bridge to maintain backward compatibility
# while the codebase is refactored into modular components in src/planka_mcp/