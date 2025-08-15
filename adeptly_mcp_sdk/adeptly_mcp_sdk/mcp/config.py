# adeptly_mcp_sdk/mcp/config.py

from typing import List
from .servers import SERVER_REGISTRY

# Names that must be present in SERVER_REGISTRY
DEFAULT_SERVERS: List[str] = ["fetch", "filesystem"]

# If your aggregator/connection manager expects a callable:
def get_default_server_commands():
    """Return the list of server command definitions for the default set."""
    return {name: SERVER_REGISTRY[name] for name in DEFAULT_SERVERS}
