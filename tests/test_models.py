"""Tests for Pydantic models and input validation."""

import pytest
from pydantic import ValidationError

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from planka_mcp import (
    GetWorkspaceInput,
    ListCardsInput,
    GetCardInput,
    CreateCardInput,
    UpdateCardInput,
    AddTaskInput,
    UpdateTaskInput,
    FindAndGetCardInput,
    AddCardLabelInput,
    RemoveCardLabelInput,
    ResponseFormat,
    DetailLevel,
    ResponseContext
)


class TestGetWorkspaceInput:
    """Test GetWorkspaceInput model."""

    def test_valid_input_default(self):
        """Test valid input with defaults."""
        input_data = GetWorkspaceInput()

        assert input_data.response_format == ResponseFormat.MARKDOWN

    def test_valid_input_json(self):
        """Test valid input with JSON format."""
        input_data = GetWorkspaceInput(response_format=ResponseFormat.JSON)

        assert input_data.response_format == ResponseFormat.JSON

    def test_invalid_response_format(self):
        """Test invalid response format."""
        with pytest.raises(ValidationError):
            GetWorkspaceInput(response_format="invalid")


class TestListCardsInput:
    """Test ListCardsInput model."""

    def test_valid_input_minimal(self):
        """Test valid input with minimal required fields."""
        input_data = ListCardsInput(board_id="board123")

        assert input_data.board_id == "board123"
        assert input_data.list_id is None
        assert input_data.label_filter is None
        assert input_data.limit == 50
        assert input_data.offset == 0
        assert input_data.detail_level == DetailLevel.PREVIEW

    def test_valid_input_full(self):
        """Test valid input with all fields."""
        input_data = ListCardsInput(
            board_id="board123",
            list_id="list456",
            label_filter="In Progress",
            limit=25,
            offset=10,
            response_format=ResponseFormat.JSON,
            detail_level=DetailLevel.DETAILED,
            response_context=ResponseContext.FULL
        )

        assert input_data.board_id == "board123"
        assert input_data.list_id == "list456"
        assert input_data.label_filter == "In Progress"
        assert input_data.limit == 25
        assert input_data.offset == 10

    def test_missing_required_board_id(self):
        """Test missing required board_id."""
        with pytest.raises(ValidationError):
            ListCardsInput()

    def test_limit_too_low(self):
        """Test limit below minimum."""
        with pytest.raises(ValidationError):
            ListCardsInput(board_id="board123", limit=0)

    def test_limit_too_high(self):
        """Test limit above maximum."""
        with pytest.raises(ValidationError):
            ListCardsInput(board_id="board123", limit=101)

    def test_negative_offset(self):
        """Test negative offset."""
        with pytest.raises(ValidationError):
            ListCardsInput(board_id="board123", offset=-1)

    def test_string_stripping(self):
        """Test that strings are stripped of whitespace."""
        input_data = ListCardsInput(board_id="  board123  ", label_filter="  Bug  ")

        assert input_data.board_id == "board123"
        assert input_data.label_filter == "Bug"

    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError):
            ListCardsInput(board_id="board123", extra_field="not allowed")


class TestGetCardInput:
    """Test GetCardInput model."""

    def test_valid_input(self):
        """Test valid input."""
        input_data = GetCardInput(card_id="card123")

        assert input_data.card_id == "card123"
        assert input_data.response_format == ResponseFormat.MARKDOWN
        assert input_data.response_context == ResponseContext.STANDARD

    def test_missing_card_id(self):
        """Test missing required card_id."""
        with pytest.raises(ValidationError):
            GetCardInput()

    def test_empty_card_id(self):
        """Test empty card_id."""
        with pytest.raises(ValidationError):
            GetCardInput(card_id="")


