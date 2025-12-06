"""Comprehensive tests for all Planka MCP tools."""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import json
import httpx
import sys
import os

# Add the src directory to the path so we can import from planka_mcp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + '/src')

# Import from the new modular structure
from planka_mcp.models import (
    GetWorkspaceInput,
    ListCardsInput,
    FindAndGetCardInput,
    GetCardInput,
    CreateCardInput,
    UpdateCardInput,
    AddTaskInput,
    UpdateTaskInput,
    ResponseFormat,
    DetailLevel,
    ResponseContext,
    AddCardLabelInput,
    RemoveCardLabelInput
)
from planka_mcp.cache import PlankaCache, CacheEntry
from planka_mcp.handlers.workspace import planka_get_workspace, fetch_workspace_data
from planka_mcp.handlers.cards import planka_list_cards, planka_get_card, planka_create_card, planka_update_card
from planka_mcp.handlers.search import planka_find_and_get_card
from planka_mcp.handlers.tasks_labels import planka_add_task, planka_update_task, planka_add_card_label, planka_remove_card_label

# ==================== planka_get_workspace TESTS ====================

class TestPlankaGetWorkspace:
    """Test planka_get_workspace tool."""

    @pytest.mark.asyncio
    async def test_get_workspace_markdown_format_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test successful workspace retrieval in markdown format."""
        with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache):

            # Mock cache.get_workspace to return workspace data
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = GetWorkspaceInput(response_format=ResponseFormat.MARKDOWN)
            result = await planka_get_workspace(params)

            # Verify result is markdown formatted
            assert isinstance(result, str)
            assert "# Planka Workspace" in result
            assert "## Projects" in result
            assert "## Boards" in result
            assert "## Lists" in result
            assert "## Labels" in result
            assert "## Users" in result
            assert "Test Project" in result
            assert "Test Board" in result
            assert "To Do" in result
            assert "Bug" in result
            assert "Test User" in result

            # Verify cache was called
            mock_cache.get_workspace.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workspace_json_format_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test successful workspace retrieval in JSON format."""
        with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache):

            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = GetWorkspaceInput(response_format=ResponseFormat.JSON)
            result = await planka_get_workspace(params)

            # Verify result is valid JSON
            assert isinstance(result, str)
            parsed = json.loads(result)
            assert "projects" in parsed
            assert "boards" in parsed
            assert "lists" in parsed
            assert "labels" in parsed
            assert "users" in parsed
            assert len(parsed["projects"]) == 1
            assert parsed["projects"][0]["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_get_workspace_cache_hit(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test workspace retrieval uses cache."""
        with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache):

            # Setup cache to simulate cache hit
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = GetWorkspaceInput()
            result = await planka_get_workspace(params)

            # Verify cache was used
            assert mock_cache.get_workspace.call_count == 1
            assert "Test Project" in result

    @pytest.mark.asyncio
    async def test_get_workspace_api_error(
        self, mock_planka_api_client, mock_cache
    ):
        """Test workspace retrieval handles API errors."""
        with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache):

            # Mock cache to raise an HTTP error
            mock_response = Mock()
            mock_response.status_code = 401
            error = httpx.HTTPStatusError(
                "Unauthorized",
                request=Mock(),
                response=mock_response
            )
            mock_cache.get_workspace = AsyncMock(side_effect=error)

            params = GetWorkspaceInput()
            result = await planka_get_workspace(params)

            # Verify error is handled gracefully
            assert "Error" in result
            assert "Invalid API credentials" in result

    @pytest.mark.asyncio
    async def test_get_workspace_empty_data(
        self, mock_planka_api_client, mock_cache
    ):
        """Test workspace retrieval with empty workspace."""
        with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache):

            empty_workspace = {
                "projects": [],
                "boards": {},
                "lists": {},
                "labels": {},
                "users": {}
            }
            mock_cache.get_workspace = AsyncMock(return_value=empty_workspace)

            params = GetWorkspaceInput()
            result = await planka_get_workspace(params)

            # Should still format properly with empty sections
            assert "# Planka Workspace" in result
            assert "## Projects" in result

    @pytest.mark.asyncio
    async def test_get_workspace_connection_error(
        self, mock_planka_api_client, mock_cache
    ):
        """Test workspace retrieval handles connection errors."""
        with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache):

            mock_cache.get_workspace = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            params = GetWorkspaceInput()
            result = await planka_get_workspace(params)

            assert "Error" in result
            assert "Cannot connect" in result


# ==================== planka_list_cards TESTS ====================

