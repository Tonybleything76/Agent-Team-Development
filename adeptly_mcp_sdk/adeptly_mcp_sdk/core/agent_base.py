from dataclasses import dataclass, field
from typing import List
from mcp_agent.agents.agent import Agent as MCPAgent

@dataclass
class AgentContract:
    name: str
    instruction: str
    server_names: List[str] = field(default_factory=lambda: ["fetch","filesystem"])

class AgentBase:
    def __init__(self, contract: AgentContract):
        self.contract = contract

    def build(self) -> MCPAgent:
        return MCPAgent(
            name=self.contract.name,
            instruction=self.contract.instruction,
            server_names=self.contract.server_names
        )
