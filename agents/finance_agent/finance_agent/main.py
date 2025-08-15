import asyncio
from mcp_agent.app import MCPApp
from adeptly_mcp_sdk.mcp.servers import configure_app
from adeptly_mcp_sdk.core.agent_base import AgentBase, AgentContract
from adeptly_mcp_sdk.core.storage import save_artifact, log_run
from adeptly_mcp_sdk.core.governance import review_text

contract = AgentContract(
    name="finance_agent",
    instruction="Forecasts, invoices, pricing sheets; month-end close."
)

async def main():
    app = MCPApp(name="finance_agent")
    configure_app(app)
    async with app.run():
        mcp_agent = AgentBase(contract).build()
        async with mcp_agent:
            # Placeholder output; swap to real LLM/tool calls.
            output = (
              "Objective: Accountant_Finance\n"
              "Body: draft output for finance_agent.\n"
              "Citations: https://modelcontextprotocol.io/docs/getting-started/intro\n"
              "Risks: ...\nNext Steps: ..."
            )
            ok, issues = review_text(output)
            if not ok:
                output += "\n\n[REVISE] Issues: " + ", ".join(issues)
            path = save_artifact(output)
            log_run({"agent":"finance_agent","artifact":path,"ok":ok,"issues":issues})
            print(path)

if __name__ == "__main__":
    asyncio.run(main())
