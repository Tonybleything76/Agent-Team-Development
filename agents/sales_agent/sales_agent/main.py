import asyncio
from inspect import signature

from mcp_agent.app import MCPApp
from adeptly_mcp_sdk.mcp.servers import configure_app
from adeptly_mcp_sdk.core.agent_base import AgentBase, AgentContract
from adeptly_mcp_sdk.core.storage import save_artifact, log_run
from adeptly_mcp_sdk.core.governance import review_text

contract = AgentContract(
    name="sales_agent",
    instruction="Capture discovery, generate follow-ups and sequences, update pipeline records."
)

async def main():
    # 1) Build the MCP server registry (filesystem, fetch, etc.)
    registry = configure_app()

    # 2) Create the app
    app = MCPApp(name="sales_agent")

    # 3) Attach registry in a version-compatible way
    attached = False
    if hasattr(app, "set_mcp_servers"):
        app.set_mcp_servers(registry)
        attached = True
    elif hasattr(app, "set_servers"):
        app.set_servers(registry)
        attached = True
    else:
        params = signature(MCPApp).parameters
        if "servers" in params:
            app = MCPApp(name="sales_agent", servers=registry)
            attached = True

    if not attached:
        print("WARNING: could not attach MCP servers; continuing without them.")

    # 4) Run the app and do a simple agent pass
    async with app.run():
        mcp_agent = AgentBase(contract).build()
        async with mcp_agent:
            output = (
                "Objective: Sales\n"
                "Body: draft output for sales_agent.\n"
                "Citations: https://modelcontextprotocol.io/docs/getting-started/intro\n"
                "Risks: ...\nNext Steps: ..."
            )
            ok, issues = review_text(output)
            if not ok:
                output += "\n\n[REVISE] Issues: " + ", ".join(issues)
            path = save_artifact(output)
            log_run({"agent": "sales_agent", "artifact": path, "ok": ok, "issues": issues})
            print(path)

if __name__ == "__main__":
    asyncio.run(main())
