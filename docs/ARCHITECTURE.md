# Architecture & Rationale

```
[CLI/Jobs] -> [Router/Supervisor] -> [Domain Agents: Sales | Marketing | Content]
                                   -> [Governance (Evaluator)]
Agents talk to tools/data via MCP servers (filesystem, fetch; later Notion/Google/etc.).
Artifacts -> /out ; Logs -> /logs.
```

**Why each component**
- Router: central intent classification + dispatch (router/orchestrator pattern).
- Domain Agents: single-responsibility units; easier to test, scale, parallelize.
- Governance (Evaluator): guardrails before anything external; checks citations, privacy/IP, tone, accessibility.
- MCP servers: standardized tool/data access so integrations can be swapped without refactoring agents.
- Artifacts/Logs: reproducibility and traceability from day one.
