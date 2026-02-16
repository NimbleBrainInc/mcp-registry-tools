# Registry Tools

## Tool Selection

| Intent | Tool |
|--------|------|
| Find available MCP servers | `registry_search(query)` |
| Get package details/requirements | `registry_resolve(package, version?)` |

## Multi-Step Workflows

### Find and inspect an MCP server
1. `registry_search(query)` to find matching servers
2. `registry_resolve(package)` to check credential requirements and available tools

## Key Patterns

- Always call `registry_resolve` after finding a package to see its full details and credential requirements.
- Search is fuzzy. Try different terms if the first search doesn't find what you need.
- Results include verification status and certification level to help assess trust.
