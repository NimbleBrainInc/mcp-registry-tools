"""Tests for the registry-tools MCP server.

Uses FastMCP test client with mocked HTTP backends.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from mcp_registry_tools.server import mcp


@pytest.fixture(autouse=True)
def reset_clients():
    """Reset lazy-initialized clients between tests."""
    import mcp_registry_tools.server as srv

    srv._registry_client = None


@pytest.fixture
def mcp_server():
    """Return the MCP server instance."""
    return mcp


@pytest.mark.asyncio
async def test_tools_list(mcp_server):
    """Test that both tools are registered."""
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]
        assert "registry_search" in tool_names
        assert "registry_resolve" in tool_names
        assert len(tool_names) == 2


@pytest.mark.asyncio
async def test_registry_search(mcp_server):
    """Test registry search with mocked client."""
    mock_results = [
        {
            "name": "@nimblebraininc/finnhub",
            "display_name": "Finnhub",
            "description": "Financial data",
            "latest_version": "0.1.0",
            "server_type": "python",
            "tools": [{"name": "get_quote", "description": "Get stock quote"}],
            "downloads": 100,
            "verified": True,
            "certification_level": None,
        }
    ]

    mock_search = AsyncMock(return_value=mock_results)
    with patch("mcp_registry_tools.server._get_registry_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.search = mock_search
        mock_get.return_value = mock_client

        async with Client(mcp_server) as client:
            result = await client.call_tool("registry_search", {"query": "finance"})
            result_str = str(result)
            assert "finnhub" in result_str


@pytest.mark.asyncio
async def test_registry_resolve(mcp_server):
    """Test registry resolve with mocked client."""
    mock_result = {
        "name": "@nimblebraininc/finnhub",
        "display_name": "Finnhub",
        "description": "Financial data",
        "version": "0.1.0",
        "tools": [],
        "credential_type": "api_key",
        "credentials_required": [{"name": "FINNHUB_API_KEY", "description": "API key"}],
        "homepage": None,
        "license": "MIT",
        "verified": True,
    }

    with patch("mcp_registry_tools.server._get_registry_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.resolve = AsyncMock(return_value=mock_result)
        mock_get.return_value = mock_client

        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "registry_resolve",
                {"package": "@nimblebraininc/finnhub"},
            )
            result_str = str(result)
            assert "finnhub" in result_str