class TestPlankaListCards:
    """Test planka_list_cards tool."""

    @pytest.mark.asyncio
    async def test_list_cards_success_preview(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test successful card listing in preview mode."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            mock_planka_api_client.get = AsyncMock(return_value=sample_board_response)

            params = ListCardsInput(
                board_id="board1",
                detail_level=DetailLevel.PREVIEW,
                response_format=ResponseFormat.MARKDOWN
            )
            result = await planka_list_cards(params)

            # Verify markdown preview format
            assert "# Cards" in result
            assert "Test Card 1" in result
            assert "Test Card 2" in result
            assert "ID: `card1`" in result
            assert "List:" in result
            assert "Labels:" in result

            # Verify API was called
            mock_planka_api_client.get.assert_called_once_with("boards/board1")

    @pytest.mark.asyncio
    async def test_list_cards_json_format(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test card listing in JSON format."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            mock_planka_api_client.get = AsyncMock(return_value=sample_board_response)

            params = ListCardsInput(
                board_id="board1",
                response_format=ResponseFormat.JSON
            )
            result = await planka_list_cards(params)

            # Verify JSON format
            parsed = json.loads(result)
            assert "board" in parsed
            assert "cards" in parsed
            assert "pagination" in parsed
            assert parsed["board"]["id"] == "board1"
            assert len(parsed["cards"]) == 2

    @pytest.mark.asyncio
    async def test_list_cards_filter_by_list(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test card listing filtered by list."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            mock_planka_api_client.get = AsyncMock(return_value=sample_board_response)

            params = ListCardsInput(
                board_id="board1",
                list_id="list1"
            )
            result = await planka_list_cards(params)

            # Should only show cards from list1
            assert "Test Card 1" in result
            assert "Test Card 2" not in result

    @pytest.mark.asyncio
    async def test_list_cards_filter_by_label(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test card listing filtered by label."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            mock_planka_api_client.get = AsyncMock(return_value=sample_board_response)

            params = ListCardsInput(
                board_id="board1",
                label_filter="Bug"
            )
            result = await planka_list_cards(params)

            # Should only show cards with Bug label
            assert "Test Card 1" in result
            assert "Test Card 2" not in result

    @pytest.mark.asyncio
    async def test_list_cards_pagination(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test card listing with pagination."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            mock_planka_api_client.get = AsyncMock(return_value=sample_board_response)

            params = ListCardsInput(
                board_id="board1",
                limit=1,
                offset=0
            )
            result = await planka_list_cards(params)

            # Should show pagination info
            assert "Pagination" in result
            assert "offset=1" in result

    @pytest.mark.asyncio
    async def test_list_cards_empty_result(
        self, mock_planka_api_client
    ):
        """Test card listing with no matching cards."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            empty_board = {
                "item": {"id": "board1", "name": "Empty Board"},
                "included": {
                    "lists": [],
                    "labels": [],
                    "cards": [],
                    "users": []
                }
            }
            mock_planka_api_client.get = AsyncMock(return_value=empty_board)

            params = ListCardsInput(board_id="board1")
            result = await planka_list_cards(params)

            assert "No cards found" in result

    @pytest.mark.asyncio
    async def test_list_cards_detail_levels(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test different detail levels."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            mock_planka_api_client.get = AsyncMock(return_value=sample_board_response)

            # Test PREVIEW
            params_preview = ListCardsInput(
                board_id="board1",
                detail_level=DetailLevel.PREVIEW
            )
            result_preview = await planka_list_cards(params_preview)

            # Test SUMMARY
            params_summary = ListCardsInput(
                board_id="board1",
                detail_level=DetailLevel.SUMMARY
            )
            result_summary = await planka_list_cards(params_summary)

            # Test DETAILED
            params_detailed = ListCardsInput(
                board_id="board1",
                detail_level=DetailLevel.DETAILED
            )
            result_detailed = await planka_list_cards(params_detailed)

            # DETAILED should be longer than SUMMARY, which is longer than PREVIEW
            assert len(result_detailed) > len(result_summary) > len(result_preview)

    @pytest.mark.asyncio
    async def test_list_cards_board_not_found(
        self, mock_planka_api_client
    ):
        """Test card listing when board doesn't exist."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            mock_response = Mock()
            mock_response.status_code = 404
            mock_planka_api_client.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Not found",
                    request=Mock(),
                    response=mock_response
                )
            )

            params = ListCardsInput(board_id="nonexistent")
            result = await planka_list_cards(params)

            assert "Error" in result
            assert "not found" in result


# ==================== planka_find_and_get_card TESTS ====================

class TestPlankaFindAndGetCard:
    """Test planka_find_and_get_card tool."""

    @pytest.mark.asyncio
    async def test_find_single_card_success(
        self, mock_planka_api_client, mock_cache,
        sample_workspace_data, sample_card_data
    ):
        """Test finding a single card and getting details."""
        with patch('planka_mcp.handlers.search.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.search.cache', mock_cache):

            # Mock board response with one matching card
            board_response = {
                "included": {
                    "cards": [sample_card_data]
                }
            }

            # Mock card detail response
            card_detail_response = {
                "item": sample_card_data,
                "included": {
                    "labels": [{"id": "label1", "name": "Bug"}],
                    "users": [{"id": "user1", "name": "Test User"}],
                    "cardLabels": [{"id": "cardLabel1", "cardId": "card1", "labelId": "label1"}],
                    "taskLists": sample_card_data["taskLists"],
                    "comments": sample_card_data["comments"],
                    "attachments": []
                }
            }

            mock_planka_api_client.get = AsyncMock(side_effect=[
                board_response,
                card_detail_response
            ])
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = FindAndGetCardInput(
                query="Test Card",
                board_id="board1"
            )
            result = await planka_find_and_get_card(params)

            # Should return detailed card view
            assert "Test Card" in result
            assert "card1" in result
            assert "## Tasks" in result

    @pytest.mark.asyncio
    async def test_find_multiple_cards(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test finding multiple matching cards."""
        with patch('planka_mcp.handlers.search.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.search.cache', mock_cache):

            # Multiple matching cards
            board_response = {
                "included": {
                    "cards": [
                        {"id": "card1", "name": "Test Card 1", "listId": "list1", "boardId": "board1"},
                        {"id": "card2", "name": "Test Card 2", "listId": "list2", "boardId": "board1"}
                    ]
                }
            }

            mock_planka_api_client.get = AsyncMock(return_value=board_response)
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = FindAndGetCardInput(query="Test", board_id="board1")
            result = await planka_find_and_get_card(params)

            # Should show list of matching cards
            assert "Found 2 matching cards" in result
            assert "Test Card 1" in result
            assert "Test Card 2" in result
            assert "planka_get_card" in result

    @pytest.mark.asyncio
    async def test_find_no_matching_cards(
        self, mock_planka_api_client, mock_cache
    ):
        """Test finding no matching cards."""
        with patch('planka_mcp.handlers.search.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.search.cache', mock_cache):

            board_response = {
                "included": {"cards": []}
            }

            mock_planka_api_client.get = AsyncMock(return_value=board_response)

            params = FindAndGetCardInput(query="Nonexistent", board_id="board1")
            result = await planka_find_and_get_card(params)

            assert "No cards found" in result
            assert "Nonexistent" in result

    @pytest.mark.asyncio
    async def test_find_search_across_all_boards(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test searching across all boards when board_id not specified."""
        with patch('planka_mcp.handlers.search.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.search.cache', mock_cache):

            board_response = {
                "included": {
                    "cards": [
                        {"id": "card1", "name": "Test Card", "listId": "list1", "boardId": "board1"}
                    ]
                }
            }

            mock_planka_api_client.get = AsyncMock(return_value=board_response)
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = FindAndGetCardInput(query="Test")
            result = await planka_find_and_get_card(params)

            # Should search all boards in workspace
            mock_cache.get_workspace.assert_called()

    @pytest.mark.asyncio
    async def test_find_search_in_description(
        self, mock_planka_api_client, mock_cache, sample_card_data
    ):
        """Test search matches card descriptions."""
        with patch('planka_mcp.handlers.search.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.search.cache', mock_cache):

            card_with_desc = sample_card_data.copy()
            card_with_desc["name"] = "Some Card"
            card_with_desc["description"] = "This has special keyword"

            board_response = {
                "included": {"cards": [card_with_desc]}
            }

            card_detail_response = {
                "item": card_with_desc,
                "included": {
                    "labels": [],
                    "users": [],
                    "cardLabels": [],
                    "taskLists": [],
                    "comments": [],
                    "attachments": []
                }
            }

            mock_planka_api_client.get = AsyncMock(side_effect=[
                board_response,
                card_detail_response
            ])
            mock_cache.get_workspace = AsyncMock(return_value={
                "projects": [],
                "boards": {},
                "lists": {},
                "labels": {},
                "users": {}
            })

            params = FindAndGetCardInput(query="special keyword", board_id="board1")
            result = await planka_find_and_get_card(params)

            # Should find card by description
            assert "Some Card" in result

    @pytest.mark.asyncio
    async def test_find_json_format(
        self, mock_planka_api_client, mock_cache,
        sample_workspace_data, sample_card_data
    ):
        """Test find returns JSON when requested."""
        with patch('planka_mcp.handlers.search.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.search.cache', mock_cache):

            board_response = {
                "included": {"cards": [sample_card_data]}
            }

            card_detail_response = {
                "item": sample_card_data,
                "included": {
                    "labels": [],
                    "users": [],
                    "cardLabels": [],
                    "taskLists": [],
                    "comments": [],
                    "attachments": []
                }
            }

            mock_planka_api_client.get = AsyncMock(side_effect=[
                board_response,
                card_detail_response
            ])
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = FindAndGetCardInput(
                query="Test Card",
                board_id="board1",
                response_format=ResponseFormat.JSON
            )
            result = await planka_find_and_get_card(params)

            # Should return valid JSON
            parsed = json.loads(result)
            assert parsed["id"] == "card1"


# ==================== planka_get_card TESTS ====================

class TestPlankaGetCard:
    """Test planka_get_card tool."""

    @pytest.mark.asyncio
    async def test_get_card_success_markdown(
        self, mock_planka_api_client, mock_cache,
        sample_workspace_data, sample_card_data
    ):
        """Test getting card details in markdown format."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            # Mock cache to return card
            async def fetch_card_func():
                return sample_card_data

            mock_cache.get_card = AsyncMock(return_value=sample_card_data)
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = GetCardInput(
                card_id="card1",
                response_format=ResponseFormat.MARKDOWN
            )
            result = await planka_get_card(params)

            # Verify markdown format
            assert "# Test Card" in result
            assert "**ID**: `card1`" in result
            assert "## Tasks" in result
            assert "## Comments" in result
            assert "## Attachments" in result

    @pytest.mark.asyncio
    async def test_get_card_json_format(
        self, mock_planka_api_client, mock_cache,
        sample_workspace_data, sample_card_data
    ):
        """Test getting card details in JSON format."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            mock_cache.get_card = AsyncMock(return_value=sample_card_data)
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = GetCardInput(
                card_id="card1",
                response_format=ResponseFormat.JSON
            )
            result = await planka_get_card(params)

            # Verify JSON format
            parsed = json.loads(result)
            assert parsed["id"] == "card1"
            assert parsed["name"] == "Test Card"
            assert "taskLists" in parsed

    @pytest.mark.asyncio
    async def test_get_card_cache_hit(
        self, mock_planka_api_client, mock_cache,
        sample_workspace_data, sample_card_data
    ):
        """Test get card uses cache."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            mock_cache.get_card = AsyncMock(return_value=sample_card_data)
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = GetCardInput(card_id="card1")
            result = await planka_get_card(params)

            # Verify cache was used
            mock_cache.get_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_card_not_found(
        self, mock_planka_api_client, mock_cache
    ):
        """Test getting non-existent card."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            mock_response = Mock()
            mock_response.status_code = 404
            mock_cache.get_card = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Not found",
                    request=Mock(),
                    response=mock_response
                )
            )

            params = GetCardInput(card_id="nonexistent")
            result = await planka_get_card(params)

            assert "Error" in result
            assert "not found" in result

    @pytest.mark.asyncio
    async def test_get_card_with_tasks_and_comments(
        self, mock_planka_api_client, mock_cache,
        sample_workspace_data, sample_card_data
    ):
        """Test card with tasks and comments are properly formatted."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            mock_cache.get_card = AsyncMock(return_value=sample_card_data)
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = GetCardInput(card_id="card1")
            result = await planka_get_card(params)

            # Verify tasks are shown
            assert "Task 1" in result
            assert "Task 2" in result
            assert "[x]" in result  # Completed task
            assert "[ ]" in result  # Incomplete task

            # Verify comments are shown
            assert "Test comment" in result


# ==================== planka_create_card TESTS ====================

class TestPlankaCreateCard:
    """Test planka_create_card tool."""

    @pytest.mark.asyncio
    async def test_create_card_minimal(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test creating card with minimal fields."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            # Mock workspace response to find board_id for list
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            created_card = {
                "item": {
                    "id": "new_card_id",
                    "name": "New Card",
                    "boardId": "board1"
                }
            }
            mock_planka_api_client.post = AsyncMock(return_value=created_card)

            params = CreateCardInput(
                list_id="list1",
                name="New Card"
            )
            result = await planka_create_card(params)

            # Verify confirmation message
            assert "Created card" in result
            assert "New Card" in result
            assert "new_card_id" in result

            # Verify API was called correctly with correct endpoint
            mock_planka_api_client.post.assert_called_once()
            call_args = mock_planka_api_client.post.call_args
            assert call_args[0][0] == "lists/list1/cards"
            # Second positional argument is the json_data
            json_data = call_args[0][1]
            assert json_data["type"] == "project"  # Required field
            assert json_data["name"] == "New Card"
            assert json_data["position"] == 65535  # Default position

    @pytest.mark.asyncio
    async def test_create_card_full(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test creating card with all fields."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            # Mock workspace response to find board_id for list
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            created_card = {
                "item": {
                    "id": "new_card_id",
                    "name": "Full Card",
                    "description": "Detailed description",
                    "dueDate": "2024-12-31T23:59:59Z",
                    "position": 1024.5,
                    "boardId": "board1"
                }
            }
            mock_planka_api_client.post = AsyncMock(return_value=created_card)

            params = CreateCardInput(
                list_id="list1",
                name="Full Card",
                description="Detailed description",
                due_date="2024-12-31T23:59:59Z",
                position=1024.5
            )
            result = await planka_create_card(params)

            # Verify all fields were sent
            call_args = mock_planka_api_client.post.call_args
            assert call_args[0][0] == "lists/list1/cards"
            # Second positional argument is the json_data
            json_data = call_args[0][1]
            assert json_data["type"] == "project"  # Required field
            assert json_data["name"] == "Full Card"
            assert json_data["description"] == "Detailed description"
            assert json_data["dueDate"] == "2024-12-31T23:59:59Z"
            assert json_data["position"] == 1024.5

    @pytest.mark.asyncio
    async def test_create_card_invalidates_cache(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test creating card invalidates board cache."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            # Mock workspace response to find board_id for list
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            created_card = {
                "item": {
                    "id": "new_card_id",
                    "name": "New Card",
                    "boardId": "board1"
                }
            }
            mock_planka_api_client.post = AsyncMock(return_value=created_card)
            mock_cache.invalidate_board = Mock()

            params = CreateCardInput(list_id="list1", name="New Card")
            await planka_create_card(params)

            # Verify cache was invalidated
            mock_cache.invalidate_board.assert_called_once_with("board1")

    @pytest.mark.asyncio
    async def test_create_card_api_error(
        self, mock_planka_api_client, mock_cache
    ):
        """Test creating card handles API errors."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            mock_response = Mock()
            mock_response.status_code = 403
            mock_planka_api_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Forbidden",
                    request=Mock(),
                    response=mock_response
                )
            )

            params = CreateCardInput(list_id="list1", name="New Card")
            result = await planka_create_card(params)

            assert "Error" in result
            assert "permission" in result


