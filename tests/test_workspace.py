"""Tests for the workspace handler."""
import pytest
from unittest.mock import Mock, patch
import json
import httpx

from planka_mcp.models import GetWorkspaceInput, ResponseFormat
from planka_mcp.handlers.workspace import planka_get_workspace, fetch_workspace_data


class TestPlankaGetWorkspace:
    """Test planka_get_workspace tool."""

    @pytest.mark.asyncio
    async def test_get_workspace_markdown_format_success(
        self, mock_planka_api_client, mock_cache, sample_workspace_data
    ):
        """Test successful workspace retrieval in markdown format."""
        with patch('planka_mcp.instances.api_client', mock_planka_api_client), \
             patch('planka_mcp.instances.cache', mock_cache):
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
        with patch('planka_mcp.instances.api_client', mock_planka_api_client), \
             patch('planka_mcp.instances.cache', mock_cache):
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
        with patch('planka_mcp.instances.api_client', mock_planka_api_client), \
             patch('planka_mcp.instances.cache', mock_cache):
            mock_response = Mock()
            mock_response.status_code = 401
            error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)
            mock_cache.get_workspace.side_effect = error
            params = GetWorkspaceInput()
            result = await planka_get_workspace(params)
            assert "Error" in result
            assert "Invalid API credentials" in result

    @pytest.mark.asyncio
    async def test_get_workspace_cache_not_initialized(self):
        """Test get_workspace when cache is not initialized."""
        # Test when cache is None
        with patch("planka_mcp.instances.cache", None):
            params = GetWorkspaceInput()
            with pytest.raises(RuntimeError) as exc_info:
                await planka_get_workspace(params)
            assert "Cache not initialized" in str(exc_info.value)

class TestFetchWorkspaceData:
    """Test the fetch_workspace_data helper function."""

    @pytest.mark.asyncio
    async def test_fetch_workspace_data_success(self, mock_planka_api_client):
        """Test successful fetch of workspace data."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            # Mock the API responses
            mock_planka_api_client.get.side_effect = [
                {"items": [{"id": "proj1", "name": "Test Project"}]},  # projects
                {"items": [{"id": "user1", "name": "Test User"}]},  # users
                {"included": {"boards": [{"id": "board1", "name": "Test Board"}]}},  # project details
                {
                    "item": {"id": "board1", "name": "Test Board", "projectId": "proj1"},
                    "included": {
                        "lists": [{"id": "list1", "name": "To Do"}],
                        "labels": [{"id": "label1", "name": "Bug", "color": "red"}],
                    },
                },  # board details
            ]

            data = await fetch_workspace_data()

            assert "projects" in data
            assert len(data["projects"]) == 1
            assert data["projects"][0]["name"] == "Test Project"

            assert "users" in data
            assert "user1" in data["users"]
            assert data["users"]["user1"]["name"] == "Test User"

            assert "boards" in data
            assert "board1" in data["boards"]
            assert data["boards"]["board1"]["name"] == "Test Board"

            assert "lists" in data
            assert "list1" in data["lists"]
            assert data["lists"]["list1"]["name"] == "To Do"

            assert "labels" in data
            assert "label1" in data["labels"]
            assert data["labels"]["label1"]["name"] == "Bug"

    @pytest.mark.asyncio
    async def test_fetch_workspace_data_api_error(self, mock_planka_api_client):
        """Test that API errors are propagated."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client):
            mock_planka_api_client.get.side_effect = httpx.HTTPStatusError(
                "API Error", request=Mock(), response=Mock(status_code=500)
            )

            with pytest.raises(httpx.HTTPStatusError):
                await fetch_workspace_data()

    @pytest.mark.asyncio
    async def test_fetch_workspace_data_not_initialized(self):
        """Test fetch_workspace_data when API client is not initialized."""
        # Test when API client is None
        with patch("planka_mcp.instances.api_client", None):
            with pytest.raises(RuntimeError) as exc_info:
                await fetch_workspace_data()
            assert "API client not initialized" in str(exc_info.value)
