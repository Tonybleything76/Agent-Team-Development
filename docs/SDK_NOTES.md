# Internal SDK Notes

**Goal**  
Make agents depend on our SDK contracts (not on a specific framework) so we can swap frameworks later with minimal churn.

**What’s inside**  
- Contracts (`AgentContract`, `AgentBase`)
- Router (pluggable)
- Governance checks (rule-based starter)
- Storage helpers (artifacts/logs)
- MCP config helpers (servers list)
