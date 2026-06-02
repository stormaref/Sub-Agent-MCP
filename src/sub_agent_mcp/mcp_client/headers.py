"""HTTP header resolution for downstream MCP server connections."""

from __future__ import annotations

from sub_agent_mcp.config.schema import MCPServerConfig


def resolve_mcp_server_headers(server: MCPServerConfig) -> dict[str, str] | None:
    """Build request headers for a downstream MCP server, or None when no auth is configured."""
    headers = dict(server.headers)
    if server.bearer_token is not None:
        token = server.bearer_token.get_secret_value()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers or None
