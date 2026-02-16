# Registry Tools MCP Server

[![mpak](https://img.shields.io/badge/mpak-registry-blue)](https://mpak.dev/packages/@nimblebraininc/registry-tools)
[![NimbleBrain](https://img.shields.io/badge/NimbleBrain-nimblebrain.ai-purple)](https://nimblebrain.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Search and resolve MCP server packages on the [mpak registry](https://mpak.dev). This server lets agents discover available MCP servers, inspect their tools, and check credential requirements before installation.

This is one of the core MCP servers that powers [NimbleBrain](https://nimblebrain.ai)'s agent runtime, giving agents self-service access to the registry. It's open source so you can see how it works, fork it to connect to your own registry, or use it as a reference for building discovery-layer MCP servers.

## Install

```bash
mpak install @nimblebraininc/registry-tools
```

<details>
<summary>Claude Code</summary>

```bash
claude mcp add registry-tools -- mpak run @nimblebraininc/registry-tools
```
</details>

<details>
<summary>Claude Desktop</summary>

```json
{
  "mcpServers": {
    "registry-tools": {
      "command": "mpak",
      "args": ["run", "@nimblebraininc/registry-tools"]
    }
  }
}
```
</details>

## Tools

### registry_search

Search the mpak registry for available MCP servers.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | `string` | Yes | Search term (e.g., "weather", "pdf", "finance") |

Returns matching packages with name, description, tools, download count, and verification status.

### registry_resolve

Get full metadata for a specific package, including credential requirements and version history.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `package` | `string` | Yes | Package identifier (e.g., "@nimblebraininc/finnhub") |
| `version` | `string` | No | Specific version (omit for latest) |

Returns detailed package info including tools, required credentials, license, and homepage.

## Configuration

| Env Var | Required | Description |
|---------|----------|-------------|
| `REGISTRY_URL` | No | mpak registry URL (default: `https://registry.mpak.dev`) |

## Extending

Want to adapt this for your own infrastructure?

- Point `REGISTRY_URL` at your own registry endpoint
- Add a `registry_browse` tool that lists categories or popular servers
- Add tools that combine search with automatic installation via your orchestrator
- Fork and modify `src/mcp_registry_tools/server.py`

## Development

```bash
git clone https://github.com/NimbleBrainInc/mcp-registry-tools.git
cd mcp-registry-tools

# Install dependencies
uv sync --group dev

# Run all checks (format, lint, typecheck, tests)
make check

# Run the server locally (stdio)
uv run python -m mcp_registry_tools.server

# Run the server locally (HTTP)
make run-http
```

## License

MIT
