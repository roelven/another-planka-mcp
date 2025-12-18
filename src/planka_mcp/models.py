from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field, ConfigDict

# ==================== ENUMS ====================

class ResponseFormat(str, Enum):
    """Output format options."""
    MARKDOWN = "markdown"
    JSON = "json"

class DetailLevel(str, Enum):
    """Level of detail in card responses (token optimization)."""
    PREVIEW = "preview"      # Minimal: ID, name, list, due date only (~50 tokens/card)
    SUMMARY = "summary"      # Standard: + members, labels, task progress (~200 tokens/card)
    DETAILED = "detailed"    # Complete: Everything including full tasks, comments (~400 tokens/card)

class ResponseContext(str, Enum):
    """How much context to include in responses (token optimization)."""
    MINIMAL = "minimal"      # IDs only, assume agent has context from workspace
    STANDARD = "standard"    # IDs + names (default, good balance)
    FULL = "full"           # Complete context with all metadata

# ==================== PYDANTIC MODELS ====================

class GetWorkspaceInput(BaseModel):
    """Input for getting workspace structure."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' (human-readable) or 'json' (machine-readable)"
    )

class ListCardsInput(BaseModel):
    """Input for listing cards with cross-list and label filtering support."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    board_id: str = Field(
        ...,
        description="Board ID to list cards from (e.g., 'abc123')",
        min_length=1,
        max_length=100
    )
    list_id: Optional[str] = Field(
        None,
        description="Optional: Filter to specific list ID. If None, returns cards from ALL lists",
        max_length=100
    )
    label_filter: Optional[str] = Field(
        None,
        description="Optional: Filter cards by label name (e.g., 'In Progress'). Case-insensitive partial match.",
        max_length=100
    )
    limit: int = Field(
        default=50,
        description="Maximum number of cards to return (1-100)",
        ge=1,
        le=100
    )
    offset: int = Field(
        default=0,
        description="Number of cards to skip for pagination",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )
    detail_level: DetailLevel = Field(
        default=DetailLevel.PREVIEW,
        description="Detail level: 'preview' (~50 tok/card), 'summary' (~200 tok/card), 'detailed' (~400 tok/card)"
    )
    response_context: ResponseContext = Field(
        default=ResponseContext.STANDARD,
        description="Context level: 'minimal' (IDs only), 'standard' (IDs+names), 'full' (complete)"
    )

class GetCardInput(BaseModel):
    """Input for getting a single card's details."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    card_id: str = Field(
        ...,
        description="Card ID to retrieve (e.g., 'card123')",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )
    response_context: ResponseContext = Field(
        default=ResponseContext.STANDARD,
        description="Context level: 'minimal', 'standard', or 'full'"
    )

class CreateCardInput(BaseModel):
    """Input for creating a new card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    list_id: str = Field(
        ...,
        description="List ID where card should be created",
        min_length=1,
        max_length=100
    )
    name: str = Field(
        ...,
        description="Card name/title",
        min_length=1,
        max_length=500
    )
    description: Optional[str] = Field(
        None,
        description="Optional: Card description (supports Markdown)",
        max_length=10000
    )
    due_date: Optional[str] = Field(
        None,
        description="Optional: Due date in ISO format (e.g., '2024-12-31T23:59:59Z')"
    )
    position: Optional[float] = Field(
        None,
        description="Optional: Position in list (lower = higher, default: bottom)"
    )

class UpdateCardInput(BaseModel):
    """Input for updating a card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    card_id: str = Field(
        ...,
        description="Card ID to update",
        min_length=1,
        max_length=100
    )
    name: Optional[str] = Field(
        None,
        description="Optional: New card name",
        max_length=500
    )
    description: Optional[str] = Field(
        None,
        description="Optional: New card description",
        max_length=10000
    )
    due_date: Optional[str] = Field(
        None,
        description="Optional: New due date in ISO format"
    )
    list_id: Optional[str] = Field(
        None,
        description="Optional: Move card to different list",
        max_length=100
    )
    position: Optional[float] = Field(
        None,
        description="Optional: New position in list"
    )

class AddTaskInput(BaseModel):
    """Input for adding a task to a card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    card_id: str = Field(
        ...,
        description="Card ID to add task to",
        min_length=1,
        max_length=100
    )
    task_name: str = Field(
        ...,
        description="Task description/name",
        min_length=1,
        max_length=500
    )
    task_list_name: Optional[str] = Field(
        default="Tasks",
        description="Optional: Task list name (default: 'Tasks')",
        max_length=100
    )

class UpdateTaskInput(BaseModel):
    """Input for updating a task."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    task_id: str = Field(
        ...,
        description="Task ID to update",
        min_length=1,
        max_length=100
    )
    is_completed: bool = Field(
        ...,
        description="Mark task as completed (true) or incomplete (false)"
    )

class FindAndGetCardInput(BaseModel):
    """Input for finding and getting a card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    query: str = Field(
        ...,
        description="Search query (searches in card names and descriptions)",
        min_length=1,
        max_length=200
    )
    board_id: Optional[str] = Field(
        None,
        description="Optional: Limit search to specific board",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )

class AddCardLabelInput(BaseModel):
    """Input for adding a label to a card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    card_id: str = Field(
        ...,
        description="Card ID to add label to",
        min_length=1,
        max_length=100
    )
    label_id: str = Field(
        ...,
        description="Label ID to add (get available labels from planka_get_workspace)",
        min_length=1,
        max_length=100
    )

class RemoveCardLabelInput(BaseModel):
    """Input for removing a label from a card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    card_id: str = Field(
        ...,
        description="Card ID to remove label from",
        min_length=1,
        max_length=100
    )
    label_id: str = Field(
        ...,
        description="Label ID to remove",
        min_length=1,
        max_length=100
    )

class DeleteCardInput(BaseModel):
    """Input for deleting a card."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    card_id: str = Field(
        ...,
        description="ID of the card to delete",
        min_length=1,
        max_length=100
    )
