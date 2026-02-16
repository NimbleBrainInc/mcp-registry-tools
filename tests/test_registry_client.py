"""Tests for RegistrySearchClient.

Verifies search, resolve, field stripping, error propagation,
and URL normalisation using httpx.MockTransport.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from mcp_registry_tools.registry_client import RegistrySearchClient

_OriginalAsyncClient = httpx.AsyncClient


def _mock_transport(handler):
    """Create an AsyncClient factory that routes through a mock handler."""
    transport = httpx.MockTransport(handler)

    def factory(**kwargs):
        kwargs.pop("timeout", None)
        return _OriginalAsyncClient(transport=transport, **kwargs)

    return factory


@pytest.mark.asyncio
async def test_search_returns_results():
    """Search returns formatted results from registry API."""

    async def handler(request: httpx.Request) -> httpx.Response:
        assert "/v1/bundles/search" in str(request.url)
        return httpx.Response(
            200,
            json={
                "bundles": [
                    {
                        "name": "@nimblebraininc/echo",
                        "display_name": "Echo",
                        "description": "Echo server",
                        "latest_version": "0.1.0",
                        "server_type": "python",
                        "tools": [{"name": "echo", "description": "Echo text"}],
                        "downloads": 42,
                        "verified": True,
                        "certification_level": None,
                    }
                ]
            },
        )

    with patch("mcp_registry_tools.registry_client.httpx.AsyncClient", _mock_transport(handler)):
        client = RegistrySearchClient()
        results = await client.search("echo")
        assert len(results) == 1
        assert results[0]["name"] == "@nimblebraininc/echo"
        assert results[0]["downloads"] == 42
        assert results[0]["tools"][0]["name"] == "echo"


@pytest.mark.asyncio
async def test_search_empty_results():
    """Search with no matches returns an empty list."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"bundles": []})

    with patch("mcp_registry_tools.registry_client.httpx.AsyncClient", _mock_transport(handler)):
        client = RegistrySearchClient()
        results = await client.search("nonexistent")
        assert results == []


@pytest.mark.asyncio
async def test_search_strips_extra_fields():
    """Search only returns expected fields, ignoring extras from API."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "bundles": [
                    {
                        "name": "@nimblebraininc/echo",
                        "description": "Echo",
                        "latest_version": "0.1.0",
                        "tools": [],
                        "extra_field": "should be ignored",
                        "internal_id": 999,
                    }
                ]
            },
        )

    with patch("mcp_registry_tools.registry_client.httpx.AsyncClient", _mock_transport(handler)):
        client = RegistrySearchClient()
        results = await client.search("echo")
        assert len(results) == 1
        assert "extra_field" not in results[0]
        assert "internal_id" not in results[0]


@pytest.mark.asyncio
async def test_search_http_error():
    """Search propagates HTTP errors."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    with patch("mcp_registry_tools.registry_client.httpx.AsyncClient", _mock_transport(handler)):
        client = RegistrySearchClient()
        with pytest.raises(httpx.HTTPStatusError):
            await client.search("anything")


@pytest.mark.asyncio
async def test_resolve_with_credentials():
    """Resolve returns credential requirements from version manifest."""
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        url = str(request.url)

        if "/versions/" in url:
            return httpx.Response(
                200,
                json={
                    "manifest": {
                        "environmentVariables": [
                            {
                                "name": "API_KEY",
                                "description": "Service API key",
                                "isSecret": True,
                                "isRequired": True,
                            },
                            {
                                "name": "LOG_LEVEL",
                                "description": "Optional log level",
                                "isSecret": False,
                                "isRequired": False,
                            },
                        ]
                    }
                },
            )

        return httpx.Response(
            200,
            json={
                "name": "@nimblebraininc/finnhub",
                "description": "Financial data",
                "latest_version": "0.2.0",
                "tools": [{"name": "get_quote", "description": "Get quote"}],
                "verified": True,
            },
        )

    with patch("mcp_registry_tools.registry_client.httpx.AsyncClient", _mock_transport(handler)):
        client = RegistrySearchClient()
        result = await client.resolve("@nimblebraininc/finnhub")
        assert result["credential_type"] == "api_key"
        assert len(result["credentials_required"]) == 1
        assert result["credentials_required"][0]["name"] == "API_KEY"
        assert result["version"] == "0.2.0"


@pytest.mark.asyncio
async def test_resolve_without_credentials():
    """Resolve returns 'none' credential_type when no secrets required."""

    async def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/versions/" in url:
            return httpx.Response(200, json={"manifest": {"environmentVariables": []}})
        return httpx.Response(
            200,
            json={
                "name": "@nimblebraininc/echo",
                "description": "Echo",
                "latest_version": "0.1.0",
                "tools": [],
            },
        )

    with patch("mcp_registry_tools.registry_client.httpx.AsyncClient", _mock_transport(handler)):
        client = RegistrySearchClient()
        result = await client.resolve("@nimblebraininc/echo")
        assert result["credential_type"] == "none"
        assert result["credentials_required"] == []


@pytest.mark.asyncio
async def test_resolve_explicit_version():
    """Resolve with explicit version uses that version instead of latest."""

    async def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/versions/0.1.0" in url:
            return httpx.Response(200, json={"manifest": {"environmentVariables": []}})
        return httpx.Response(
            200,
            json={
                "name": "@nimblebraininc/echo",
                "description": "Echo",
                "latest_version": "0.2.0",
                "tools": [],
            },
        )

    with patch("mcp_registry_tools.registry_client.httpx.AsyncClient", _mock_transport(handler)):
        client = RegistrySearchClient()
        result = await client.resolve("@nimblebraininc/echo", version="0.1.0")
        assert result["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_url_trailing_slash_stripped():
    """Client strips trailing slash from registry URL."""
    client = RegistrySearchClient(registry_url="https://registry.mpak.dev/")
    assert client._registry_url == "https://registry.mpak.dev"
