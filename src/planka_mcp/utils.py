import json
import httpx
from typing import List, Dict, Any, Optional
from .models import ResponseFormat, DetailLevel

# ==================== ERROR HANDLING ====================

def handle_api_error(e: Exception) -> str:
    """Consistent, actionable error messages."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return "Error: Invalid API credentials. Check your access token or API key in the .env file."
        elif status == 403:
            return "Error: You don't have permission to access this resource. You may need board membership."
        elif status == 404:
            return "Error: Resource not found. Check that the ID is correct and the resource exists."
        elif status == 429:
            return "Error: Rate limit exceeded. Wait a moment before trying again."
        else:
            return f"Error: API request failed (HTTP {status}). Please try again."
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. The Planka server may be slow or unreachable."
    elif isinstance(e, httpx.ConnectError):
        return "Error: Cannot connect to Planka server. Check the PLANKA_BASE_URL in your .env file."
    return f"Error: Unexpected error - {type(e).__name__}: {str(e)}"

# ==================== RESPONSE FORMATTING ====================

class ResponseFormatter:
    """Shared formatting logic for consistent outputs."""

    @staticmethod
    def truncate_response(content: str, limit: int = 25000) -> str:
        """Truncate response if over limit."""
        if len(content) <= limit:
            return content

        truncate_at = int(limit * 0.6)
        truncated = content[:truncate_at]

        last_newline = truncated.rfind('\n')
        if last_newline > truncate_at * 0.8:
            truncated = truncated[:last_newline]

        warning = f"""
---
⚠️ **RESPONSE TRUNCATED**: Output was {len(content):,} characters (limit: {limit:,})

**To see more results:**
- Use pagination: Increase `offset` parameter
- Add filters: Use `list_id` or `label_filter` to filter results
- Reduce detail: Use `detail_level="preview"` instead of "summary" or "detailed"
---
"""
        return truncated + warning

    @staticmethod
    def format_task_progress(task_lists: List[Dict]) -> str:
        """Format task progress as 'completed/total'."""
        total_tasks = 0
        completed_tasks = 0
        for task_list in task_lists:
            for task in task_list.get('tasks', []):
                total_tasks += 1
                if task.get('isCompleted', False):
                    completed_tasks += 1
        if total_tasks == 0:
            return "0/0"
        return f"{completed_tasks}/{total_tasks}"

    @staticmethod
    def format_card_preview(card: Dict, context: Dict) -> str:
        """Format card in preview mode (~50 tokens)."""
        list_name = context.get('lists', {}).get(card.get('listId'), {}).get('name', 'Unknown List')
        # Get label IDs from card_labels mapping (cardLabels join table)
        card_label_ids = context.get('card_labels', {}).get(card.get('id'), [])
        labels = [context.get('labels', {}).get(label_id, {}).get('name', '')
                  for label_id in card_label_ids]

        task_progress = ResponseFormatter.format_task_progress(card.get('taskLists', []))

        return f"""- **{card.get('name', 'Untitled')}** (ID: `{card.get('id', 'N/A')}`)
  - List: {list_name}
  - Labels: {', '.join(labels) if labels else 'None'}
  - Due: {card.get('dueDate', 'No due date')}
  - Tasks: {task_progress}
  - Comments: {len(card.get('comments', []))}
  - Attachments: {len(card.get('attachments', []))}"""

    @staticmethod
    def format_card_summary(card: Dict, context: Dict) -> str:
        """Format card in summary mode (~200 tokens)."""
        list_name = context.get('lists', {}).get(card.get('listId'), {}).get('name', 'Unknown List')
        # Get label IDs from card_labels mapping (cardLabels join table)
        card_label_ids = context.get('card_labels', {}).get(card.get('id'), [])
        labels = [context.get('labels', {}).get(label_id, {}).get('name', '')
                  for label_id in card_label_ids]
        members = [context.get('users', {}).get(user_id, {}).get('name', '')
                   for user_id in card.get('memberIds', [])]

        task_progress = ResponseFormatter.format_task_progress(card.get('taskLists', []))
        description = card.get('description', '')
        desc_snippet = (description[:100] + '...') if len(description) > 100 else description

        return f"""### {card.get('name', 'Untitled')}