class TestCreateCardInput:
    """Test CreateCardInput model."""

    def test_valid_input_minimal(self):
        """Test valid input with minimal fields."""
        input_data = CreateCardInput(list_id="list123", name="Test Card")

        assert input_data.list_id == "list123"
        assert input_data.name == "Test Card"
        assert input_data.description is None
        assert input_data.due_date is None
        assert input_data.position is None

    def test_valid_input_full(self):
        """Test valid input with all fields."""
        input_data = CreateCardInput(
            list_id="list123",
            name="Test Card",
            description="Test description",
            due_date="2024-12-31T23:59:59Z",
            position=1024.5
        )

        assert input_data.list_id == "list123"
        assert input_data.name == "Test Card"
        assert input_data.description == "Test description"
        assert input_data.due_date == "2024-12-31T23:59:59Z"
        assert input_data.position == 1024.5

    def test_missing_list_id(self):
        """Test missing required list_id."""
        with pytest.raises(ValidationError):
            CreateCardInput(name="Test Card")

    def test_missing_name(self):
        """Test missing required name."""
        with pytest.raises(ValidationError):
            CreateCardInput(list_id="list123")

    def test_name_too_long(self):
        """Test name exceeding max length."""
        with pytest.raises(ValidationError):
            CreateCardInput(list_id="list123", name="A" * 501)

    def test_description_too_long(self):
        """Test description exceeding max length."""
        with pytest.raises(ValidationError):
            CreateCardInput(
                list_id="list123",
                name="Test Card",
                description="A" * 10001
            )


class TestUpdateCardInput:
    """Test UpdateCardInput model."""

    def test_valid_input_single_field(self):
        """Test updating single field."""
        input_data = UpdateCardInput(card_id="card123", name="New Name")

        assert input_data.card_id == "card123"
        assert input_data.name == "New Name"
        assert input_data.description is None

    def test_valid_input_multiple_fields(self):
        """Test updating multiple fields."""
        input_data = UpdateCardInput(
            card_id="card123",
            name="New Name",
            description="New Description",
            list_id="list456"
        )

        assert input_data.card_id == "card123"
        assert input_data.name == "New Name"
        assert input_data.description == "New Description"
        assert input_data.list_id == "list456"

    def test_missing_card_id(self):
        """Test missing required card_id."""
        with pytest.raises(ValidationError):
            UpdateCardInput(name="New Name")

    def test_all_optional_fields_none(self):
        """Test that all update fields can be None."""
        input_data = UpdateCardInput(card_id="card123")

        assert input_data.name is None
        assert input_data.description is None
        assert input_data.due_date is None
        assert input_data.list_id is None
        assert input_data.position is None


class TestAddTaskInput:
    """Test AddTaskInput model."""

    def test_valid_input_default_list(self):
        """Test valid input with default task list."""
        input_data = AddTaskInput(card_id="card123", task_name="Test Task")

        assert input_data.card_id == "card123"
        assert input_data.task_name == "Test Task"
        assert input_data.task_list_name == "Tasks"

    def test_valid_input_custom_list(self):
        """Test valid input with custom task list name."""
        input_data = AddTaskInput(
            card_id="card123",
            task_name="Test Task",
            task_list_name="My Checklist"
        )

        assert input_data.task_list_name == "My Checklist"

    def test_missing_card_id(self):
        """Test missing required card_id."""
        with pytest.raises(ValidationError):
            AddTaskInput(task_name="Test Task")

    def test_missing_task_name(self):
        """Test missing required task_name."""
        with pytest.raises(ValidationError):
            AddTaskInput(card_id="card123")

    def test_task_name_too_long(self):
        """Test task_name exceeding max length."""
        with pytest.raises(ValidationError):
            AddTaskInput(card_id="card123", task_name="A" * 501)


class TestUpdateTaskInput:
    """Test UpdateTaskInput model."""

    def test_valid_input_complete(self):
        """Test marking task as complete."""
        input_data = UpdateTaskInput(task_id="task123", is_completed=True)

        assert input_data.task_id == "task123"
        assert input_data.is_completed is True

    def test_valid_input_incomplete(self):
        """Test marking task as incomplete."""
        input_data = UpdateTaskInput(task_id="task123", is_completed=False)

        assert input_data.task_id == "task123"
        assert input_data.is_completed is False

    def test_missing_task_id(self):
        """Test missing required task_id."""
        with pytest.raises(ValidationError):
            UpdateTaskInput(is_completed=True)

    def test_missing_is_completed(self):
        """Test missing required is_completed."""
        with pytest.raises(ValidationError):
            UpdateTaskInput(task_id="task123")


