"""Tests for the search handler."""
import pytest
from unittest.mock import patch

from planka_mcp.models import FindAndGetCardInput
from planka_mcp.handlers.search import planka_find_and_get_card


class TestPlankaFindAndGetCard:
    """Test planka_find_and_get_card tool."""

    @pytest.mark.asyncio
    async def test_find_single_card_success(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_workspace_data,
        sample_card_data,
    ):
        """Test finding a single card and getting details."""
        with patch("planka_mcp.handlers.search.api_client", mock_planka_api_client), \
             patch("planka_mcp.handlers.search.cache", mock_cache):

            mock_cache.get_workspace.return_value = sample_workspace_data
            board_response = {"included": {"cards": [sample_card_data]}}
            card_detail_response = {"item": sample_card_data, "included": {}}
            mock_planka_api_client.get.side_effect = [board_response, card_detail_response]

            params = FindAndGetCardInput(query="Test Card", board_id="board1")
            result = await planka_find_and_get_card(params)
            assert "Test Card" in result
            assert "card1" in result

    @pytest.mark.asyncio
    async def test_find_multiple_cards(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_workspace_data,
    ):
        """Test finding multiple matching cards."""
        with patch("planka_mcp.handlers.search.api_client", mock_planka_api_client), \
             patch("planka_mcp.handlers.search.cache", mock_cache):
            mock_cache.get_workspace.return_value = sample_workspace_data
            board_response = {"included": {"cards": [{"id": "card1", "name": "Test Card 1"}, {"id": "card2", "name": "Test Card 2"}]}}
            mock_planka_api_client.get.return_value = board_response
            params = FindAndGetCardInput(query="Test", board_id="board1")
            result = await planka_find_and_get_card(params)
            assert "Found 2 matching cards" in result

    @pytest.mark.asyncio
    async def test_find_no_matching_cards(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_workspace_data,
    ):
        """Test finding no matching cards."""
        with patch("planka_mcp.handlers.search.api_client", mock_planka_api_client), \
             patch("planka_mcp.handlers.search.cache", mock_cache):
            mock_cache.get_workspace.return_value = sample_workspace_data
            board_response = {"included": {"cards": []}}
            mock_planka_api_client.get.return_value = board_response
            params = FindAndGetCardInput(query="Nonexistent", board_id="board1")
            result = await planka_find_and_get_card(params)
            assert "No cards found" in result
