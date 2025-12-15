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

@pytest.mark.asyncio
async def test_initialize_auth_with_api_key():
    """Test that initialize_auth returns the API key when token is not available."""
    with patch('os.getenv') as mock_getenv:
        # Mock getenv to return None for token, then API key
        def getenv_side_effect(key):
            if key == "PLANKA_API_TOKEN":
                return None
            elif key == "PLANKA_API_KEY":
                return "test-api-key"
            elif key == "PLANKA_BASE_URL":
                return "https://test.planka.com"
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        token = await initialize_auth()
        assert token == "test-api-key"

@pytest.mark.asyncio
async def test_initialize_auth_with_email_password():
    """Test that initialize_auth authenticates with email/password when no token or API key is available."""
    with patch('os.getenv') as mock_getenv, \
         patch('httpx.AsyncClient') as mock_async_client:
        
        # Mock getenv to return None for token and API key, but email/password
        def getenv_side_effect(key):
            if key == "PLANKA_API_TOKEN":
                return None
            elif key == "PLANKA_API_KEY":
                return None
            elif key == "PLANKA_EMAIL":
                return "test@example.com"
            elif key == "PLANKA_PASSWORD":
                return "password123"
            elif key == "PLANKA_BASE_URL":
                return "https://test.planka.com"
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "item": {
                "accessToken": "generated-token"
            }
        }
        
        instance = mock_async_client.return_value
        instance.post = AsyncMock(return_value=mock_response)
        
        # Use __aenter__ and __aexit__ for async context manager
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        
        token = await initialize_auth()
        assert token == "generated-token"

@pytest.mark.asyncio
async def test_initialize_auth_no_credentials():
    """Test that initialize_auth raises ValueError when no authentication method is configured."""
    with patch('os.getenv') as mock_getenv:
        # Mock getenv to return None for all authentication methods
        def getenv_side_effect(key):
            if key == "PLANKA_BASE_URL":
                return "https://test.planka.com"
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        
        with pytest.raises(ValueError, match="No authentication method configured"):
            await initialize_auth()

@pytest.mark.asyncio
async def test_initialize_auth_missing_base_url():
    """Test that initialize_auth raises ValueError when PLANKA_BASE_URL is not set."""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.return_value = None
        
        with pytest.raises(ValueError, match="PLANKA_BASE_URL not set"):
            await initialize_auth()

class TestAPIClientMethods:
    """Test individual HTTP method helpers."""
    
    @pytest.mark.asyncio
    async def test_get_method(self):
        """Test the GET method helper."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {"data": "get-success"}
            
            result = await client.get("test-endpoint", params={"key": "value"})
            
            mock_request.assert_awaited_once_with("GET", "test-endpoint", params={"key": "value"})
            assert result == {"data": "get-success"}
    
    @pytest.mark.asyncio
    async def test_post_method(self):
        """Test the POST method helper."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {"data": "post-success"}
            
            result = await client.post("test-endpoint", json_data={"key": "value"})
            
            mock_request.assert_awaited_once_with("POST", "test-endpoint", json_data={"key": "value"})
            assert result == {"data": "post-success"}
    
    @pytest.mark.asyncio
    async def test_patch_method(self):
        """Test the PATCH method helper."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {"data": "patch-success"}
            
            result = await client.patch("test-endpoint", json_data={"key": "value"})
            
            mock_request.assert_awaited_once_with("PATCH", "test-endpoint", json_data={"key": "value"})
            assert result == {"data": "patch-success"}
    
    @pytest.mark.asyncio
    async def test_delete_method(self):
        """Test the DELETE method helper."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {"data": "delete-success"}
            
            result = await client.delete("test-endpoint")
            
            mock_request.assert_awaited_once_with("DELETE", "test-endpoint")
            assert result == {"data": "delete-success"}
    
    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test the close method."""
        client = PlankaAPIClient("https://test.planka.com", "test-token")
        
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_client_instance = MagicMock()
            mock_client_instance.aclose = AsyncMock()
            mock_async_client.return_value = mock_client_instance
            
            # Create client to initialize the _client
            await client.get_client()
            
            # Now close it
            await client.close()
            
            mock_client_instance.aclose.assert_awaited_once()