class TestFindAndGetCardInput:
    """Test FindAndGetCardInput model."""

    def test_valid_input_minimal(self):
        """Test valid input with minimal fields."""
        input_data = FindAndGetCardInput(query="login bug")

        assert input_data.query == "login bug"
        assert input_data.board_id is None
        assert input_data.response_format == ResponseFormat.MARKDOWN

    def test_valid_input_with_board(self):
        """Test valid input with board filter."""
        input_data = FindAndGetCardInput(
            query="authentication",
            board_id="board123",
            response_format=ResponseFormat.JSON
        )

        assert input_data.query == "authentication"
        assert input_data.board_id == "board123"
        assert input_data.response_format == ResponseFormat.JSON

    def test_missing_query(self):
        """Test missing required query."""
        with pytest.raises(ValidationError):
            FindAndGetCardInput()

    def test_query_too_long(self):
        """Test query exceeding max length."""
        with pytest.raises(ValidationError):
            FindAndGetCardInput(query="A" * 201)


class TestAddCardLabelInput:
    """Test AddCardLabelInput model."""

    def test_valid_input(self):
        """Test valid input."""
        input_data = AddCardLabelInput(
            card_id="card123",
            label_id="label456"
        )

        assert input_data.card_id == "card123"
        assert input_data.label_id == "label456"

    def test_missing_card_id(self):
        """Test missing required card_id."""
        with pytest.raises(ValidationError):
            AddCardLabelInput(label_id="label456")

    def test_missing_label_id(self):
        """Test missing required label_id."""
        with pytest.raises(ValidationError):
            AddCardLabelInput(card_id="card123")

    def test_empty_card_id(self):
        """Test empty card_id."""
        with pytest.raises(ValidationError):
            AddCardLabelInput(card_id="", label_id="label456")

    def test_empty_label_id(self):
        """Test empty label_id."""
        with pytest.raises(ValidationError):
            AddCardLabelInput(card_id="card123", label_id="")

    def test_card_id_too_long(self):
        """Test card_id exceeding max length."""
        with pytest.raises(ValidationError):
            AddCardLabelInput(card_id="A" * 101, label_id="label456")

    def test_label_id_too_long(self):
        """Test label_id exceeding max length."""
        with pytest.raises(ValidationError):
            AddCardLabelInput(card_id="card123", label_id="A" * 101)


class TestRemoveCardLabelInput:
    """Test RemoveCardLabelInput model."""

    def test_valid_input(self):
        """Test valid input."""
        input_data = RemoveCardLabelInput(
            card_id="card123",
            label_id="label456"
        )

        assert input_data.card_id == "card123"
        assert input_data.label_id == "label456"

    def test_missing_card_id(self):
        """Test missing required card_id."""
        with pytest.raises(ValidationError):
            RemoveCardLabelInput(label_id="label456")

    def test_missing_label_id(self):
        """Test missing required label_id."""
        with pytest.raises(ValidationError):
            RemoveCardLabelInput(card_id="card123")

    def test_empty_card_id(self):
        """Test empty card_id."""
        with pytest.raises(ValidationError):
            RemoveCardLabelInput(card_id="", label_id="label456")

    def test_empty_label_id(self):
        """Test empty label_id."""
        with pytest.raises(ValidationError):
            RemoveCardLabelInput(card_id="card123", label_id="")

    def test_card_id_too_long(self):
        """Test card_id exceeding max length."""
        with pytest.raises(ValidationError):
            RemoveCardLabelInput(card_id="A" * 101, label_id="label456")

    def test_label_id_too_long(self):
        """Test label_id exceeding max length."""
        with pytest.raises(ValidationError):
            RemoveCardLabelInput(card_id="card123", label_id="A" * 101)


class TestEnums:
    """Test enum values."""

    def test_response_format_values(self):
        """Test ResponseFormat enum values."""
        assert ResponseFormat.MARKDOWN.value == "markdown"
        assert ResponseFormat.JSON.value == "json"

    def test_detail_level_values(self):
        """Test DetailLevel enum values."""
        assert DetailLevel.PREVIEW.value == "preview"
        assert DetailLevel.SUMMARY.value == "summary"
        assert DetailLevel.DETAILED.value == "detailed"

    def test_response_context_values(self):
        """Test ResponseContext enum values."""
        assert ResponseContext.MINIMAL.value == "minimal"
        assert ResponseContext.STANDARD.value == "standard"
        assert ResponseContext.FULL.value == "full"
