import asyncio
from mcp_agent.app import MCPApp
from adeptly_mcp_sdk.mcp.servers import configure_app
from adeptly_mcp_sdk.core.agent_base import AgentBase, AgentContract
from adeptly_mcp_sdk.core.storage import save_artifact, log_run
from adeptly_mcp_sdk.core.governance import review_text

contract = AgentContract(
    name="qa_qc_agent",
    instruction="Create test plans, run ADA and regression checks; record sign-offs."
)

async def main():
    app = MCPApp(name="qa_qc_agent")
    configure_app(app)
    async with app.run():
        mcp_agent = AgentBase(contract).build()
        async with mcp_agent:
            # Placeholder output; swap to real LLM/tool calls.
            output = (
              "Objective: QA/QC\n"
              "Body: draft output for qa_qc_agent.\n"
              "Citations: https://modelcontextprotocol.io/docs/getting-started/intro\n"
              "Risks: ...\nNext Steps: ..."
            )
            ok, issues = review_text(output)
            if not ok:
                output += "\n\n[REVISE] Issues: " + ", ".join(issues)
            path = save_artifact(output)
            log_run({"agent":"qa_qc_agent","artifact":path,"ok":ok,"issues":issues})
            print(path)

if __name__ == "__main__":
    asyncio.run(main())
