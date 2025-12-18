"""Tests for the tasks and labels handler."""
import pytest
from unittest.mock import patch, Mock, call

from planka_mcp.models import (
    AddTaskInput,
    UpdateTaskInput,
    AddCardLabelInput,
    RemoveCardLabelInput,
    DeleteTaskInput,
)
from planka_mcp.handlers.tasks_labels import (
    planka_add_task,
    planka_update_task,
    planka_add_card_label,
    planka_remove_card_label,
    planka_delete_task,
)


class TestPlankaAddTask:
    """Test planka_add_task tool."""

    @pytest.mark.asyncio
    async def test_add_task_with_correct_endpoint(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_card_data
    ):
        """Test successful task creation using correct API endpoint."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            # Mock the API to return success for the correct endpoint
            created_task = {"item": {"id": "new_task", "name": "New Test Task"}}
            mock_planka_api_client.post.return_value = created_task
            
            # Mock the get method to return a card without task lists
            # This simulates the scenario where we want to create a task directly on the card
            card_response = {"included": {"taskLists": []}}
            mock_planka_api_client.get.return_value = card_response

            params = AddTaskInput(card_id="card1", task_name="New Test Task")
            result = await planka_add_task(params)

            assert "Added task" in result
            assert "New Test Task" in result
            # Verify the correct endpoint is used: POST /api/cards/{cardId}/tasks
            mock_planka_api_client.post.assert_called_once_with(
                "cards/card1/tasks",
                {"name": "New Test Task", "position": 65535}
            )

    @pytest.mark.asyncio
    async def test_add_task_simple_case(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_card_data
    ):
        """Test successful task creation using the simplified direct endpoint."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            # Mock the API to return success for the correct endpoint
            created_task = {"item": {"id": "new_task", "name": "New Test Task"}}
            mock_planka_api_client.post.return_value = created_task

            params = AddTaskInput(card_id="card1", task_name="New Test Task")
            result = await planka_add_task(params)

            assert "Added task" in result
            assert "New Test Task" in result
            # Verify the correct endpoint is used: POST /api/cards/{cardId}/tasks
            mock_planka_api_client.post.assert_called_once_with(
                "cards/card1/tasks",
                {"name": "New Test Task", "position": 65535}
            )

    @pytest.mark.asyncio
    async def test_add_task_not_initialized(self):
        """Test add_task when API client or cache is not initialized."""
        # Test when API client is None
        with patch("planka_mcp.instances.api_client", None):
            params = AddTaskInput(card_id="card1", task_name="Test Task")
            result = await planka_add_task(params)
            assert "Error" in result
            assert "API client or Cache not initialized" in result
        
        # Test when cache is None
        with patch("planka_mcp.instances.api_client", Mock()), \
             patch("planka_mcp.instances.cache", None):
            params = AddTaskInput(card_id="card1", task_name="Test Task")
            result = await planka_add_task(params)
            assert "Error" in result
            assert "API client or Cache not initialized" in result


class TestPlankaUpdateTask:
    """Test planka_update_task tool."""

    @pytest.mark.asyncio
    async def test_update_task_success(
        self,
        mock_planka_api_client,
        mock_cache
    ):
        """Test successful task update."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            updated_task = {"item": {"id": "task1", "name": "Test Task", "isCompleted": True}}
            mock_planka_api_client.patch.return_value = updated_task
            params = UpdateTaskInput(task_id="task1", is_completed=True)
            result = await planka_update_task(params)
            assert "Marked task as complete" in result
            mock_planka_api_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_not_initialized(self):
        """Test update_task when API client is not initialized."""
        # Test when API client is None
        with patch("planka_mcp.instances.api_client", None):
            params = UpdateTaskInput(task_id="task1", is_completed=True)
            result = await planka_update_task(params)
            assert "Error" in result
            assert "API client not initialized" in result


class TestPlankaDeleteTask:
    """Test planka_delete_task tool."""

    @pytest.mark.asyncio
    async def test_delete_task_success(
        self,
        mock_planka_api_client,
        mock_cache
    ):
        """Test successful task deletion."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            # Mock the API calls
            task_detail = {"item": {"id": "task1", "name": "Test Task"}}
            mock_planka_api_client.get.return_value = task_detail
            mock_planka_api_client.delete.return_value = None
            
            params = DeleteTaskInput(task_id="task1")
            result = await planka_delete_task(params)
            
            assert "Deleted task" in result
            assert "Test Task" in result
            assert "task1" in result
            # Verify the correct endpoints were called
            mock_planka_api_client.get.assert_called_once_with("tasks/task1")
            mock_planka_api_client.delete.assert_called_once_with("tasks/task1")

    @pytest.mark.asyncio
    async def test_delete_task_not_initialized(self):
        """Test delete_task when API client is not initialized."""
        # Test when API client is None
        with patch("planka_mcp.instances.api_client", None):
            params = DeleteTaskInput(task_id="task1")
            result = await planka_delete_task(params)
            assert "Error" in result
            assert "API client not initialized" in result


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
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            mock_cache.get_workspace.return_value = sample_workspace_data
            mock_planka_api_client.post.return_value = {"item": {"id": "cardLabel1"}}
            params = AddCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_add_card_label(params)
            assert "Added label" in result
            mock_planka_api_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_card_label_not_initialized(self):
        """Test add_card_label when API client or cache is not initialized."""
        # Test when API client is None
        with patch("planka_mcp.instances.api_client", None):
            params = AddCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_add_card_label(params)
            assert "Error" in result
            assert "API client or Cache not initialized" in result
        
        # Test when cache is None
        with patch("planka_mcp.instances.api_client", Mock()), \
             patch("planka_mcp.instances.cache", None):
            params = AddCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_add_card_label(params)
            assert "Error" in result
            assert "API client or Cache not initialized" in result


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
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            mock_cache.get_workspace.return_value = sample_workspace_data
            mock_planka_api_client.delete.return_value = None
            params = RemoveCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_remove_card_label(params)
            assert "Removed label" in result
            mock_planka_api_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_card_label_not_initialized(self):
        """Test remove_card_label when API client or cache is not initialized."""
        # Test when API client is None
        with patch("planka_mcp.instances.api_client", None):
            params = RemoveCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_remove_card_label(params)
            assert "Error" in result
            assert "API client or Cache not initialized" in result
        
        # Test when cache is None
        with patch("planka_mcp.instances.api_client", Mock()), \
             patch("planka_mcp.instances.cache", None):
            params = RemoveCardLabelInput(card_id="card1", label_id="label1")
            result = await planka_remove_card_label(params)
            assert "Error" in result
            assert "API client or Cache not initialized" in result
