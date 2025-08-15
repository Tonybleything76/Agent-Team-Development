# Agent Guide — Contracts, Prompts, Lifecycle

**Contract (all agents)**
- `plan(goal) -> plan`
- `act(plan) -> context`
- `produce(context) -> artifact`
- `handoff(artifact) -> side-effects`

**Router (Supervisor)**
- Classify task → plan → assign agents → request Governance review → deliver.

**Governance (Evaluator)**
- Enforces: objective, citations, risks, next steps; privacy/IP; tone & accessibility.
- Returns APPROVE or REVISE with reasons.

**Initial MCP servers**
- filesystem, fetch (local). Add others gradually.
