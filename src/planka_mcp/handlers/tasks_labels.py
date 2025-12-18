from typing import List, Dict, Any, Optional
from ..models import AddTaskInput, UpdateTaskInput, AddCardLabelInput, RemoveCardLabelInput, DeleteTaskInput
from ..utils import ResponseFormatter, handle_api_error
from ..api_client import PlankaAPIClient
from ..cache import PlankaCache

from .. import instances # Import the instances module itself

# Import fetch_workspace_data from workspace module
from .workspace import fetch_workspace_data

# ==================== TOOLS ====================

async def planka_add_task(params: AddTaskInput) -> str:
    """Add a task (checklist item) to a card."

    Creates a task directly on the card using the correct Planka API endpoint.
    Common pattern for tracking subtasks within cards.

    Args:
        params (AddTaskInput): Card ID, task name, and optional task list name

    Returns:
        str: Confirmation with task details

    Examples:
        - "Add task 'Contact support' to card abc123" → Adds task
        - "Add checklist item 'Review PR' to card xyz789" → Adds task
    """
    if instances.api_client is None or instances.cache is None:
        return handle_api_error(RuntimeError("API client or Cache not initialized"))

    try:
        # Create the task directly on the card using the correct endpoint
        # POST /api/cards/{cardId}/tasks - as per official Planka API documentation
        task_response = await instances.api_client.post(
            f"cards/{params.card_id}/tasks",
            {"name": params.task_name, "position": 65535}
        )
        task = task_response.get("item", {})

        # Invalidate card cache
        instances.cache.invalidate_card(params.card_id)

        return f"✓ Added task: **{task.get('name', 'Unnamed')}** (Task ID: `{task.get('id', 'N/A')}`)"

    except Exception as e:
        return handle_api_error(e)

async def planka_update_task(params: UpdateTaskInput) -> str:
    """Update a task's completion status."

    Mark a task as completed or incomplete. Returns updated progress.

    Args:
        params (UpdateTaskInput): Task ID and completion status

    Returns:
        str: Confirmation with updated task status

    Examples:
        - "Mark task abc123 as complete" → Sets isCompleted=true
        - "Mark task xyz789 as incomplete" → Sets isCompleted=false
    """
    if instances.api_client is None:
        return handle_api_error(RuntimeError("API client not initialized"))

    try:
        # Update task
        response = await instances.api_client.patch(
            f"tasks/{params.task_id}",
            {"isCompleted": params.is_completed}
        )
        task = response.get("item", {})

        # Invalidate card cache (task belongs to card via task list)
        # Note: We'd need to track card_id, but for now we'll leave it
        # The cache will expire naturally within 1 minute

        status = "complete" if params.is_completed else "incomplete"
        check = "[x]" if params.is_completed else "[ ]"

        return f"✓ Marked task as {status}: {check} **{task.get('name', 'Unnamed task')}** (ID: `{task.get('id', params.task_id)}`)"

    except Exception as e:
        return handle_api_error(e)

async def planka_delete_task(params: DeleteTaskInput) -> str:
    """Delete a task from a card."

    Permanently removes a task from a card. The task cannot be recovered.

    Args:
        params (DeleteTaskInput): Task ID to delete

    Returns:
        str: Confirmation with deleted task ID

    Examples:
        - "Delete task abc123" → Removes the task permanently
        - "Remove task xyz789" → Deletes the task from the card
    """
    if instances.api_client is None:
        return handle_api_error(RuntimeError("API client not initialized"))

    try:
        # Get task details first to get task name for confirmation
        # The API client now handles empty responses gracefully
        task_response = await instances.api_client.get(f"tasks/{params.task_id}")
        task = task_response.get("item", {}) if task_response else {}
        task_name = task.get("name", f"Task {params.task_id}")

        # Delete the task using DELETE /api/tasks/{taskId}
        # The API client now handles empty responses (204 No Content) gracefully
        await instances.api_client.delete(f"tasks/{params.task_id}")

        # Note: We'd need to track card_id for cache invalidation, but for now we'll leave it
        # The cache will expire naturally within 1 minute

        return f"✓ Deleted task: **{task_name}** (ID: `{params.task_id}`)"

    except Exception as e:
        return handle_api_error(e)

async def planka_add_card_label(params: AddCardLabelInput) -> str:
    """Add a label to a card."

    Assigns an existing label to a card. Use planka_get_workspace to see available
    labels and their IDs.

    Args:
        params (AddCardLabelInput): Card ID and label ID

    Returns:
        str: Confirmation with label name

    Examples:
        - "Add the 'Critical' label to card abc123" → Adds label to card
        - "Label card xyz789 as 'In Progress'" → Adds label to card
    """
    if instances.api_client is None or instances.cache is None:
        return handle_api_error(RuntimeError("API client or Cache not initialized"))

    try:
        # Add label to card
        response = await instances.api_client.post(
            f"cards/{params.card_id}/labels",
            {"labelId": params.label_id}
        )

        # Get workspace to find label name
        workspace = await instances.cache.get_workspace(fetch_workspace_data)
        label_name = workspace.get('labels', {}).get(params.label_id, {}).get('name', 'Unknown')

        # Invalidate card cache
        instances.cache.invalidate_card(params.card_id)

        return f"✓ Added label **{label_name}** to card (Label ID: `{params.label_id}`)"

    except Exception as e:
        return handle_api_error(e)

async def planka_remove_card_label(params: RemoveCardLabelInput) -> str:
    """Remove a label from a card."

    Removes a label assignment from a card.

    Args:
        params (RemoveCardLabelInput): Card ID and label ID

    Returns:
        str: Confirmation with label name

    Examples:
        - "Remove the 'Critical' label from card abc123" → Removes label
        - "Unlabel card xyz789" → Removes label
    """
    if instances.api_client is None or instances.cache is None:
        return handle_api_error(RuntimeError("API client or Cache not initialized"))

    try:
        # Get workspace to find label name before removing
        workspace = await instances.cache.get_workspace(fetch_workspace_data)
        label_name = workspace.get('labels', {}).get(params.label_id, {}).get('name', 'Unknown')

        # Remove label from card
        await instances.api_client.delete(f"cards/{params.card_id}/labels/{params.label_id}")

        # Invalidate card cache
        instances.cache.invalidate_card(params.card_id)

        return f"✓ Removed label **{label_name}** from card (Label ID: `{params.label_id}`)"

    except Exception as e:
        return handle_api_error(e)