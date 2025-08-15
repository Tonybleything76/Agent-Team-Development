# Adeptly Agents — Overview

**Purpose**  
Build a family of specialized AI agents on top of the **Model Context Protocol (MCP)** so all tool/data access is standardized and swappable.

**Why MCP (in one line)**  
MCP is a standard “port” for AI apps (like USB‑C for tools/data); it has official SDKs and ready‑made servers you can plug in.

**Key repos we depend on**
- `mcp-agent` — composable agent framework that implements Anthropic patterns; manages MCP server lifecycles.
- (optional) `Agent-MCP` — patterns for parallel agents + persistent knowledge graph; useful as we scale.
- Official MCP servers (filesystem, fetch, etc.)
- Community “awesome” MCP servers (discovery)
