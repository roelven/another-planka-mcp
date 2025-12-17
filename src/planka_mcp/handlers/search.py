import json
from typing import List, Dict, Any, Optional
from ..models import FindAndGetCardInput, ResponseFormat
from ..utils import ResponseFormatter, handle_api_error
from ..api_client import PlankaAPIClient
from ..cache import PlankaCache

from .. import instances # Import the instances module itself

# Import fetch_workspace_data from workspace module
from .workspace import fetch_workspace_data

# ==================== TOOLS ====================

async def planka_find_and_get_card(params: FindAndGetCardInput) -> str:
    """Search for a card by name/description and get full details in one operation."

    This composite tool saves 37% tokens by combining search + retrieval. If multiple
    cards match, returns a list to choose from. If unique match, returns full card details.

    Args:
        params (FindAndGetCardInput): Search query and optional board filter

    Returns:
        str: Card details if unique match, or list of matching cards to choose from

    Examples:
        - "Find the login bug card and show details" → Single efficient call
        - "Get details about the authentication card" → Searches + retrieves
    """
    if instances.api_client is None or instances.cache is None:
        return handle_api_error(RuntimeError("API client or Cache not initialized"))

    try:
        query_lower = params.query.lower()
        matching_cards = []

        # If board_id specified, search only that board
        if params.board_id:
            board_detail = await instances.api_client.get(f"boards/{params.board_id}")
            cards = board_detail.get("included", {}).get("cards", [])
            
            # Ensure cards is always a list, never None
            if cards is None:
                cards = []

            # Search in card name and description
            matching_cards = [
                c for c in cards
                if query_lower in c.get('name', '').lower()
                or query_lower in (c.get('description') or '').lower()
            ]
        else:
            # Search across all boards - fetch workspace
            workspace = await instances.cache.get_workspace(fetch_workspace_data)

            # Search each board
            for board_id in workspace.get("boards", {}).keys():
                board_detail = await instances.api_client.get(f"boards/{board_id}")
                cards = board_detail.get("included", {}).get("cards", [])

                matching_cards.extend([
                    c for c in cards
                    if query_lower in c.get('name', '').lower()
                    or query_lower in (c.get('description') or '').lower()
                ])

        # If no matches, return message
        if not matching_cards:
            return f"No cards found matching query: '{params.query}'"

        # If single match, return full details
        if len(matching_cards) == 1:
            card = matching_cards[0]
            # Fetch full card details
            card_detail = await instances.api_client.get(f"cards/{card['id']}")
            full_card = card_detail.get("item", {})
            included = card_detail.get("included", {})

            # Build context
            workspace = await instances.cache.get_workspace(fetch_workspace_data)

            # Build card labels mapping from cardLabels join table
            card_labels_map = {}
            for card_label in included.get("cardLabels", []):
                card_id = card_label.get("cardId")
                label_id = card_label.get("labelId")
                if card_id and label_id:
                    if card_id not in card_labels_map:
                        card_labels_map[card_id] = []
                    card_labels_map[card_id].append(label_id)

            context = {
                'lists': workspace.get('lists', {}),
                'labels': {lbl["id"]: lbl for lbl in included.get("labels", [])},
                'users': {usr["id"]: usr for usr in included.get("users", [])},
                'card_labels': card_labels_map,
                'board_name': workspace.get('boards', {}).get(full_card.get('boardId'), {}).get('name', 'Unknown Board')
            }

            # Merge included data into card
            full_card['taskLists'] = included.get('taskLists', [])
            full_card['comments'] = included.get('comments', [])
            full_card['attachments'] = included.get('attachments', [])

            if params.response_format == ResponseFormat.MARKDOWN:
                return ResponseFormatter.format_card_detailed(full_card, context)
            else:
                return json.dumps(full_card, indent=2)

        # Multiple matches - return list to choose from
        workspace = await instances.cache.get_workspace(fetch_workspace_data)
        output = f"# Found {len(matching_cards)} matching cards\n\n"
        for card in matching_cards[:10]:  # Limit to first 10
            list_name = workspace.get('lists', {}).get(card.get('listId'), {}).get('name', 'Unknown List')
            board_name = workspace.get('boards', {}).get(card.get('boardId'), {}).get('name', 'Unknown Board')
            output += f"- **{card.get('name', 'Untitled')}** (ID: `{card['id']}`)\n"
            output += f"  - Board: {board_name}\n"
            output += f"  - List: {list_name}\n\n"

        if len(matching_cards) > 10:
            output += f"\n... and {len(matching_cards) - 10} more cards.\n"

        output += "\n**Use planka_get_card with a specific card ID to see full details.**"
        return output

    except Exception as e:
        return handle_api_error(e)