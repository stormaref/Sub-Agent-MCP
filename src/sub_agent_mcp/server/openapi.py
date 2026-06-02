"""OpenAPI document generation for the MCP HTTP surface."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools.base import Tool
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from sub_agent_mcp import __version__

OPENAPI_PATH = "/mcp/openapi.json"
MCP_TRANSPORT_PATH = "/mcp"
TOOLS_PATH_PREFIX = "/mcp/tools"


def _tool_request_schema(tool: Tool) -> dict[str, Any]:
    """Build request body schema for a tool operation."""
    properties = dict(tool.parameters.get("properties", {}))
    required = list(tool.parameters.get("required", []))
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _tool_response_schema(tool: Tool) -> dict[str, Any]:
    """Build response schema for a tool operation."""
    if tool.output_schema is not None:
        return tool.output_schema
    return {
        "type": "object",
        "description": "Tool result (unstructured)",
    }


def build_openapi_document(mcp: FastMCP) -> dict[str, Any]:
    """Generate an OpenAPI 3.1 document from registered FastMCP tools."""
    paths: dict[str, Any] = {
        MCP_TRANSPORT_PATH: {
            "post": {
                "operationId": "mcpStreamableHttp",
                "summary": "MCP Streamable HTTP transport",
                "description": (
                    "Primary MCP endpoint (JSON-RPC over Streamable HTTP). "
                    "Use an MCP client to call tools such as list_agents and spawn_agent."
                ),
                "tags": ["mcp"],
                "responses": {
                    "200": {"description": "MCP response"},
                    "406": {"description": "Not acceptable (wrong Accept header)"},
                },
            },
            "get": {
                "operationId": "mcpStreamableHttpSse",
                "summary": "MCP Streamable HTTP SSE stream",
                "tags": ["mcp"],
                "responses": {"200": {"description": "Server-sent events stream"}},
            },
            "delete": {
                "operationId": "mcpStreamableHttpTerminate",
                "summary": "Terminate MCP session",
                "tags": ["mcp"],
                "responses": {"200": {"description": "Session terminated"}},
            },
        },
        OPENAPI_PATH: {
            "get": {
                "operationId": "getOpenApi",
                "summary": "OpenAPI specification",
                "tags": ["meta"],
                "responses": {
                    "200": {
                        "description": "OpenAPI 3.1 document",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
    }

    for tool in mcp._tool_manager.list_tools():
        path = f"{TOOLS_PATH_PREFIX}/{tool.name}"
        paths[path] = {
            "post": {
                "operationId": tool.name,
                "summary": tool.title or tool.name,
                "description": tool.description,
                "tags": ["tools"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": _tool_request_schema(tool),
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Tool result",
                        "content": {
                            "application/json": {
                                "schema": _tool_response_schema(tool),
                            }
                        },
                    }
                },
            }
        }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": mcp.name,
            "version": __version__,
            "description": (
                "Sub-Agent MCP server. Tools are invoked via the MCP protocol at "
                f"{MCP_TRANSPORT_PATH}; tool paths document input/output schemas."
            ),
        },
        "paths": paths,
        "tags": [
            {"name": "mcp", "description": "Model Context Protocol transport"},
            {"name": "tools", "description": "MCP tool schemas (invoke via /mcp)"},
            {"name": "meta", "description": "Server metadata"},
        ],
    }


def register_openapi_route(mcp: FastMCP) -> None:
    """Register GET /mcp/openapi.json on the FastMCP HTTP app."""

    @mcp.custom_route(OPENAPI_PATH, methods=["GET"], name="openapi")
    async def openapi_handler(_request: Request) -> Response:
        document = build_openapi_document(mcp)
        return JSONResponse(document)
