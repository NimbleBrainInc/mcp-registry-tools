"""HTTP client for searching the mpak registry.

Read-only async client for searching and resolving packages from
registry.mpak.dev. Self-contained (httpx only, no agent imports).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_URL = "https://registry.mpak.dev"
DEFAULT_TIMEOUT = 15.0


class RegistrySearchClient:
    """Async HTTP client for mpak registry search and resolution."""

    def __init__(
        self,
        registry_url: str = DEFAULT_REGISTRY_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._registry_url = registry_url.rstrip("/")
        self._timeout = timeout

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search the registry for bundles matching a query."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._registry_url}/v1/bundles/search",
                params={"q": query, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

        bundles = data.get("bundles", [])
        return [
            {
                "name": b.get("name", ""),
                "display_name": b.get("display_name"),
                "description": b.get("description", ""),
                "latest_version": b.get("latest_version", ""),
                "server_type": b.get("server_type"),
                "tools": [
                    {"name": t["name"], "description": t.get("description", "")}
                    for t in b.get("tools", [])
                ],
                "downloads": b.get("downloads", 0),
                "verified": b.get("verified", False),
                "certification_level": b.get("certification_level"),
            }
            for b in bundles
        ]

    async def resolve(self, package: str, version: str | None = None) -> dict[str, Any]:
        """Resolve full package metadata from the registry."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._registry_url}/v1/bundles/{package}",
            )
            response.raise_for_status()
            bundle = response.json()

        resolved_version = version or bundle.get("latest_version", "")

        env_vars: list[dict[str, Any]] = []
        if resolved_version:
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    ver_response = await client.get(
                        f"{self._registry_url}/v1/bundles/{package}/versions/{resolved_version}",
                    )
                    ver_response.raise_for_status()
                    ver_data = ver_response.json()

                manifest = ver_data.get("manifest", {})
                for pkg in manifest.get("packages", [manifest]):
                    for ev in pkg.get("environmentVariables", []):
                        env_vars.append(ev)
            except httpx.HTTPStatusError:
                logger.warning(
                    "Failed to fetch version detail for %s@%s", package, resolved_version
                )

        required_secrets = [ev for ev in env_vars if ev.get("isSecret") and ev.get("isRequired")]
        credential_type = "api_key" if required_secrets else "none"

        return {
            "name": bundle.get("name", package),
            "display_name": bundle.get("display_name"),
            "description": bundle.get("description", ""),
            "version": resolved_version,
            "tools": [
                {"name": t["name"], "description": t.get("description", "")}
                for t in bundle.get("tools", [])
            ],
            "credential_type": credential_type,
            "credentials_required": [
                {
                    "name": ev["name"],
                    "description": ev.get("description", ""),
                }
                for ev in required_secrets
            ],
            "homepage": bundle.get("homepage"),
            "license": bundle.get("license"),
            "verified": bundle.get("verified", False),
        }
