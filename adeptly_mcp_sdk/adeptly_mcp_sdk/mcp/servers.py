# adeptly_mcp_sdk/mcp/servers.py
from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import os

@dataclass
class MCPServerSpec:
    name: str
    command: List[str]
    transport: str = "stdio"
    env: Optional[Dict[str, str]] = None

    def as_dict(self) -> Dict:
        return {
            "command": self.command,
            "transport": self.transport,
            "env": self.env,
        }

def _default_filesystem_spec() -> MCPServerSpec:
    return MCPServerSpec(
        name="filesystem",
        command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
        transport="stdio",
    )

def _default_fetch_spec() -> MCPServerSpec:
    return MCPServerSpec(
        name="fetch",
        command=["python", "-m", "mcp_server_fetch"],
        transport="stdio",
    )

def configure_app() -> Dict[str, Dict]:
    """
    Return a registry (dict) of MCP server specs keyed by name.
    The agent will attach this registry to MCPApp in a version-compatible way.
    """
    servers: Dict[str, MCPServerSpec] = {}
    if os.getenv("MCP_ENABLE_FILESYSTEM", "1") != "0":
        servers["filesystem"] = _default_filesystem_spec()
    if os.getenv("MCP_ENABLE_FETCH", "1") != "0":
        servers["fetch"] = _default_fetch_spec()
    # Convert to plain dicts
    return {name: spec.as_dict() for name, spec in servers.items()}
