"""
Planka MCP Server - Modular Package

This package provides tools to interact with Planka kanban boards.
"""

from .server import mcp
from .instances import api_client, cache
from .handlers import (
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
    fetch_workspace_data,
    planka_get_workspace
)
from .models import (
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
    RemoveCardLabelInput,
    DeleteCardInput,
    DeleteTaskInput
)
from .cache import CacheEntry, PlankaCache
from .utils import handle_api_error, ResponseFormatter, PaginationHelper
from .api_client import PlankaAPIClient

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
    'DeleteCardInput',
    'DeleteTaskInput',
    'CacheEntry',
    'PlankaCache',
    'handle_api_error',
    'ResponseFormatter',
    'PaginationHelper',
    'PlankaAPIClient'
]