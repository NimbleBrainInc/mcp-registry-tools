"""Registry Tools MCP Server.

Search and resolve packages from the mpak MCP server registry.

Environment variables:
    REGISTRY_URL: mpak registry URL (default: https://registry.mpak.dev).
"""

import logging
import os
import sys
from importlib.resources import files
from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .registry_client import RegistrySearchClient

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_registry_tools")

mcp = FastMCP(
    "registry-tools",
    instructions=(
        "Before searching or resolving MCP servers, read the "
        "skill://registry-tools/usage resource for workflow guidance."
    ),
)

# ---------------------------------------------------------------------------
# Lazy client initialization
# ---------------------------------------------------------------------------

_registry_client: RegistrySearchClient | None = None


def _get_registry_client() -> RegistrySearchClient:
    """Lazily initialize the registry client."""
    global _registry_client
    if _registry_client is None:
        url = os.environ.get("REGISTRY_URL", "https://registry.mpak.dev")
        _registry_client = RegistrySearchClient(registry_url=url)
        logger.info("Initialized RegistrySearchClient at %s", url)
    return _registry_client


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "service": "mcp-registry-tools"})


# ---------------------------------------------------------------------------
# Registry tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def registry_search(query: str) -> dict[str, Any]:
    """Search the mpak registry for available MCP servers.

    Returns name, description, tools, version, and verification status.

    Args:
        query: Search term (e.g., 'weather', 'pdf', 'finance').

    Returns:
        Search results with count and query.
    """
    client = _get_registry_client()
    results = await client.search(query)

    return {
        "results": results,
        "count": len(results),
        "query": query,
    }


@mcp.tool()
async def registry_resolve(package: str, version: str | None = None) -> dict[str, Any]:
    """Get full metadata for a specific package from the mpak registry.

    Includes credential requirements and available tools.

    Args:
        package: Package identifier (e.g., '@nimblebraininc/finnhub').
        version: Specific version. Omit for latest.

    Returns:
        Package metadata dict.
    """
    client = _get_registry_client()
    return await client.resolve(package, version)


# ---------------------------------------------------------------------------
# SKILL.md resource
# ---------------------------------------------------------------------------

try:
    SKILL_CONTENT = files("mcp_registry_tools").joinpath("SKILL.md").read_text()
except FileNotFoundError:
    SKILL_CONTENT = "Registry tools for searching and resolving MCP server packages."


@mcp.resource("skill://registry-tools/usage")
def registry_tools_skill() -> str:
    """How to effectively use registry tools."""
    return SKILL_CONTENT


# ---------------------------------------------------------------------------
# Entrypoints
# ---------------------------------------------------------------------------

app = mcp.http_app()

if __name__ == "__main__":
    logger.info("Running in stdio mode")
    mcp.run()
