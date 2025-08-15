import asyncio
from mcp_agent.app import MCPApp
from adeptly_mcp_sdk.mcp.servers import configure_app
from adeptly_mcp_sdk.core.agent_base import AgentBase, AgentContract
from adeptly_mcp_sdk.core.storage import save_artifact, log_run
from adeptly_mcp_sdk.core.governance import review_text

contract = AgentContract(
    name="router_agent",
    instruction="Classify intent, plan, assign agents, schedule governance review, escalate blockers."
)

async def main():
    app = MCPApp(name="router_agent")
    configure_app(app)
    async with app.run():
        mcp_agent = AgentBase(contract).build()
        async with mcp_agent:
            # Placeholder output; swap to real LLM/tool calls.
            output = (
              "Objective: Router / Supervisor\n"
              "Body: draft output for router_agent.\n"
              "Citations: https://modelcontextprotocol.io/docs/getting-started/intro\n"
              "Risks: ...\nNext Steps: ..."
            )
            ok, issues = review_text(output)
            if not ok:
                output += "\n\n[REVISE] Issues: " + ", ".join(issues)
            path = save_artifact(output)
            log_run({"agent":"router_agent","artifact":path,"ok":ok,"issues":issues})
            print(path)

if __name__ == "__main__":
    asyncio.run(main())
