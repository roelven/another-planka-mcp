from typing import List, Dict, Any, Optional
from ..models import ListCardsInput, GetCardInput, CreateCardInput, UpdateCardInput, ResponseFormat, DetailLevel
from ..utils import ResponseFormatter, PaginationHelper, handle_api_error
from ..api_client import PlankaAPIClient
from ..cache import PlankaCache

from .. import instances # Import the instances module itself
from .workspace import fetch_workspace_data

# ==================== TOOLS ====================

async def planka_list_cards(params: ListCardsInput) -> str:
    """List cards from a Planka board with smart filtering and detail levels."

    Supports cross-list queries (set list_id=None to get ALL cards from board) and label
    filtering. Use detail_level to control token usage: preview mode saves 60-88% tokens
    when browsing cards.

    Args:
        params (ListCardsInput): Filtering and formatting parameters

    Returns:
        str: Formatted list of cards matching the criteria

    Examples:
        - "Show me all In Progress cards" → board_id="X", list_id=None, label_filter="In Progress"
        - "What cards are in the TODO list?" → board_id="X", list_id="Y"
        - "Find all Critical bugs" → board_id="X", label_filter="Critical"
        - Use detail_level="preview" for quick browsing (saves 88% tokens vs detailed)
    """
    if instances.api_client is None:
        return handle_api_error(RuntimeError("API client not initialized"))

    try:
        # Fetch board details (includes lists, labels, cards)
        board_detail = await instances.api_client.get(f"boards/{params.board_id}")
        board = board_detail.get("item", {})
        included = board_detail.get("included", {})

        # Build context maps for formatters
        lists_map = {lst["id"]: lst for lst in included.get("lists", [])}
        labels_map = {lbl["id"]: lbl for lbl in included.get("labels", [])}
        users_map = {usr["id"]: usr for usr in included.get("users", [])}

        # Build card labels mapping from cardLabels join table
        # Planka uses normalized structure: cardLabels = [{id, cardId, labelId}, ...]
        card_labels_map = {}
        for card_label in included.get("cardLabels", []):
            card_id = card_label.get("cardId")
            label_id = card_label.get("labelId")
            if card_id and label_id:
                if card_id not in card_labels_map:
                    card_labels_map[card_id] = []
                card_labels_map[card_id].append(label_id)

        context = {
            'lists': lists_map,
            'labels': labels_map,
            'users': users_map,
            'card_labels': card_labels_map,
            'board_name': board.get("name", "Unknown Board")
        }

        # Get all cards from included
        cards = included.get("cards", [])

        # Filter by list if specified
        if params.list_id:
            cards = [c for c in cards if c.get('listId') == params.list_id]

        # Filter by label if specified (case-insensitive partial match)
        if params.label_filter:
            label_lower = params.label_filter.lower()
            cards = [
                c for c in cards
                if any(
                    label_lower in labels_map.get(label_id, {}).get('name', '').lower()
                    for label_id in card_labels_map.get(c.get('id'), [])
                )
            ]

        # Paginate
        paginated = PaginationHelper.paginate_results(
            cards,
            params.offset,
            params.limit
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            content = ResponseFormatter.format_card_list_markdown(
                paginated["items"],
                context,
                params.detail_level
            )

            # Add pagination info if there's more data
            if paginated["has_more"]:
                content += f"\n\n---\n**Pagination**: Showing {paginated['count']} of {paginated['total']} cards. "
                content += f"Use offset={paginated['next_offset']} to see more.\n"
        else:
            content = json.dumps({
                "board": {
                    "id": board["id"],
                    "name": board.get("name", "Unknown Board")
                },
                "cards": paginated["items"],
                "pagination": paginated
            }, indent=2)

        return ResponseFormatter.truncate_response(content)

    except Exception as e:
        return handle_api_error(e)

async def planka_get_card(params: GetCardInput) -> str:
    """Get complete details for a specific card."

    Returns full card information including tasks, comments, attachments, members, and labels.
    Uses response_context parameter to control how much metadata is included.

    Args:
        params (GetCardInput): Card ID and formatting preferences

    Returns:
        str: Complete card details with all related information

    Examples:
        - "Show me everything about card abc123" → Full card details
        - "Get card details for xyz789" → Complete information
    """
    if instances.api_client is None or instances.cache is None:
        return handle_api_error(RuntimeError("API client or Cache not initialized"))

    try:
        # Fetch card with caching
        async def fetch_card():
            card_detail = await instances.api_client.get(f"cards/{params.card_id}")
            full_card = card_detail.get("item", {})
            included = card_detail.get("included", {})

            # Merge included data into card
            full_card['taskLists'] = included.get('taskLists', [])
            full_card['comments'] = included.get('comments', [])
            full_card['attachments'] = included.get('attachments', [])
            full_card['_included_labels'] = included.get('labels', [])
            full_card['_included_users'] = included.get('users', [])
            full_card['_included_cardLabels'] = included.get('cardLabels', [])

            return full_card

        card = await instances.cache.get_card(params.card_id, fetch_card)

        # Build context from workspace
        workspace = await instances.cache.get_workspace(fetch_workspace_data)

        # Use included data if available, otherwise use workspace data
        labels_map = {lbl["id"]: lbl for lbl in card.get('_included_labels', [])}
        if not labels_map:
            labels_map = workspace.get('labels', {})

        users_map = {usr["id"]: usr for usr in card.get('_included_users', [])}
        if not users_map:
            users_map = workspace.get('users', {})

        # Build card labels mapping from cardLabels join table
        card_labels_map = {}
        included_card_labels = card.get('_included_cardLabels', [])
        if included_card_labels:
            for card_label in included_card_labels:
                card_id = card_label.get("cardId")
                label_id = card_label.get("labelId")
                if card_id and label_id:
                    if card_id not in card_labels_map:
                        card_labels_map[card_id] = []
                    card_labels_map[card_id].append(label_id)
        else:
            card_labels_map = workspace.get('card_labels', {})

        context = {
            'lists': workspace.get('lists', {}),
            'labels': labels_map,
            'users': users_map,
            'card_labels': card_labels_map,
            'board_name': workspace.get('boards', {}).get(card.get('boardId'), {}).get('name', 'Unknown Board')
        }

        if params.response_format == ResponseFormat.MARKDOWN:
            content = ResponseFormatter.format_card_detailed(card, context)
        else:
            content = json.dumps(card, indent=2)

        return ResponseFormatter.truncate_response(content)

    except Exception as e:
        return handle_api_error(e)

async def planka_create_card(params: CreateCardInput) -> str:
    """Create a new card in a Planka list."

    Creates a card with the specified name, description, and optional due date. Returns
    minimal confirmation to save tokens.

    Args:
        params (CreateCardInput): Card details (list_id, name, description, due_date, position)

    Returns:
        str: Minimal confirmation with card ID and name

    Examples:
        - "Create a card called 'Fix login bug' in the TODO list" → Creates card
        - "Add new task 'Update docs' with description..." → Creates card with details
    """
    if instances.api_client is None or instances.cache is None:
        return handle_api_error(RuntimeError("API client or Cache not initialized"))

    try:
        # Verify list exists in workspace
        workspace = await instances.cache.get_workspace(fetch_workspace_data)
        list_info = workspace.get('lists', {}).get(params.list_id)

        if not list_info:
            return f"Error: List ID '{params.list_id}' not found. Use planka_get_workspace to see valid list IDs."

        board_id = list_info.get('boardId')

        # Build request body for /api/lists/:listId/cards endpoint
        # Required: type (project or story), name, position
        card_data = {
            "type": "project",  # Required field - use "project" as default
            "name": params.name,
            "position": params.position if params.position is not None else 65535
        }

        if params.description:
            card_data["description"] = params.description
        if params.due_date:
            card_data["dueDate"] = params.due_date

        # Create card using correct endpoint: POST /api/lists/:listId/cards
        response = await instances.api_client.post(f"lists/{params.list_id}/cards", card_data)
        card = response.get("item", {})

        # Invalidate board cache (board now has new card)
        instances.cache.invalidate_board(board_id)

        # Return minimal confirmation
        return f"✓ Created card: **{card.get('name', 'Untitled')}** (ID: `{card.get('id', 'N/A')}`)"

    except Exception as e:
        return handle_api_error(e)

async def planka_update_card(params: UpdateCardInput) -> str:
    """Update an existing card's details."

    Modify card name, description, due date, position, or move to different list.
    Invalidates relevant caches automatically.

    Args:
        params (UpdateCardInput): Card ID and fields to update

    Returns:
        str: Minimal confirmation with updated fields

    Examples:
        - "Update card abc123 description to..." → Updates description
        - "Move card xyz789 to the Done list" → Moves card to different list
    """
    if instances.api_client is None or instances.cache is None:
        return handle_api_error(RuntimeError("API client or Cache not initialized"))

    try:
        # Build update payload (only include fields that are provided)
        update_data = {}

        if params.name is not None:
            update_data["name"] = params.name
        if params.description is not None:
            update_data["description"] = params.description
        if params.due_date is not None:
            update_data["dueDate"] = params.due_date
        if params.list_id is not None:
            update_data["listId"] = params.list_id
            # When moving to different list, position is REQUIRED by Planka API
            # If not provided, use default position at end of list
            if params.position is None:
                update_data["position"] = 65535
        if params.position is not None:
            update_data["position"] = params.position

        # Update card
        response = await instances.api_client.patch(f"cards/{params.card_id}", update_data)
        card = response.get("item", {})

        # Invalidate caches
        instances.cache.invalidate_card(params.card_id)
        if card.get('boardId'):
            instances.cache.invalidate_board(card['boardId'])

        # Build confirmation message
        updates = []
        if params.name:
            updates.append("name")
        if params.description is not None:
            updates.append("description")
        if params.due_date:
            updates.append("due date")
        if params.list_id:
            updates.append("list (moved)")
        if params.position is not None:
            updates.append("position")

        update_str = ", ".join(updates) if updates else "card"

        return f"✓ Updated {update_str} for card: **{card.get('name', 'Untitled')}** (ID: `{card.get('id', params.card_id)}`)"

    except Exception as e:
        return handle_api_error(e)