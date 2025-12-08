"""Tests for the workspace handler."""
import pytest
from unittest.mock import Mock, patch
import json
import httpx

from src.planka_mcp.models import GetWorkspaceInput, ResponseFormat
from src.planka_mcp.handlers.workspace import planka_get_workspace


class TestPlankaGetWorkspace:
    """Test planka_get_workspace tool."""

    @pytest.mark.asyncio
    async def test_get_workspace_markdown_format_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test successful workspace retrieval in markdown format."""
        with patch('src.planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('src.planka_mcp.handlers.workspace.cache', mock_cache):
            mock_cache.get_workspace.return_value = sample_workspace_data
            params = GetWorkspaceInput(response_format=ResponseFormat.MARKDOWN)
            result = await planka_get_workspace(params)
            assert isinstance(result, str)
            assert "# Planka Workspace" in result
            assert "Test Project" in result
            mock_cache.get_workspace.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workspace_json_format_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test successful workspace retrieval in JSON format."""
        with patch('src.planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('src.planka_mcp.handlers.workspace.cache', mock_cache):
            mock_cache.get_workspace.return_value = sample_workspace_data
            params = GetWorkspaceInput(response_format=ResponseFormat.JSON)
            result = await planka_get_workspace(params)
            parsed = json.loads(result)
            assert "projects" in parsed
            assert parsed["projects"][0]["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_get_workspace_api_error(
        self, mock_planka_api_client, mock_cache
    ):
        """Test workspace retrieval handles API errors."""
        with patch('src.planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('src.planka_mcp.handlers.workspace.cache', mock_cache):
            mock_response = Mock()
            mock_response.status_code = 401
            error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)
            mock_cache.get_workspace.side_effect = error
            params = GetWorkspaceInput()
            result = await planka_get_workspace(params)
            assert "Error" in result
            assert "Invalid API credentials" in result
