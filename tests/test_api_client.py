import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from planka_mcp.api_client import PlankaAPIClient, initialize_auth

class TestPlankaAPIClient:
    """Test PlankaAPIClient functionality."""

    @pytest.mark.asyncio
    async def test_request_success(self):
        """Test a successful API request."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")
        
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "success"}
            
            instance = mock_async_client.return_value
            instance.request = AsyncMock(return_value=mock_response)

            response = await client.request("GET", "test")
            assert response == {"data": "success"}

    @pytest.mark.asyncio
    async def test_request_http_error(self):
        """Test an API request that returns an HTTP error."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")
        
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.request = httpx.Request("GET", "https://test.planka.com/api/test")
            mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("Not Found", request=mock_response.request, response=mock_response))

            instance = mock_async_client.return_value
            instance.request = AsyncMock(return_value=mock_response)

            with pytest.raises(httpx.HTTPStatusError):
                await client.request("GET", "test")

@pytest.mark.asyncio
async def test_initialize_auth_with_token():
    """Test that initialize_auth returns the token from the environment."""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.return_value = "test-token"
        token = await initialize_auth()
        assert token == "test-token"