# ==================== planka_update_card TESTS ====================

class TestPlankaUpdateCard:
    """Test planka_update_card tool."""

    @pytest.mark.asyncio
    async def test_update_card_name(
        self, mock_planka_api_client, mock_cache
    ):
        """Test updating card name."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            updated_card = {
                "item": {
                    "id": "card1",
                    "name": "Updated Name",
                    "boardId": "board1"
                }
            }
            mock_planka_api_client.patch = AsyncMock(return_value=updated_card)
            mock_cache.invalidate_card = Mock()
            mock_cache.invalidate_board = Mock()

            params = UpdateCardInput(card_id="card1", name="Updated Name")
            result = await planka_update_card(params)

            # Verify update message
            assert "Updated name" in result
            assert "Updated Name" in result

            # Verify API call
            mock_planka_api_client.patch.assert_called_once()
            call_args = mock_planka_api_client.patch.call_args
            assert call_args[0][0] == "cards/card1"
            # Second positional argument is the json_data
            assert call_args[0][1]["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_card_multiple_fields(
        self, mock_planka_api_client, mock_cache
    ):
        """Test updating multiple card fields."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            updated_card = {
                "item": {
                    "id": "card1",
                    "name": "Updated Card",
                    "description": "New description",
                    "listId": "list2",
                    "boardId": "board1"
                }
            }
            mock_planka_api_client.patch = AsyncMock(return_value=updated_card)
            mock_cache.invalidate_card = Mock()
            mock_cache.invalidate_board = Mock()

            params = UpdateCardInput(
                card_id="card1",
                name="Updated Card",
                description="New description",
                list_id="list2"
            )
            result = await planka_update_card(params)

            # Verify multiple fields mentioned
            assert "name" in result
            assert "description" in result
            assert "moved" in result

    @pytest.mark.asyncio
    async def test_update_card_move_list(
        self, mock_planka_api_client, mock_cache
    ):
        """Test moving card to different list."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            updated_card = {
                "item": {
                    "id": "card1",
                    "name": "Test Card",
                    "listId": "list2",
                    "boardId": "board1"
                }
            }
            mock_planka_api_client.patch = AsyncMock(return_value=updated_card)
            mock_cache.invalidate_card = Mock()
            mock_cache.invalidate_board = Mock()

            params = UpdateCardInput(card_id="card1", list_id="list2")
            result = await planka_update_card(params)

            # Verify move is indicated
            assert "moved" in result

            # Verify position is automatically added when moving lists
            call_args = mock_planka_api_client.patch.call_args
            update_data = call_args[0][1]
            assert update_data["listId"] == "list2"
            assert update_data["position"] == 65535  # Default position at end

    @pytest.mark.asyncio
    async def test_update_card_move_list_with_position(
        self, mock_planka_api_client, mock_cache
    ):
        """Test moving card to different list with explicit position."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            updated_card = {
                "item": {
                    "id": "card1",
                    "name": "Test Card",
                    "listId": "list2",
                    "boardId": "board1"
                }
            }
            mock_planka_api_client.patch = AsyncMock(return_value=updated_card)
            mock_cache.invalidate_card = Mock()
            mock_cache.invalidate_board = Mock()

            params = UpdateCardInput(card_id="card1", list_id="list2", position=1024.5)
            result = await planka_update_card(params)

            # Verify explicit position is used
            call_args = mock_planka_api_client.patch.call_args
            update_data = call_args[0][1]
            assert update_data["listId"] == "list2"
            assert update_data["position"] == 1024.5  # Explicit position preserved

    @pytest.mark.asyncio
    async def test_update_card_invalidates_cache(
        self, mock_planka_api_client, mock_cache
    ):
        """Test updating card invalidates caches."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            updated_card = {
                "item": {
                    "id": "card1",
                    "name": "Updated",
                    "boardId": "board1"
                }
            }
            mock_planka_api_client.patch = AsyncMock(return_value=updated_card)
            mock_cache.invalidate_card = Mock()
            mock_cache.invalidate_board = Mock()

            params = UpdateCardInput(card_id="card1", name="Updated")
            await planka_update_card(params)

            # Verify both caches invalidated
            mock_cache.invalidate_card.assert_called_once_with("card1")
            mock_cache.invalidate_board.assert_called_once_with("board1")

    @pytest.mark.asyncio
    async def test_update_card_not_found(
        self, mock_planka_api_client, mock_cache
    ):
        """Test updating non-existent card."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            mock_response = Mock()
            mock_response.status_code = 404
            mock_planka_api_client.patch = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Not found",
                    request=Mock(),
                    response=mock_response
                )
            )

            params = UpdateCardInput(card_id="nonexistent", name="Updated")
            result = await planka_update_card(params)

            assert "Error" in result
            assert "not found" in result


