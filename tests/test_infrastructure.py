"""Tests for core infrastructure: API client, caching, error handling, formatters."""

import pytest
import time
from unittest.mock import AsyncMock, Mock, patch
import httpx


# Import infrastructure components
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from planka_mcp import (
    PlankaAPIClient,
    PlankaCache,
    CacheEntry,
    ResponseFormatter,
    PaginationHelper,
    handle_api_error,
    DetailLevel
)


class TestPlankaAPIClient:
    """Test PlankaAPIClient functionality."""

    @pytest.mark.asyncio
    async def test_api_client_initialization(self):
        """Test API client initializes correctly."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")

        assert client.base_url == "https://test.planka.com"
        assert client.auth_token == "test-token"
        assert client._client is None

    @pytest.mark.asyncio
    async def test_get_client_creates_httpx_client(self):
        """Test that get_client creates httpx.AsyncClient."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")

        http_client = await client.get_client()

        assert isinstance(http_client, httpx.AsyncClient)
        assert client._client is not None

    @pytest.mark.asyncio
    async def test_get_request(self):
        """Test GET request helper."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")

        with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"test": "data"}

            result = await client.get("projects")

            mock_request.assert_called_once_with("GET", "projects", params=None)
            assert result == {"test": "data"}

    @pytest.mark.asyncio
    async def test_post_request(self):
        """Test POST request helper."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")

        with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"item": {"id": "card1"}}

            result = await client.post("cards", {"name": "Test Card"})

            mock_request.assert_called_once_with("POST", "cards", json_data={"name": "Test Card"})
            assert result == {"item": {"id": "card1"}}

    @pytest.mark.asyncio
    async def test_api_client_close(self):
        """Test API client cleanup."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")
        client._client = AsyncMock()

        await client.close()

        client._client.aclose.assert_called_once()


class TestPlankaCache:
    """Test PlankaCache functionality."""

    def test_cache_initialization(self):
        """Test cache initializes correctly."""
        cache = PlankaCache()

        assert cache.workspace is None
        assert cache.board_overviews == {}
        assert cache.card_details == {}
        assert cache.stats["workspace_hits"] == 0

    @pytest.mark.asyncio
    async def test_workspace_cache_miss(self):
        """Test workspace cache miss."""
        cache = PlankaCache()

        async def fetch_func():
            return {"projects": []}

        result = await cache.get_workspace(fetch_func)

        assert result == {"projects": []}
        assert cache.stats["workspace_misses"] == 1
        assert cache.stats["workspace_hits"] == 0
        assert cache.workspace is not None

    @pytest.mark.asyncio
    async def test_workspace_cache_hit(self):
        """Test workspace cache hit."""
        cache = PlankaCache()

        async def fetch_func():
            return {"projects": []}

        # First call - cache miss
        await cache.get_workspace(fetch_func)

        # Second call - cache hit
        result = await cache.get_workspace(fetch_func)

        assert result == {"projects": []}
        assert cache.stats["workspace_hits"] == 1
        assert cache.stats["workspace_misses"] == 1

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache entry expiration."""
        cache = PlankaCache()
        call_count = 0

        async def fetch_func():
            nonlocal call_count
            call_count += 1
            return {"projects": [], "call": call_count}

        # First call
        result1 = await cache.get_workspace(fetch_func)
        assert result1["call"] == 1

        # Manually expire the cache
        cache.workspace.timestamp = time.time() - 400  # 400 seconds ago (> 300 TTL)

        # Second call - should fetch again
        result2 = await cache.get_workspace(fetch_func)
        assert result2["call"] == 2

    def test_cache_invalidation(self):
        """Test cache invalidation methods."""
        cache = PlankaCache()

        # Set up cache entries
        cache.workspace = CacheEntry({"test": "data"}, time.time(), 300)
        cache.board_overviews["board1"] = CacheEntry({"board": "data"}, time.time(), 180)
        cache.card_details["card1"] = CacheEntry({"card": "data"}, time.time(), 60)

        # Test invalidation
        cache.invalidate_workspace()
        assert cache.workspace is None

        cache.invalidate_board("board1")
        assert "board1" not in cache.board_overviews

        cache.invalidate_card("card1")
        assert "card1" not in cache.card_details

    def test_cache_cleanup(self):
        """Test cache cleanup when max size exceeded."""
        cache = PlankaCache()

        # Add 110 cards (exceeds max of 100)
        for i in range(110):
            cache.card_details[f"card{i}"] = CacheEntry(
                {"id": f"card{i}"},
                time.time() - i,  # Older cards have earlier timestamps
                60
            )

        cache.cleanup_card_cache()

        # Should keep only 50 most recent
        assert len(cache.card_details) == 50


class TestCacheEntry:
    """Test CacheEntry functionality."""

    def test_cache_entry_is_valid(self):
        """Test cache entry validity check."""
        entry = CacheEntry({"test": "data"}, time.time(), 300)

        assert entry.is_valid() is True

        # Expired entry
        old_entry = CacheEntry({"test": "data"}, time.time() - 400, 300)
        assert old_entry.is_valid() is False


