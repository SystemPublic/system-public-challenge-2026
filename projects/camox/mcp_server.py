"""The product's tool surface: every function in tools.TOOLS, served as the MCP server "camox".

In-process (agent harness):  async with mcp.Client(mcp_server.server) as c: ...
Standalone:  .venv/bin/python mcp_server.py  -> http://127.0.0.1:8799/mcp/  (Authorization: Bearer $MCP_TOKEN)
In FastAPI:  app.mount("/mcp", mcp_server.http_app()), and run the session manager in the app's lifespan:
             async with mcp_server.server.session_manager.run(): yield
             (Mounted sub-apps do not get their own lifespan run. Call http_app() once: it creates the manager.)
"""
import os
import secrets

import uvicorn
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Mount

import tools

server = MCPServer("camox")
for fn in tools.TOOLS:
    server.add_tool(fn)


def http_app():
    """Streamable HTTP app (endpoint at its root) behind the MCP_TOKEN bearer check.
    Host checks are off so it can sit behind a proxy; the token is the gate."""
    app = server.streamable_http_app(
        streamable_http_path="/",
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
    token = os.environ["MCP_TOKEN"]

    async def guarded(scope, receive, send):
        auth = dict(scope.get("headers", [])).get(b"authorization", b"").decode()
        if scope["type"] == "http" and not secrets.compare_digest(auth, f"Bearer {token}"):
            return await PlainTextResponse("Missing or wrong bearer token", 401)(scope, receive, send)
        await app(scope, receive, send)
    return guarded


if __name__ == "__main__":
    mcp_app = http_app()
    uvicorn.run(Starlette(routes=[Mount("/mcp", mcp_app)], lifespan=lambda _: server.session_manager.run()),
                host="127.0.0.1", port=int(os.environ.get("MCP_PORT", 8799)))