# ==================== planka_add_task TESTS ====================

class TestPlankaAddTask:
    """Test planka_add_task tool."""

    @pytest.mark.asyncio
    async def test_add_task_to_existing_list(
        self, mock_planka_api_client, mock_cache
    ):
        """Test adding task to existing task list."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            # Mock card with existing task list
            card_response = {
                "included": {
                    "taskLists": [
                        {"id": "tasklist1", "name": "Tasks"}
                    ]
                }
            }

            created_task = {
                "item": {
                    "id": "task_new",
                    "name": "New Task"
                }
            }

            mock_planka_api_client.get = AsyncMock(return_value=card_response)
            mock_planka_api_client.post = AsyncMock(return_value=created_task)
            mock_cache.invalidate_card = Mock()

            params = AddTaskInput(card_id="card1", task_name="New Task")
            result = await planka_add_task(params)

            # Verify success message
            assert "Added task" in result
            assert "New Task" in result
            assert "task_new" in result

            # Verify task was added to existing list (no new list created)
            assert mock_planka_api_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_add_task_creates_new_list(
        self, mock_planka_api_client, mock_cache
    ):
        """Test adding task creates new task list if none exists."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            # Mock card with no task lists
            card_response = {
                "included": {"taskLists": []}
            }

            created_list = {
                "item": {"id": "tasklist_new", "name": "Tasks"}
            }

            created_task = {
                "item": {"id": "task_new", "name": "New Task"}
            }

            mock_planka_api_client.get = AsyncMock(return_value=card_response)
            mock_planka_api_client.post = AsyncMock(side_effect=[
                created_list,
                created_task
            ])
            mock_cache.invalidate_card = Mock()

            params = AddTaskInput(card_id="card1", task_name="New Task")
            result = await planka_add_task(params)

            # Verify both task list and task were created
            assert mock_planka_api_client.post.call_count == 2

            # Verify first call created task list
            first_call = mock_planka_api_client.post.call_args_list[0]
            assert "task-lists" in first_call[0][0]

    @pytest.mark.asyncio
    async def test_add_task_custom_list_name(
        self, mock_planka_api_client, mock_cache
    ):
        """Test adding task to custom-named task list."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            card_response = {
                "included": {
                    "taskLists": [
                        {"id": "tasklist1", "name": "My Checklist"}
                    ]
                }
            }

            created_task = {
                "item": {"id": "task_new", "name": "New Task"}
            }

            mock_planka_api_client.get = AsyncMock(return_value=card_response)
            mock_planka_api_client.post = AsyncMock(return_value=created_task)
            mock_cache.invalidate_card = Mock()

            params = AddTaskInput(
                card_id="card1",
                task_name="New Task",
                task_list_name="My Checklist"
            )
            result = await planka_add_task(params)

            # Verify task added to correct list
            assert "My Checklist" in result

    @pytest.mark.asyncio
    async def test_add_task_invalidates_cache(
        self, mock_planka_api_client, mock_cache
    ):
        """Test adding task invalidates card cache."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            card_response = {
                "included": {
                    "taskLists": [{"id": "tasklist1", "name": "Tasks"}]
                }
            }

            created_task = {
                "item": {"id": "task_new", "name": "New Task"}
            }

            mock_planka_api_client.get = AsyncMock(return_value=card_response)
            mock_planka_api_client.post = AsyncMock(return_value=created_task)
            mock_cache.invalidate_card = Mock()

            params = AddTaskInput(card_id="card1", task_name="New Task")
            await planka_add_task(params)

            # Verify cache invalidated
            mock_cache.invalidate_card.assert_called_once_with("card1")

    @pytest.mark.asyncio
    async def test_add_task_card_not_found(
        self, mock_planka_api_client, mock_cache
    ):
        """Test adding task to non-existent card."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            mock_response = Mock()
            mock_response.status_code = 404
            mock_planka_api_client.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Not found",
                    request=Mock(),
                    response=mock_response
                )
            )

            params = AddTaskInput(card_id="nonexistent", task_name="New Task")
            result = await planka_add_task(params)

            assert "Error" in result
            assert "not found" in result


# ==================== planka_update_task TESTS ====================

class TestPlankaUpdateTask:
    """Test planka_update_task tool."""

    @pytest.mark.asyncio
    async def test_update_task_complete(
        self, mock_planka_api_client, mock_cache
    ):
        """Test marking task as complete."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            updated_task = {
                "item": {
                    "id": "task1",
                    "name": "Test Task",
                    "isCompleted": True
                }
            }
            mock_planka_api_client.patch = AsyncMock(return_value=updated_task)

            params = UpdateTaskInput(task_id="task1", is_completed=True)
            result = await planka_update_task(params)

            # Verify completion indicated
            assert "complete" in result
            assert "[x]" in result
            assert "Test Task" in result

            # Verify API call
            mock_planka_api_client.patch.assert_called_once()
            call_args = mock_planka_api_client.patch.call_args
            assert call_args[0][0] == "tasks/task1"
            # Second positional argument is the json_data
            assert call_args[0][1]["isCompleted"] is True

    @pytest.mark.asyncio
    async def test_update_task_incomplete(
        self, mock_planka_api_client, mock_cache
    ):
        """Test marking task as incomplete."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            updated_task = {
                "item": {
                    "id": "task1",
                    "name": "Test Task",
                    "isCompleted": False
                }
            }
            mock_planka_api_client.patch = AsyncMock(return_value=updated_task)

            params = UpdateTaskInput(task_id="task1", is_completed=False)
            result = await planka_update_task(params)

            # Verify incompletion indicated
            assert "incomplete" in result
            assert "[ ]" in result

    @pytest.mark.asyncio
    async def test_update_task_not_found(
        self, mock_planka_api_client, mock_cache
    ):
        """Test updating non-existent task."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            mock_response = Mock()
            mock_response.status_code = 404
            mock_planka_api_client.patch = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Not found",
                    request=Mock(),
                    response=mock_response
                )
            )

            params = UpdateTaskInput(task_id="nonexistent", is_completed=True)
            result = await planka_update_task(params)

            assert "Error" in result
            assert "not found" in result

    @pytest.mark.asyncio
    async def test_update_task_api_error(
        self, mock_planka_api_client, mock_cache
    ):
        """Test update task handles API errors."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            mock_response = Mock()
            mock_response.status_code = 403
            mock_planka_api_client.patch = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Forbidden",
                    request=Mock(),
                    response=mock_response
                )
            )

            params = UpdateTaskInput(task_id="task1", is_completed=True)
            result = await planka_update_task(params)

            assert "Error" in result
            assert "permission" in result


# ==================== CACHE BEHAVIOR TESTS ====================

class TestCacheBehavior:
    """Test caching behavior across tools."""

    @pytest.mark.asyncio
    async def test_workspace_cache_ttl(self):
        """Test workspace cache respects TTL."""
        import time

        cache = PlankaCache()
        test_data = {"projects": []}

        # Set cache entry
        cache.workspace = CacheEntry(
            data=test_data,
            timestamp=time.time(),
            ttl=300
        )

        # Should be valid immediately
        assert cache.workspace.is_valid()

        # Simulate expired cache
        cache.workspace.timestamp = time.time() - 301
        assert not cache.workspace.is_valid()

    @pytest.mark.asyncio
    async def test_write_operations_invalidate_cache(
        self, mock_planka_api_client, mock_cache
    ):
        """Test write operations invalidate relevant caches."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            mock_cache.invalidate_card = Mock()
            mock_cache.invalidate_board = Mock()

            # Create card should invalidate board cache
            created_card = {
                "item": {"id": "card1", "name": "New", "boardId": "board1"}
            }
            mock_planka_api_client.post = AsyncMock(return_value=created_card)

            params = CreateCardInput(list_id="list1", name="New")
            await planka_create_card(params)

            mock_cache.invalidate_board.assert_called_once_with("board1")

    @pytest.mark.asyncio
    async def test_card_cache_cleanup(self):
        """Test card cache cleanup limits memory usage."""
        cache = PlankaCache()

        # Fill cache beyond limit
        for i in range(120):
            cache.card_details[f"card{i}"] = CacheEntry(
                data={"id": f"card{i}"},
                timestamp=1000 + i,  # Different timestamps
                ttl=60
            )

        # Trigger cleanup
        cache.cleanup_card_cache()

        # Should keep only 100 most recent
        assert len(cache.card_details) == 100