class TestResponseFormatter:
    """Test ResponseFormatter functionality."""

    def test_truncate_response_no_truncation(self):
        """Test that short responses are not truncated."""
        content = "Short content"
        result = ResponseFormatter.truncate_response(content, limit=1000)

        assert result == content

    def test_truncate_response_with_truncation(self):
        """Test that long responses are truncated."""
        content = "A" * 30000
        result = ResponseFormatter.truncate_response(content, limit=25000)

        assert len(result) < 25000
        assert "RESPONSE TRUNCATED" in result

    def test_format_task_progress_no_tasks(self):
        """Test task progress formatting with no tasks."""
        result = ResponseFormatter.format_task_progress([])

        assert result == "0/0"

    def test_format_task_progress_with_tasks(self):
        """Test task progress formatting with tasks."""
        task_lists = [
            {
                "id": "tl1",
                "tasks": [
                    {"id": "t1", "name": "Task 1", "isCompleted": True},
                    {"id": "t2", "name": "Task 2", "isCompleted": False},
                    {"id": "t3", "name": "Task 3", "isCompleted": True}
                ]
            }
        ]

        result = ResponseFormatter.format_task_progress(task_lists)

        assert result == "2/3"

    def test_format_card_preview(self, sample_card_data, sample_workspace_data):
        """Test card preview formatting."""
        context = {
            'lists': sample_workspace_data['lists'],
            'labels': sample_workspace_data['labels'],
            'users': sample_workspace_data['users']
        }

        result = ResponseFormatter.format_card_preview(sample_card_data, context)

        assert "Test Card" in result
        assert "card1" in result
        assert "1/2" in result  # Task progress

    def test_format_card_summary(self, sample_card_data, sample_workspace_data):
        """Test card summary formatting."""
        context = {
            'lists': sample_workspace_data['lists'],
            'labels': sample_workspace_data['labels'],
            'users': sample_workspace_data['users']
        }

        result = ResponseFormatter.format_card_summary(sample_card_data, context)

        assert "Test Card" in result
        assert "This is a test card" in result or "..." in result
        assert "Test User" in result

    def test_format_card_detailed(self, sample_card_data, sample_workspace_data):
        """Test card detailed formatting."""
        context = {
            'lists': sample_workspace_data['lists'],
            'labels': sample_workspace_data['labels'],
            'users': sample_workspace_data['users'],
            'board_name': 'Test Board'
        }

        result = ResponseFormatter.format_card_detailed(sample_card_data, context)

        assert "# Test Card" in result
        assert "## Tasks" in result
        assert "[x] Task 1" in result
        assert "[ ] Task 2" in result
        assert "## Comments" in result
        assert "Test comment" in result


class TestPaginationHelper:
    """Test PaginationHelper functionality."""

    def test_paginate_results_first_page(self):
        """Test pagination first page."""
        items = [{"id": f"item{i}"} for i in range(100)]

        result = PaginationHelper.paginate_results(items, offset=0, limit=20)

        assert len(result["items"]) == 20
        assert result["offset"] == 0
        assert result["limit"] == 20
        assert result["count"] == 20
        assert result["total"] == 100
        assert result["has_more"] is True
        assert result["next_offset"] == 20

    def test_paginate_results_last_page(self):
        """Test pagination last page."""
        items = [{"id": f"item{i}"} for i in range(100)]

        result = PaginationHelper.paginate_results(items, offset=90, limit=20)

        assert len(result["items"]) == 10
        assert result["has_more"] is False
        assert result["next_offset"] is None

    def test_paginate_results_empty(self):
        """Test pagination with no items."""
        result = PaginationHelper.paginate_results([], offset=0, limit=20)

        assert len(result["items"]) == 0
        assert result["total"] == 0
        assert result["has_more"] is False


class TestErrorHandling:
    """Test error handling functionality."""

    def test_handle_api_error_401(self):
        """Test 401 authentication error handling."""
        response = Mock()
        response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=response)

        result = handle_api_error(error)

        assert "Invalid API credentials" in result
        assert ".env" in result

    def test_handle_api_error_404(self):
        """Test 404 not found error handling."""
        response = Mock()
        response.status_code = 404
        error = httpx.HTTPStatusError("Not Found", request=Mock(), response=response)

        result = handle_api_error(error)

        assert "Resource not found" in result

    def test_handle_api_error_429(self):
        """Test 429 rate limit error handling."""
        response = Mock()
        response.status_code = 429
        error = httpx.HTTPStatusError("Too Many Requests", request=Mock(), response=response)

        result = handle_api_error(error)

        assert "Rate limit exceeded" in result

    def test_handle_api_error_timeout(self):
        """Test timeout error handling."""
        error = httpx.TimeoutException("Request timed out")

        result = handle_api_error(error)

        assert "timed out" in result

    def test_handle_api_error_connection(self):
        """Test connection error handling."""
        error = httpx.ConnectError("Connection failed")

        result = handle_api_error(error)

        assert "Cannot connect" in result
        assert "PLANKA_BASE_URL" in result

    def test_handle_api_error_generic(self):
        """Test generic error handling."""
        error = Exception("Something went wrong")

        result = handle_api_error(error)

        assert "Unexpected error" in result
        assert "Exception" in result