**ID**: `{card.get('id', 'N/A')}`
**List**: {list_name}
**Labels**: {', '.join(labels) if labels else 'None'}
**Members**: {', '.join(members) if members else 'None'}
**Due Date**: {card.get('dueDate', 'No due date')}
**Created**: {card.get('createdAt', 'Unknown')}
**Tasks**: {task_progress}
**Comments**: {len(card.get('comments', []))}
**Attachments**: {len(card.get('attachments', []))}

**Description**: {desc_snippet if desc_snippet else '(No description)'}
"""

    @staticmethod
    def format_card_detailed(card: Dict, context: Dict) -> str:
        """Format card in detailed mode (~400 tokens)."""
        list_name = context.get('lists', {}).get(card.get('listId'), {}).get('name', 'Unknown List')
        # Get label IDs from card_labels mapping (cardLabels join table)
        card_label_ids = context.get('card_labels', {}).get(card.get('id'), [])
        labels = [context.get('labels', {}).get(label_id, {}).get('name', '')
                  for label_id in card_label_ids]
        members = [context.get('users', {}).get(user_id, {}).get('name', '')
                   for user_id in card.get('memberIds', [])]

        output = f"""# {card.get('name', 'Untitled')}

**ID**: `{card.get('id', 'N/A')}`
**List**: {list_name} (ID: `{card.get('listId', 'N/A')}`)
**Board**: {context.get('board_name', 'Unknown')}

## Details
- **Due Date**: {card.get('dueDate', 'No due date')}
- **Created**: {card.get('createdAt', 'Unknown')}
- **Updated**: {card.get('updatedAt', 'Unknown')}
- **Position**: {card.get('position', 'N/A')}

## Members
{', '.join(members) if members else '(No members assigned)'}

## Labels
{', '.join(labels) if labels else '(No labels)'}

## Description
{card.get('description', '(No description)')}

## Tasks
"""
        task_lists = card.get('taskLists', [])
        if task_lists:
            for task_list in task_lists:
                output += f"\n**{task_list.get('name', 'Tasks')}**:\n"
                for task in task_list.get('tasks', []):
                    check = '[x]' if task.get('isCompleted', False) else '[ ]'
                    output += f"- {check} {task.get('name', 'Unnamed task')} (ID: `{task.get('id', 'N/A')}`)\n"
        else:
            output += "(No tasks)\n"

        output += "\n## Comments\n"
        comments = card.get('comments', [])
        if comments:
            for comment in comments:
                user_id = comment.get('userId', 'Unknown')
                user_name = context.get('users', {}).get(user_id, {}).get('name', 'Unknown User')
                output += f"- **{user_name}** ({comment.get('createdAt', 'Unknown')}): {comment.get('text', '')}\n"
        else:
            output += "(No comments)\n"

        output += f"\n## Attachments\n"
        attachments = card.get('attachments', [])
        if attachments:
            for att in attachments:
                output += f"- {att.get('name', 'Unnamed')} (ID: `{att.get('id', 'N/A')}`)\n"
        else:
            output += "(No attachments)\n"

        return output

    @staticmethod
    def format_card_list_markdown(
        cards: List[Dict],
        context: Dict,
        detail_level: DetailLevel
    ) -> str:
        """Format multiple cards as Markdown list."""
        if not cards:
            return "No cards found matching the criteria."

        output = f"# Cards ({len(cards)} found)\n\n"

        for card in cards:
            if detail_level == DetailLevel.PREVIEW:
                output += ResponseFormatter.format_card_preview(card, context) + "\n\n"
            elif detail_level == DetailLevel.SUMMARY:
                output += ResponseFormatter.format_card_summary(card, context) + "\n"
            else:  # DETAILED
                output += ResponseFormatter.format_card_detailed(card, context) + "\n---\n\n"

        return output.strip()


# ==================== PAGINATION ====================

class PaginationHelper:
    """Handles pagination logic consistently."""

    @staticmethod
    def paginate_results(
        items: List[Dict],
        offset: int,
        limit: int,
        total: Optional[int] = None
    ) -> Dict:
        """Return paginated results with metadata."""
        # Defensive programming: handle None items gracefully
        if items is None:
            items = []
        
        total = total or len(items)
        paginated_items = items[offset:offset + limit]

        return {
            "items": paginated_items,
            "offset": offset,
            "limit": limit,
            "count": len(paginated_items),
            "total": total,
            "has_more": offset + limit < total,
            "next_offset": offset + limit if offset + limit < total else None
        }