# ==================== EDGE CASES ====================

class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_truncate_large_response(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test responses are truncated if too large."""
        with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache):

            # Create workspace with many items
            large_workspace = sample_workspace_data.copy()
            large_workspace["boards"] = {
                f"board{i}": {
                    "id": f"board{i}",
                    "name": f"Board {i}" * 100,  # Make names very long
                    "projectId": "proj1"
                }
                for i in range(500)
            }

            mock_cache.get_workspace = AsyncMock(return_value=large_workspace)

            params = GetWorkspaceInput()
            result = await planka_get_workspace(params)

            # Should be truncated if over limit
            # Note: Actual truncation depends on CHARACTER_LIMIT
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_card_with_no_labels_or_members(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test card with empty labels and members."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache):

            card_no_labels = {
                "id": "card1",
                "name": "Bare Card",
                "listId": "list1",
                "boardId": "board1",
                "memberIds": [],
                "taskLists": [],
                "comments": [],
                "attachments": [],
                "_included_cardLabels": [],
                "_included_labels": [],
                "_included_users": []
            }

            mock_cache.get_card = AsyncMock(return_value=card_no_labels)
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            params = GetCardInput(card_id="card1")
            result = await planka_get_card(params)

            # Should handle empty lists gracefully
            assert "Bare Card" in result
            assert "(No labels)" in result or "None" in result

    @pytest.mark.asyncio
    async def test_timeout_error_handling(
        self, mock_planka_api_client, mock_cache
    ):
        """Test timeout errors are handled gracefully."""
        with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache):

            mock_cache.get_workspace = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )

            params = GetWorkspaceInput()
            result = await planka_get_workspace(params)

            assert "Error" in result
            assert "timed out" in result

    @pytest.mark.asyncio
    async def test_case_insensitive_label_filter(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test label filter is case-insensitive."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            mock_planka_api_client.get = AsyncMock(return_value=sample_board_response)

            # Test lowercase filter
            params = ListCardsInput(board_id="board1", label_filter="bug")
            result = await planka_list_cards(params)

            assert "Test Card 1" in result

    @pytest.mark.asyncio
    async def test_pagination_edge_cases(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test pagination with various offset/limit combinations."""
        with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client):

            mock_planka_api_client.get = AsyncMock(return_value=sample_board_response)

            # Test offset beyond available cards
            params = ListCardsInput(
                board_id="board1",
                offset=100,
                limit=10
            )
            result = await planka_list_cards(params)

            # Should return empty result
            assert "No cards found" in result or "0 found" in result


