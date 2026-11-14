"""The graph tools as an MCP server over streamable HTTP, behind one bearer token (MCP_TOKEN in .env).

Run: .venv/bin/python mcp_server.py   then connect any MCP client to http://localhost:8799/mcp
"""
import os
import secrets
import sys
from pathlib import Path

import uvicorn
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import PlainTextResponse

sys.path.insert(0, str(Path(__file__).parent / "agent"))
import agent  # noqa: E402  (loads .env)
import tools  # noqa: E402

PORT = int(os.environ.get("MCP_PORT", 8799))
server = MCPServer("camox-graph", instructions=agent.SYSTEM)
for fn in tools.TOOLS:
    server.add_tool(fn)
# Host checks are off so the server can sit behind a proxy; the bearer token is the gate.
app = server.streamable_http_app(transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))


def require_token(app, token=os.environ["MCP_TOKEN"]):
    async def guarded(scope, receive, send):
        auth = dict(scope.get("headers", [])).get(b"authorization", b"").decode()
        if scope["type"] == "http" and not secrets.compare_digest(auth, f"Bearer {token}"):
            return await PlainTextResponse("Missing or wrong bearer token", 401)(scope, receive, send)
        await app(scope, receive, send)
    return guarded


if __name__ == "__main__":
    uvicorn.run(require_token(app), host="127.0.0.1", port=PORT)
