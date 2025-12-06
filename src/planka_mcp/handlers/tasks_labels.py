from typing import List, Dict, Any, Optional
from ..models import AddTaskInput, UpdateTaskInput, AddCardLabelInput, RemoveCardLabelInput
from ..utils import ResponseFormatter, handle_api_error
from ..api_client import PlankaAPIClient
from ..cache import PlankaCache

# Global instances imported from server
from ..server import api_client, cache

# Import fetch_workspace_data from workspace module
from .workspace import fetch_workspace_data

# ==================== TOOLS ====================

async def planka_add_task(params: AddTaskInput) -> str:
    '''Add a task (checklist item) to a card.

    Creates a task in the specified task list (or creates "Tasks" list if not exists).
    Common pattern for tracking subtasks within cards.

    Args:
        params (AddTaskInput): Card ID, task name, and optional task list name

    Returns:
        str: Confirmation with task details

    Examples:
        - "Add task 'Contact support' to card abc123" → Adds task
        - "Add checklist item 'Review PR' to card xyz789" → Adds task
    '''
    try:
        # First, get the card to check for existing task lists
        card_detail = await api_client.get(f"cards/{params.card_id}")
        included = card_detail.get("included", {})
        task_lists = included.get("taskLists", [])

        # Find or create the task list
        task_list = None
        task_list_name = params.task_list_name or "Tasks"

        # Look for existing task list with matching name
        for tl in task_lists:
            if tl.get("name", "").lower() == task_list_name.lower():
                task_list = tl
                break

        # If no task list exists, create one
        if not task_list:
            response = await api_client.post(
                f"cards/{params.card_id}/task-lists",
                {"name": task_list_name}
            )
            task_list = response.get("item", {})

        # Create the task
        task_response = await api_client.post(
            f"task-lists/{task_list['id']}/tasks",
            {"name": params.task_name}
        )
        task = task_response.get("item", {})

        # Invalidate card cache
        cache.invalidate_card(params.card_id)

        return f"✓ Added task: **{task.get('name', 'Unnamed')}** to list '{task_list.get('name', 'Tasks')}' (Task ID: `{task.get('id', 'N/A')}`)"

    except Exception as e:
        return handle_api_error(e)

async def planka_update_task(params: UpdateTaskInput) -> str:
    '''Update a task's completion status.

    Mark a task as completed or incomplete. Returns updated progress.

    Args:
        params (UpdateTaskInput): Task ID and completion status

    Returns:
        str: Confirmation with updated task status

    Examples:
        - "Mark task abc123 as complete" → Sets isCompleted=true
        - "Mark task xyz789 as incomplete" → Sets isCompleted=false
    '''
    try:
        # Update task
        response = await api_client.patch(
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

async def planka_add_card_label(params: AddCardLabelInput) -> str:
    '''Add a label to a card.

    Assigns an existing label to a card. Use planka_get_workspace to see available
    labels and their IDs.

    Args:
        params (AddCardLabelInput): Card ID and label ID

    Returns:
        str: Confirmation with label name

    Examples:
        - "Add the 'Critical' label to card abc123" → Adds label to card
        - "Label card xyz789 as 'In Progress'" → Adds label to card
    '''
    try:
        # Add label to card
        response = await api_client.post(
            f"cards/{params.card_id}/labels",
            {"labelId": params.label_id}
        )

        # Get workspace to find label name
        workspace = await cache.get_workspace(fetch_workspace_data)
        label_name = workspace.get('labels', {}).get(params.label_id, {}).get('name', 'Unknown')

        # Invalidate card cache
        cache.invalidate_card(params.card_id)

        return f"✓ Added label **{label_name}** to card (Label ID: `{params.label_id}`)"

    except Exception as e:
        return handle_api_error(e)

async def planka_remove_card_label(params: RemoveCardLabelInput) -> str:
    '''Remove a label from a card.

    Removes a label assignment from a card.

    Args:
        params (RemoveCardLabelInput): Card ID and label ID

    Returns:
        str: Confirmation with label name

    Examples:
        - "Remove the 'Critical' label from card abc123" → Removes label
        - "Unlabel card xyz789" → Removes label
    '''
    try:
        # Get workspace to find label name before removing
        workspace = await cache.get_workspace(fetch_workspace_data)
        label_name = workspace.get('labels', {}).get(params.label_id, {}).get('name', 'Unknown')

        # Remove label from card
        await api_client.delete(f"cards/{params.card_id}/labels/{params.label_id}")

        # Invalidate card cache
        cache.invalidate_card(params.card_id)

        return f"✓ Removed label **{label_name}** from card (Label ID: `{params.label_id}`)"

    except Exception as e:
        return handle_api_error(e)