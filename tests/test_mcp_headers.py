"""Tests for downstream MCP server header resolution."""

from __future__ import annotations

from pydantic import SecretStr

from sub_agent_mcp.config.schema import AgentConfig, LLMConfig, MCPServerConfig
from sub_agent_mcp.mcp_client.headers import resolve_mcp_server_headers
from sub_agent_mcp.mcp_client.manager import build_client_config


def test_resolve_mcp_server_headers_bearer_token() -> None:
    server = MCPServerConfig(
        name="api",
        transport="streamable_http",
        url="https://mcp.example.com/mcp",
        bearer_token=SecretStr("secret-token"),
    )

    headers = resolve_mcp_server_headers(server)

    assert headers == {"Authorization": "Bearer secret-token"}


def test_resolve_mcp_server_headers_merges_custom_headers() -> None:
    server = MCPServerConfig(
        name="api",
        transport="streamable_http",
        url="https://mcp.example.com/mcp",
        bearer_token=SecretStr("secret-token"),
        headers={"X-Custom": "value"},
    )

    headers = resolve_mcp_server_headers(server)

    assert headers == {
        "Authorization": "Bearer secret-token",
        "X-Custom": "value",
    }


def test_resolve_mcp_server_headers_without_bearer_token() -> None:
    server = MCPServerConfig(
        name="api",
        transport="streamable_http",
        url="https://mcp.example.com/mcp",
    )

    assert resolve_mcp_server_headers(server) is None


def test_resolve_mcp_server_headers_empty_bearer_token() -> None:
    server = MCPServerConfig(
        name="api",
        transport="streamable_http",
        url="https://mcp.example.com/mcp",
        bearer_token=SecretStr(""),
    )

    assert resolve_mcp_server_headers(server) is None


def test_build_client_config_omits_headers_without_bearer_token() -> None:
    agent = AgentConfig(
        id="researcher",
        title="Research Agent",
        description="Test agent",
        llm=LLMConfig(
            base_uri="https://api.openai.com/v1",
            api_key=SecretStr("llm-key"),
            model_id="gpt-4.1-mini",
        ),
        system_prompt="You are helpful.",
        mcp_servers=[
            MCPServerConfig(
                name="api",
                transport="streamable_http",
                url="https://mcp.example.com/mcp",
            )
        ],
    )

    config = build_client_config(agent)

    assert "headers" not in config["api"]


def test_build_client_config_includes_bearer_token() -> None:
    agent = AgentConfig(
        id="researcher",
        title="Research Agent",
        description="Test agent",
        llm=LLMConfig(
            base_uri="https://api.openai.com/v1",
            api_key=SecretStr("llm-key"),
            model_id="gpt-4.1-mini",
        ),
        system_prompt="You are helpful.",
        mcp_servers=[
            MCPServerConfig(
                name="api",
                transport="streamable_http",
                url="https://mcp.example.com/mcp",
                bearer_token=SecretStr("mcp-token"),
            )
        ],
    )

    config = build_client_config(agent)

    assert config["api"]["headers"] == {"Authorization": "Bearer mcp-token"}
