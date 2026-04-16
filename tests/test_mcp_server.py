"""Tests for MCP server configuration: OAuth auth and transport modes."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import os
import sys
import importlib

# Add project root to path so we can import mcp_server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def reload_mcp_server():
    """Reload mcp_server module to pick up env changes."""
    import mcp_server
    return importlib.reload(mcp_server)


class TestServerTransportConfig:
    """Test that the server configures transport and auth correctly."""

    def test_stdio_transport_no_auth(self):
        """In stdio mode, FastMCP should be created without auth."""
        env = {
            "MCP_TRANSPORT": "stdio",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            mcp_server = reload_mcp_server()
            assert mcp_server.transport == "stdio"
            assert mcp_server.auth_provider is None

    def test_default_transport_is_stdio(self):
        """When MCP_TRANSPORT is not set, default to stdio with no auth."""
        env = {
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("MCP_TRANSPORT", None)
            mcp_server = reload_mcp_server()
            assert mcp_server.transport == "stdio"
            assert mcp_server.auth_provider is None

    def test_http_transport_with_auth(self):
        """In streamable-http mode with MCP_SERVER_URL, auth provider should be set."""
        env = {
            "MCP_TRANSPORT": "streamable-http",
            "MCP_SERVER_URL": "https://planka-mcp.example.com",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            mcp_server = reload_mcp_server()
            assert mcp_server.transport == "streamable-http"
            assert mcp_server.auth_provider is not None

    def test_http_transport_without_server_url_no_auth(self):
        """In streamable-http mode without MCP_SERVER_URL, auth provider should be None."""
        env = {
            "MCP_TRANSPORT": "streamable-http",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("MCP_SERVER_URL", None)
            mcp_server = reload_mcp_server()
            assert mcp_server.transport == "streamable-http"
            assert mcp_server.auth_provider is None


class TestOAuthProviderConfig:
    """Test OAuth provider configuration details."""

    def test_oauth_provider_has_correct_scopes(self):
        """OAuth provider should require 'planka' scope."""
        env = {
            "MCP_TRANSPORT": "streamable-http",
            "MCP_SERVER_URL": "https://planka-mcp.example.com",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            mcp_server = reload_mcp_server()
            provider = mcp_server.auth_provider
            assert provider is not None
            assert provider.required_scopes == ["planka"]

    def test_oauth_provider_has_dcr_disabled(self):
        """OAuth provider should have DCR disabled (client is pre-registered)."""
        env = {
            "MCP_TRANSPORT": "streamable-http",
            "MCP_SERVER_URL": "https://planka-mcp.example.com",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            mcp_server = reload_mcp_server()
            provider = mcp_server.auth_provider
            assert provider is not None
            assert provider.client_registration_options is not None
            assert provider.client_registration_options.enabled is False


class TestFastMCPInstance:
    """Test that the FastMCP instance is configured correctly."""

    def test_mcp_instance_exists(self):
        """The mcp instance should always be created."""
        env = {
            "MCP_TRANSPORT": "stdio",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            mcp_server = reload_mcp_server()
            assert mcp_server.mcp is not None
            assert mcp_server.mcp.name == "planka_mcp"

    def test_mcp_tools_registered(self):
        """All expected tools should be registered on the mcp instance."""
        env = {
            "MCP_TRANSPORT": "stdio",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            mcp_server = reload_mcp_server()

            expected_tools = [
                "planka_get_workspace",
                "planka_list_cards",
                "planka_find_and_get_card",
                "planka_get_card",
                "planka_create_card",
                "planka_update_card",
                "planka_delete_card",
                "planka_add_task",
                "planka_update_task",
                "planka_delete_task",
                "planka_add_card_label",
                "planka_remove_card_label",
            ]
            registered = [t.name for t in mcp_server.mcp._tool_manager._tools.values()]
            for tool_name in expected_tools:
                assert tool_name in registered, f"Tool '{tool_name}' not registered"


class TestServerLifespan:
    """Test the server lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_registers_oauth_client(self):
        """Lifespan should pre-register the OAuth client when credentials are set."""
        env = {
            "MCP_TRANSPORT": "streamable-http",
            "MCP_SERVER_URL": "https://planka-mcp.example.com",
            "MCP_CLIENT_ID": "test-client-id",
            "MCP_CLIENT_SECRET": "test-client-secret",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            mcp_server = reload_mcp_server()

            with patch("mcp_server.initialize_auth", new_callable=AsyncMock, return_value="test-token"):
                with patch("mcp_server.PlankaAPIClient") as mock_client_cls:
                    mock_client = MagicMock()
                    mock_client.close = AsyncMock()
                    mock_client_cls.return_value = mock_client

                    async with mcp_server.server_lifespan(mcp_server.mcp):
                        client = await mcp_server.auth_provider.get_client("test-client-id")
                        assert client is not None
                        assert client.client_id == "test-client-id"
                        assert client.client_secret == "test-client-secret"
                        assert client.scope == "planka"

    @pytest.mark.asyncio
    async def test_lifespan_warns_without_credentials(self, capsys):
        """Lifespan should warn when OAuth is enabled but credentials are missing."""
        env = {
            "MCP_TRANSPORT": "streamable-http",
            "MCP_SERVER_URL": "https://planka-mcp.example.com",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("MCP_CLIENT_ID", None)
            os.environ.pop("MCP_CLIENT_SECRET", None)
            mcp_server = reload_mcp_server()

            with patch("mcp_server.initialize_auth", new_callable=AsyncMock, return_value="test-token"):
                with patch("mcp_server.PlankaAPIClient") as mock_client_cls:
                    mock_client = MagicMock()
                    mock_client.close = AsyncMock()
                    mock_client_cls.return_value = mock_client

                    async with mcp_server.server_lifespan(mcp_server.mcp):
                        pass

                    captured = capsys.readouterr()
                    assert "WARNING" in captured.err
                    assert "MCP_CLIENT_ID" in captured.err

    @pytest.mark.asyncio
    async def test_lifespan_initializes_instances(self):
        """Lifespan should initialize api_client and cache."""
        env = {
            "MCP_TRANSPORT": "stdio",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            mcp_server = reload_mcp_server()

            with patch("mcp_server.initialize_auth", new_callable=AsyncMock, return_value="test-token"):
                with patch("mcp_server.PlankaAPIClient") as mock_client_cls:
                    mock_client = MagicMock()
                    mock_client.close = AsyncMock()
                    mock_client_cls.return_value = mock_client

                    async with mcp_server.server_lifespan(mcp_server.mcp):
                        import planka_mcp.instances as instances
                        assert instances.api_client is mock_client
                        assert instances.cache is not None

    @pytest.mark.asyncio
    async def test_lifespan_cleans_up_on_exit(self):
        """Lifespan should close api_client on exit."""
        env = {
            "MCP_TRANSPORT": "stdio",
            "PLANKA_BASE_URL": "https://planka.example.com",
            "PLANKA_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            mcp_server = reload_mcp_server()

            with patch("mcp_server.initialize_auth", new_callable=AsyncMock, return_value="test-token"):
                with patch("mcp_server.PlankaAPIClient") as mock_client_cls:
                    mock_client = MagicMock()
                    mock_client.close = AsyncMock()
                    mock_client_cls.return_value = mock_client

                    async with mcp_server.server_lifespan(mcp_server.mcp):
                        pass

                    mock_client.close.assert_called_once()
