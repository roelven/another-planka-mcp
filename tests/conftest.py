"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime


@pytest.fixture
def mock_planka_api_client():
    """Mock PlankaAPIClient for testing."""
    from unittest.mock import AsyncMock

    client = AsyncMock()
    client.base_url = "https://test.planka.com"
    client.auth_token = "test-token"

    return client


@pytest.fixture
def mock_cache():
    """Mock PlankaCache for testing."""
    from unittest.mock import Mock

    cache = Mock()
    cache.workspace = None
    cache.board_overviews = {}
    cache.card_details = {}
    cache.stats = {
        "workspace_hits": 0,
        "workspace_misses": 0,
        "board_overview_hits": 0,
        "board_overview_misses": 0,
        "card_hits": 0,
        "card_misses": 0,
    }

    return cache


@pytest.fixture
def sample_workspace_data():
    """Sample workspace data for testing."""
    return {
        "projects": [
            {"id": "proj1", "name": "Test Project"}
        ],
        "boards": {
            "board1": {
                "id": "board1",
                "name": "Test Board",
                "projectId": "proj1",
                "project_name": "Test Project"
            }
        },
        "lists": {
            "list1": {
                "id": "list1",
                "name": "To Do",
                "boardId": "board1",
                "board_name": "Test Board",
                "position": 0
            },
            "list2": {
                "id": "list2",
                "name": "In Progress",
                "boardId": "board1",
                "board_name": "Test Board",
                "position": 1
            }
        },
        "labels": {
            "label1": {
                "id": "label1",
                "name": "Bug",
                "color": "red",
                "boardId": "board1",
                "board_name": "Test Board"
            },
            "label2": {
                "id": "label2",
                "name": "Feature",
                "color": "blue",
                "boardId": "board1",
                "board_name": "Test Board"
            }
        },
        "users": {
            "user1": {
                "id": "user1",
                "name": "Test User",
                "username": "testuser",
                "email": "test@example.com"
            }
        }
    }


@pytest.fixture
def sample_card_data():
    """Sample card data for testing."""
    return {
        "id": "card1",
        "name": "Test Card",
        "description": "This is a test card",
        "listId": "list1",
        "boardId": "board1",
        "position": 65535,
        "dueDate": "2024-12-31T23:59:59Z",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-02T00:00:00Z",
        "memberIds": ["user1"],
        "taskLists": [
            {
                "id": "tasklist1",
                "name": "Tasks",
                "tasks": [
                    {"id": "task1", "name": "Task 1", "isCompleted": True},
                    {"id": "task2", "name": "Task 2", "isCompleted": False}
                ]
            }
        ],
        "comments": [
            {
                "id": "comment1",
                "text": "Test comment",
                "userId": "user1",
                "createdAt": "2024-01-03T00:00:00Z"
            }
        ],
        "attachments": []
    }


@pytest.fixture
def sample_board_response():
    """Sample board API response for testing."""
    return {
        "item": {
            "id": "board1",
            "name": "Test Board",
            "projectId": "proj1"
        },
        "included": {
            "lists": [
                {"id": "list1", "name": "To Do", "boardId": "board1", "position": 0},
                {"id": "list2", "name": "In Progress", "boardId": "board1", "position": 1}
            ],
            "labels": [
                {"id": "label1", "name": "Bug", "color": "red", "boardId": "board1"},
                {"id": "label2", "name": "Feature", "color": "blue", "boardId": "board1"}
            ],
            "cards": [
                {
                    "id": "card1",
                    "name": "Test Card 1",
                    "listId": "list1",
                    "boardId": "board1",
                    "memberIds": ["user1"],
                    "taskLists": [],
                    "comments": [],
                    "attachments": []
                },
                {
                    "id": "card2",
                    "name": "Test Card 2",
                    "listId": "list2",
                    "boardId": "board1",
                    "memberIds": [],
                    "taskLists": [],
                    "comments": [],
                    "attachments": []
                }
            ],
            "cardLabels": [
                {"id": "cardLabel1", "cardId": "card1", "labelId": "label1"},
                {"id": "cardLabel2", "cardId": "card2", "labelId": "label2"}
            ],
            "users": [
                {"id": "user1", "name": "Test User", "username": "testuser"}
            ]
        }
    }
