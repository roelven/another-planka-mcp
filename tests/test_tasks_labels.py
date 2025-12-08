"""Tests for the tasks and labels handler."""
import pytest
from unittest.mock import patch

from src.planka_mcp.models import (
    AddTaskInput,
    UpdateTaskInput,
    AddCardLabelInput,
    RemoveCardLabelInput,
)
from src.planka_mcp.handlers.tasks_labels import (
    planka_add_task,
    planka_update_task,
    planka_add_card_label,
    planka_remove_card_label,
)


class TestPlankaAddTask:
    """Test planka_add_task tool."""

    @pytest.mark.asyncio
    async def test_add_task_success(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_card_data
    ):
        """Test successful task creation."""
        with patch("src.planka_mcp.handlers.tasks_labels.api_client", mock_planka_api_client), \
             patch("src.planka_mcp.handlers.tasks_labels.cache", mock_cache):
            card_response = {"included": {"taskLists": [{"id": "tasklist1", "name": "Tasks"}]}}
            created_task = {"item": {"id": "new_task", "name": "New Test Task"}}
            mock_planka_api_client.get.return_value = card_response
            mock_planka_api_client.post.return_value = created_task

            params = AddTaskInput(card_id="card1", task_name="New Test Task")
            result = await planka_add_task(params)

            assert "Added task" in result
            assert "New Test Task" in result
            mock_planka_api_client.post.assert_called_once()


class TestPlankaUpdateTask:
    """Test planka_update_task tool."""

    @pytest.mark.asyncio
    async def test_update_task_success(
        self,
        mock_planka_api_client,
        mock_cache
    ):
        """Test successful task update."""
        with patch("src.planka_mcp.handlers.tasks_labels.api_client", mock_planka_api_client), \
             patch("src.planka_mcp.handlers.tasks_labels.cache", mock_cache):
            updated_task = {"item": {"id": "task1", "name": "Test Task", "isCompleted": True}}
            mock_planka_api_client.patch.return_value = updated_task
            params = UpdateTaskInput(task_id="task1", is_completed=True)
            result = await planka_update_task(params)
            assert "Marked task as complete" in result
            mock_planka_api_client.patch.assert_called_once()


class TestPlankaAddCardLabel:
    """Test planka_add_card_label tool."""

    @pytest.mark.asyncio
    async def test_add_card_label_success(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_workspace_data
    ):
        """Test successful card label addition."""
        with patch("src.planka_mcp.handlers.tasks_labels.api_client", mock_planka_api_client), \
             patch("src.planka_mcp.handlers.tasks_labels.cache", mock_cache):
            mock_cache.get_workspace.return_value = sample_workspace_data
            mock_planka_api_client.post.return_value = {"item": {"id": "cardLabel1"}}
            params = AddCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_add_card_label(params)
            assert "Added label" in result
            mock_planka_api_client.post.assert_called_once()


class TestPlankaRemoveCardLabel:
    """Test planka_remove_card_label tool."""

    @pytest.mark.asyncio
    async def test_remove_card_label_success(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_workspace_data
    ):
        """Test successful card label removal."""
        with patch("src.planka_mcp.handlers.tasks_labels.api_client", mock_planka_api_client), \
             patch("src.planka_mcp.handlers.tasks_labels.cache", mock_cache):
            mock_cache.get_workspace.return_value = sample_workspace_data
            mock_planka_api_client.delete.return_value = None
            params = RemoveCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_remove_card_label(params)
            assert "Removed label" in result
            mock_planka_api_client.delete.assert_called_once()
