"""Tests for the cards handler."""
import pytest
from unittest.mock import patch, Mock
import json
import httpx

from planka_mcp.models import (
    ListCardsInput,
    GetCardInput,
    CreateCardInput,
    UpdateCardInput,
    ResponseFormat,
    DetailLevel,
)
from planka_mcp.handlers.cards import (
    planka_list_cards,
    planka_get_card,
    planka_create_card,
    planka_update_card,
)


class TestPlankaListCards:
    """Test planka_list_cards tool."""

    @pytest.mark.asyncio
    async def test_list_cards_success_preview(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test successful card listing in preview mode."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            mock_planka_api_client.get.return_value = sample_board_response
            params = ListCardsInput(
                board_id="board1",
                detail_level=DetailLevel.PREVIEW,
                response_format=ResponseFormat.MARKDOWN,
            )
            result = await planka_list_cards(params)
            assert "# Cards" in result
            assert "Test Card 1" in result
            mock_planka_api_client.get.assert_called_once_with("boards/board1")

    @pytest.mark.asyncio
    async def test_list_cards_json_format(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test card listing in JSON format."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            mock_planka_api_client.get.return_value = sample_board_response
            params = ListCardsInput(
                board_id="board1", response_format=ResponseFormat.JSON
            )
            result = await planka_list_cards(params)
            parsed = json.loads(result)
            assert "cards" in parsed
            assert len(parsed["cards"]) == 2

    @pytest.mark.asyncio
    async def test_list_cards_filter_by_list(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test card listing filtered by list."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            mock_planka_api_client.get.return_value = sample_board_response
            params = ListCardsInput(board_id="board1", list_id="list1")
            result = await planka_list_cards(params)
            assert "Test Card 1" in result
            assert "Test Card 2" not in result

    @pytest.mark.asyncio
    async def test_list_cards_api_error(self, mock_planka_api_client):
        """Test card listing handles API errors."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            mock_response = Mock()
            mock_response.status_code = 404
            error = httpx.HTTPStatusError("Not Found", request=Mock(), response=mock_response)
            mock_planka_api_client.get.side_effect = error
            params = ListCardsInput(board_id="nonexistent")
            result = await planka_list_cards(params)
            assert "Error" in result
            assert "not found" in result

    @pytest.mark.asyncio
    async def test_list_cards_api_client_not_initialized(self):
        """Test card listing when API client is not initialized."""
        # Mock instances.api_client to be None
        with patch("planka_mcp.instances.api_client", None):
            params = ListCardsInput(board_id="board1")
            result = await planka_list_cards(params)
            assert "Error" in result
            assert "API client not initialized" in result

    @pytest.mark.asyncio
    async def test_list_cards_label_filter(self, mock_planka_api_client, sample_board_response):
        """Test card listing with label filtering."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            mock_planka_api_client.get.return_value = sample_board_response
            
            # Test filtering by "Bug" label
            params = ListCardsInput(
                board_id="board1",
                label_filter="Bug",
                response_format=ResponseFormat.MARKDOWN,
            )
            result = await planka_list_cards(params)
            
            # Should only show card1 which has the "Bug" label
            assert "Test Card 1" in result
            assert "Test Card 2" not in result
            assert "Bug" in result
            
            # Test filtering by "Feature" label
            params.label_filter = "Feature"
            result = await planka_list_cards(params)
            
            # Should only show card2 which has the "Feature" label
            assert "Test Card 2" in result
            assert "Test Card 1" not in result
            assert "Feature" in result
            
            # Test filtering by non-existent label
            params.label_filter = "Nonexistent"
            result = await planka_list_cards(params)
            
            # Should show no cards message
            assert "No cards found" in result

    @pytest.mark.asyncio
    async def test_list_cards_pagination(self, mock_planka_api_client, sample_board_response):
        """Test card listing with pagination."""
        # Create a response with more cards than the default limit
        cards = []
        for i in range(60):
            cards.append({"id": f"card{i}", "name": f"Test Card {i}", "listId": "list1"})
        
        paginated_response = sample_board_response.copy()
        paginated_response["included"]["cards"] = cards

        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            mock_planka_api_client.get.return_value = paginated_response
            params = ListCardsInput(board_id="board1", limit=50)
            result = await planka_list_cards(params)

            assert "Pagination" in result
            assert "Showing 50 of 60 cards" in result
            assert "offset=50" in result

    @pytest.mark.asyncio
    async def test_list_cards_pagination_edge_cases(self, mock_planka_api_client, sample_board_response):
        """Test card listing pagination edge cases."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            # Create a response with 5 cards for edge case testing
            few_cards_response = sample_board_response.copy()
            cards = []
            for i in range(1, 6):  # 5 cards total
                cards.append({
                    "id": f"card{i}",
                    "name": f"Test Card {i}",
                    "listId": "list1",
                    "boardId": "board1",
                    "memberIds": [],
                    "taskLists": [],
                    "comments": [],
                    "attachments": []
                })
            few_cards_response["included"]["cards"] = cards
            mock_planka_api_client.get.return_value = few_cards_response
            
            # Test offset beyond available cards (offset 10, but only 5 cards)
            params = ListCardsInput(
                board_id="board1",
                limit=10,
                offset=10,
                response_format=ResponseFormat.MARKDOWN,
            )
            result = await planka_list_cards(params)
            assert "No cards found" in result
            
            # Test limit larger than available cards
            params = ListCardsInput(
                board_id="board1",
                limit=100,
                offset=0,
                response_format=ResponseFormat.MARKDOWN,
            )
            result = await planka_list_cards(params)
            # Should show all 5 cards
            for i in range(1, 6):
                assert f"Test Card {i}" in result
            
            # Test limit=1 (minimum valid limit)
            params = ListCardsInput(
                board_id="board1",
                limit=1,
                offset=0,
                response_format=ResponseFormat.MARKDOWN,
            )
            result = await planka_list_cards(params)
            # Should show only the first card
            assert "Test Card 1" in result
            assert "Test Card 2" not in result

    @pytest.mark.asyncio
    async def test_list_cards_malformed_card_labels(
        self, mock_planka_api_client, sample_board_response
    ):
        """Test card listing with malformed card labels."""
        malformed_response = sample_board_response.copy()
        malformed_response["included"]["cardLabels"] = [
            {"id": "cardLabel1", "cardId": "card1"},  # missing labelId
            {"id": "cardLabel2", "labelId": "label2"},  # missing cardId
        ]

        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            mock_planka_api_client.get.return_value = malformed_response
            params = ListCardsInput(board_id="board1")
            result = await planka_list_cards(params)
            # The code should not crash, and just render no labels
            assert "Labels: None" in result

class TestPlankaGetCard:
    """Test planka_get_card tool."""

    @pytest.mark.asyncio
    async def test_get_card_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data, sample_card_data
    ):
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):

            mock_cache.get_card.return_value = sample_card_data
            mock_cache.get_workspace.return_value = sample_workspace_data

            params = GetCardInput(card_id="card1")
            result = await planka_get_card(params)

            assert "Test Card" in result
            assert "card1" in result

    @pytest.mark.asyncio
    async def test_get_card_fallback_to_workspace_context(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test that get_card falls back to workspace context if card details are missing."""
        card_data_without_includes = {
            "id": "card1",
            "name": "Test Card",
            "listId": "list1",
            "boardId": "board1",
        }

        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):

            mock_cache.get_card.return_value = card_data_without_includes
            mock_cache.get_workspace.return_value = sample_workspace_data

            params = GetCardInput(card_id="card1")
            result = await planka_get_card(params)

            # Check that the card name is in the result
            assert "Test Card" in result
            # Check that the label name from the workspace is in the result
            assert "Bug" in result

    @pytest.mark.asyncio
    async def test_get_card_json_format(
        self, mock_planka_api_client, mock_cache, sample_workspace_data, sample_card_data
    ):
        """Test get_card in JSON format."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):

            mock_cache.get_card.return_value = sample_card_data
            mock_cache.get_workspace.return_value = sample_workspace_data

            params = GetCardInput(card_id="card1", response_format=ResponseFormat.JSON)
            result = await planka_get_card(params)
            parsed = json.loads(result)

            assert parsed["id"] == "card1"
            assert parsed["name"] == "Test Card"

    @pytest.mark.asyncio
    async def test_get_card_not_initialized(self):
        """Test get_card when API client or cache is not initialized."""
        # Test when API client is None
        with patch("planka_mcp.instances.api_client", None):
            params = GetCardInput(card_id="card1")
            result = await planka_get_card(params)
            assert "Error" in result
            assert "API client or Cache not initialized" in result
        
        # Test when cache is None
        with patch("planka_mcp.instances.api_client", Mock()), \
             patch("planka_mcp.instances.cache", None):
            params = GetCardInput(card_id="card1")
            result = await planka_get_card(params)
            assert "Error" in result
            assert "API client or Cache not initialized" in result


class TestPlankaCreateCard:
    """Test planka_create_card tool."""

    @pytest.mark.asyncio
    async def test_create_card_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test successful card creation."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            
            mock_cache.get_workspace.return_value = sample_workspace_data
            created_card = {"item": {"id": "new_card", "name": "New Test Card"}}
            mock_planka_api_client.post.return_value = created_card

            params = CreateCardInput(list_id="list1", name="New Test Card")
            result = await planka_create_card(params)

            assert "Created card" in result
            assert "New Test Card" in result
            mock_planka_api_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_card_invalid_list_id(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test card creation with an invalid list ID."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            
            mock_cache.get_workspace.return_value = sample_workspace_data

            params = CreateCardInput(list_id="invalid_list", name="New Test Card")
            result = await planka_create_card(params)

            assert "Error: List ID 'invalid_list' not found" in result


class TestPlankaUpdateCard:
    """Test planka_update_card tool."""

    @pytest.mark.asyncio
    async def test_update_card_success(
        self, mock_planka_api_client, mock_cache, sample_card_data
    ):
        """Test successful card update."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            updated_card = {"item": {"id": "card1", "name": "Updated Test Card"}}
            mock_planka_api_client.patch.return_value = updated_card
            params = UpdateCardInput(card_id="card1", name="Updated Test Card")
            result = await planka_update_card(params)
            assert "Updated" in result
            assert "Updated Test Card" in result
            mock_planka_api_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_card_description(
        self, mock_planka_api_client, mock_cache, sample_card_data
    ):
        """Test updating card description."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            updated_card = {"item": {"id": "card1", "description": "New Description"}}
            mock_planka_api_client.patch.return_value = updated_card
            params = UpdateCardInput(card_id="card1", description="New Description")
            result = await planka_update_card(params)
            assert "Updated description" in result

    @pytest.mark.asyncio
    async def test_update_card_due_date(
        self, mock_planka_api_client, mock_cache, sample_card_data
    ):
        """Test updating card due date."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            updated_card = {"item": {"id": "card1", "dueDate": "2025-01-01T00:00:00Z"}}
            mock_planka_api_client.patch.return_value = updated_card
            params = UpdateCardInput(card_id="card1", due_date="2025-01-01T00:00:00Z")
            result = await planka_update_card(params)
            assert "Updated due date" in result

    @pytest.mark.asyncio
    async def test_move_card_to_another_list(
        self, mock_planka_api_client, mock_cache, sample_card_data
    ):
        """Test moving card to another list."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            updated_card = {"item": {"id": "card1", "listId": "list2"}}
            mock_planka_api_client.patch.return_value = updated_card
            params = UpdateCardInput(card_id="card1", list_id="list2")
            result = await planka_update_card(params)
            assert "Updated list (moved)" in result

    @pytest.mark.asyncio
    async def test_move_card_to_another_list_without_position(
        self, mock_planka_api_client, mock_cache, sample_card_data
    ):
        """Test moving card to another list without specifying position."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            updated_card = {"item": {"id": "card1", "listId": "list2"}}
            mock_planka_api_client.patch.return_value = updated_card
            params = UpdateCardInput(card_id="card1", list_id="list2")
            result = await planka_update_card(params)
            assert "Updated list (moved)" in result
            # Check that position was added to the patch call
            mock_planka_api_client.patch.assert_called_once_with(
                "cards/card1", {"listId": "list2", "position": 65535}
            )

    @pytest.mark.asyncio
    async def test_update_card_no_fields(
        self, mock_planka_api_client, mock_cache, sample_card_data
    ):
        """Test updating card with no fields."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            updated_card = {"item": {"id": "card1"}}
            mock_planka_api_client.patch.return_value = updated_card
            params = UpdateCardInput(card_id="card1")
            result = await planka_update_card(params)
            assert "Updated card" in result

    @pytest.mark.asyncio
    async def test_update_card_no_fields(
        self, mock_planka_api_client, mock_cache, sample_card_data
    ):
        """Test updating card with no fields."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            updated_card = {"item": {"id": "card1"}}
            mock_planka_api_client.patch.return_value = updated_card
            params = UpdateCardInput(card_id="card1")
            result = await planka_update_card(params)
            assert "Updated card" in result