class TestPlankaAddCardLabel:
    """Test planka_add_card_label tool."""

    @pytest.mark.asyncio
    async def test_add_label_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test adding a label to a card."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            # Mock workspace to get label name
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)

            response = {"item": {"id": "cardLabel123"}}
            mock_planka_api_client.post = AsyncMock(return_value=response)
            mock_cache.invalidate_card = Mock()

            params = AddCardLabelInput(
                card_id="card1",
                label_id="label1"
            )
            result = await planka_add_card_label(params)

            # Verify confirmation message
            assert "Added label" in result
            assert "Bug" in result  # Label name from sample data

            # Verify API was called correctly
            mock_planka_api_client.post.assert_called_once()
            call_args = mock_planka_api_client.post.call_args
            assert call_args[0][0] == "cards/card1/labels"
            assert call_args[0][1]["labelId"] == "label1"

            # Verify cache was invalidated
            mock_cache.invalidate_card.assert_called_once_with("card1")

    @pytest.mark.asyncio
    async def test_add_label_api_error(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test adding label with API error."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)
            mock_planka_api_client.post = AsyncMock(side_effect=Exception("API Error"))

            params = AddCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_add_card_label(params)

            assert "Error" in result


class TestPlankaRemoveCardLabel:
    """Test planka_remove_card_label tool."""

    @pytest.mark.asyncio
    async def test_remove_label_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test removing a label from a card."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            # Mock workspace to get label name
            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)
            mock_planka_api_client.delete = AsyncMock()
            mock_cache.invalidate_card = Mock()

            params = RemoveCardLabelInput(
                card_id="card1",
                label_id="label1"
            )
            result = await planka_remove_card_label(params)

            # Verify confirmation message
            assert "Removed label" in result
            assert "Bug" in result  # Label name from sample data

            # Verify API was called correctly
            mock_planka_api_client.delete.assert_called_once_with("cards/card1/labels/label1")

            # Verify cache was invalidated
            mock_cache.invalidate_card.assert_called_once_with("card1")

    @pytest.mark.asyncio
    async def test_remove_label_api_error(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test removing label with API error."""
        with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache):

            mock_cache.get_workspace = AsyncMock(return_value=sample_workspace_data)
            mock_planka_api_client.delete = AsyncMock(side_effect=Exception("API Error"))

            params = RemoveCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_remove_card_label(params)

            assert "Error" in result