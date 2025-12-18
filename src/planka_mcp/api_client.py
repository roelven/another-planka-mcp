import os
import sys
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# ==================== API CLIENT ====================

class PlankaAPIClient:
    """Centralized API client for all Planka requests."""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,  # DEFAULT_TIMEOUT
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                }
            )
        return self._client

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request with error handling."""
        client = await self.get_client()
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                files=files
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise e
        except Exception as e:
            raise e

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET request helper."""
        return await self.request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json_data: Dict) -> Dict:
        """POST request helper."""
        return await self.request("POST", endpoint, json_data=json_data)

    async def patch(self, endpoint: str, json_data: Dict) -> Dict:
        """PATCH request helper."""
        return await self.request("PATCH", endpoint, json_data=json_data)

    async def delete(self, endpoint: str) -> Dict:
        """DELETE request helper."""
        client = await self.get_client()
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"

        try:
            response = await client.request(
                "DELETE",
                url=url
            )
            response.raise_for_status()
            
            # DELETE operations may return empty responses (204 No Content)
            # Return empty dict for successful deletes with no content
            if response.status_code == 204:
                return {}
            
            return response.json()
        except httpx.HTTPStatusError as e:
            raise e
        except Exception as e:
            raise e

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()

# ==================== AUTHENTICATION ====================

async def initialize_auth() -> str:
    """Initialize authentication and return access token."""
    load_dotenv()

    base_url = os.getenv("PLANKA_BASE_URL")
    if not base_url:
        raise ValueError("PLANKA_BASE_URL not set in environment")

    # Option 1: Use existing access token
    token = os.getenv("PLANKA_API_TOKEN")
    if token:
        return token

    # Option 2: Use API key
    api_key = os.getenv("PLANKA_API_KEY")
    if api_key:
        return api_key

    # Option 3: Authenticate with email/password
    email = os.getenv("PLANKA_EMAIL")
    password = os.getenv("PLANKA_PASSWORD")
    if email and password:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/access-tokens",
                json={"emailOrUsername": email, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            return data["item"]["accessToken"]

    raise ValueError(
        "No authentication method configured. Set one of: "
        "PLANKA_API_TOKEN, PLANKA_API_KEY, or PLANKA_EMAIL+PLANKA_PASSWORD"
    )