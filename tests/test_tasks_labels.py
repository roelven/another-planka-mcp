"""Tests for the tasks and labels handler."""
import pytest
from unittest.mock import patch, Mock, call

from planka_mcp.models import (
    AddTaskInput,
    UpdateTaskInput,
    AddCardLabelInput,
    RemoveCardLabelInput,
)
from planka_mcp.handlers.tasks_labels import (
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
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            card_response = {"included": {"taskLists": [{"id": "tasklist1", "name": "Tasks"}]}}
            created_task = {"item": {"id": "new_task", "name": "New Test Task"}}
            mock_planka_api_client.get.return_value = card_response
            mock_planka_api_client.post.return_value = created_task

            params = AddTaskInput(card_id="card1", task_name="New Test Task")
            result = await planka_add_task(params)

            assert "Added task" in result
            assert "New Test Task" in result
            # Verify the correct endpoint and payload are used for adding task to existing task list
            mock_planka_api_client.post.assert_called_once_with(
                "taskLists/tasklist1/tasks",
                {"name": "New Test Task"}
            )

    @pytest.mark.asyncio
    async def test_add_task_create_new_task_list(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_card_data
    ):
        """Test successful task creation when no task list exists."""
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            # Card has no task lists
            card_response = {"included": {"taskLists": []}}
            created_task_list = {"item": {"id": "new_tasklist", "name": "Tasks"}}
            created_task = {"item": {"id": "new_task", "name": "New Test Task"}}
            
            # Mock the API calls - first call creates task list, second call creates task
            mock_planka_api_client.get.return_value = card_response
            mock_planka_api_client.post.side_effect = [created_task_list, created_task]

            params = AddTaskInput(card_id="card1", task_name="New Test Task")
            result = await planka_add_task(params)

            assert "Added task" in result
            assert "New Test Task" in result
            # Verify the correct endpoints and payloads are used
            calls = mock_planka_api_client.post.call_args_list
            assert len(calls) == 2
            # First call should create task list - FIXED: now uses "taskLists" instead of "task-lists"
            assert calls[0] == call("taskLists", {"name": "Tasks", "cardId": "card1"})
            # Second call should create task
            assert calls[1] == call("taskLists/new_tasklist/tasks", {"name": "New Test Task"})

    @pytest.mark.asyncio
    async def test_add_task_endpoint_correction(
        self,
        mock_planka_api_client,
        mock_cache,
        sample_card_data
    ):
        """Test that verifies the correct API endpoint is used for task list creation.
        
        This test demonstrates the bug: the current implementation uses 'task-lists' 
        but the Planka API expects 'taskLists' (camelCase).
        """
        with patch("planka_mcp.instances.api_client", mock_planka_api_client), \
             patch("planka_mcp.instances.cache", mock_cache):
            # Card has no task lists
            card_response = {"included": {"taskLists": []}}
            created_task_list = {"item": {"id": "new_tasklist", "name": "Tasks"}}
            created_task = {"item": {"id": "new_task", "name": "New Test Task"}}
            
            # Mock the API calls
            mock_planka_api_client.get.return_value = card_response
            mock_planka_api_client.post.side_effect = [created_task_list, created_task]

            params = AddTaskInput(card_id="card1", task_name="New Test Task")
            result = await planka_add_task(params)

            # Check what endpoint was actually called
            calls = mock_planka_api_client.post.call_args_list
            first_call_endpoint = calls[0][0][0]
            
            # This will fail with current implementation, demonstrating the bug
            assert first_call_endpoint == "taskLists", f"Expected 'taskLists' but got '{first_call_endpoint}'"

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
