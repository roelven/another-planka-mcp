"""Tests for the cards handler."""
import pytest
from unittest.mock import patch, Mock
import json
import httpx

from src.planka_mcp.models import (
    ListCardsInput,
    GetCardInput,
    CreateCardInput,
    UpdateCardInput,
    ResponseFormat,
    DetailLevel,
)
from src.planka_mcp.handlers.cards import (
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
        with patch("src.planka_mcp.handlers.cards.api_client", mock_planka_api_client):
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
        with patch("src.planka_mcp.handlers.cards.api_client", mock_planka_api_client):
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
        with patch("src.planka_mcp.handlers.cards.api_client", mock_planka_api_client):
            mock_planka_api_client.get.return_value = sample_board_response
            params = ListCardsInput(board_id="board1", list_id="list1")
            result = await planka_list_cards(params)
            assert "Test Card 1" in result
            assert "Test Card 2" not in result

    @pytest.mark.asyncio
    async def test_list_cards_api_error(self, mock_planka_api_client):
        """Test card listing handles API errors."""
        with patch("src.planka_mcp.handlers.cards.api_client", mock_planka_api_client):
            mock_response = Mock()
            mock_response.status_code = 404
            error = httpx.HTTPStatusError("Not Found", request=Mock(), response=mock_response)
            mock_planka_api_client.get.side_effect = error
            params = ListCardsInput(board_id="nonexistent")
            result = await planka_list_cards(params)
            assert "Error" in result
            assert "not found" in result


class TestPlankaGetCard:
    """Test planka_get_card tool."""

    @pytest.mark.asyncio
    async def test_get_card_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data, sample_card_data
    ):
        with patch("src.planka_mcp.handlers.cards.api_client", mock_planka_api_client), \
             patch("src.planka_mcp.handlers.cards.cache", mock_cache):

            mock_cache.get_card.return_value = sample_card_data
            mock_cache.get_workspace.return_value = sample_workspace_data

            params = GetCardInput(card_id="card1")
            result = await planka_get_card(params)

            assert "Test Card" in result
            assert "card1" in result


class TestPlankaCreateCard:
    """Test planka_create_card tool."""

    @pytest.mark.asyncio
    async def test_create_card_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test successful card creation."""
        with patch("src.planka_mcp.handlers.cards.api_client", mock_planka_api_client), \
             patch("src.planka_mcp.handlers.cards.cache", mock_cache):
            
            mock_cache.get_workspace.return_value = sample_workspace_data
            created_card = {"item": {"id": "new_card", "name": "New Test Card"}}
            mock_planka_api_client.post.return_value = created_card

            params = CreateCardInput(list_id="list1", name="New Test Card")
            result = await planka_create_card(params)

            assert "Created card" in result
            assert "New Test Card" in result
            mock_planka_api_client.post.assert_called_once()


class TestPlankaUpdateCard:
    """Test planka_update_card tool."""

    @pytest.mark.asyncio
    async def test_update_card_success(
        self, mock_planka_api_client, mock_cache, sample_card_data
    ):
        """Test successful card update."""
        with patch("src.planka_mcp.handlers.cards.api_client", mock_planka_api_client), \
             patch("src.planka_mcp.handlers.cards.cache", mock_cache):
            updated_card = {"item": {"id": "card1", "name": "Updated Test Card"}}
            mock_planka_api_client.patch.return_value = updated_card
            params = UpdateCardInput(card_id="card1", name="Updated Test Card")
            result = await planka_update_card(params)
            assert "Updated" in result
            assert "Updated Test Card" in result
            mock_planka_api_client.patch.assert_called_once()

