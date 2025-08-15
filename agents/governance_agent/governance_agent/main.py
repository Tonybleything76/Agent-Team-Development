import asyncio
from mcp_agent.app import MCPApp
from adeptly_mcp_sdk.mcp.servers import configure_app
from adeptly_mcp_sdk.core.agent_base import AgentBase, AgentContract
from adeptly_mcp_sdk.core.storage import save_artifact, log_run
from adeptly_mcp_sdk.core.governance import review_text

contract = AgentContract(
    name="governance_agent",
    instruction="Run policy checks, verify citations/PII/tone/accessibility, approve/return; track trends."
)

async def main():
    app = MCPApp(name="governance_agent")
    configure_app(app)
    async with app.run():
        mcp_agent = AgentBase(contract).build()
        async with mcp_agent:
            # Placeholder output; swap to real LLM/tool calls.
            output = (
              "Objective: Governance Evaluator\n"
              "Body: draft output for governance_agent.\n"
              "Citations: https://modelcontextprotocol.io/docs/getting-started/intro\n"
              "Risks: ...\nNext Steps: ..."
            )
            ok, issues = review_text(output)
            if not ok:
                output += "\n\n[REVISE] Issues: " + ", ".join(issues)
            path = save_artifact(output)
            log_run({"agent":"governance_agent","artifact":path,"ok":ok,"issues":issues})
            print(path)

if __name__ == "__main__":
    asyncio.run(main())
