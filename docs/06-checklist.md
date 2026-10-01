# 6. Tutorial Progress

Track your progress through all tutorial steps. Your checked items are saved in your browser — they persist between sessions.

<div id="tp-overview"></div>

---

## What This Tutorial Covers

| Step | Page | What you do |
|---|---|---|
| 0 | [Prerequisites](00-prerequisites.md) | Confirm BTP and Integration Suite are ready |
| 1 | [Purchase Order MCP](01-purchase-order-mcp.md) | Create Integration Package, add API artifact with Content Modifier, create and deploy MCP Server, publish to Developer Hub, subscribe |
| 2 | [Business Partner MCP](02-business-partner-mcp.md) | Same process as Section 1 with Business Partner-specific values |
| 3 | [Spotify MCP](03-spotify-mcp.md) | Create OAuth2 security material, create MCP Server from external spec, configure Policies HTTP connection |
| 4 | [Twilio Email MCP](04-twilio-mcp.md) | Create User Credentials security material, create MCP Server from external spec, configure Policies HTTP connection |
| 5 | [AI Agent Client](05-ai-agent.md) | Configure `mcp.json`, run the LLM agent or simple menu client |

---

## End State

When all steps are complete, four MCP Servers are live and an AI client can:

- **List and inspect purchase orders** from an SAP backend
- **Look up customers and business partners** from the CRM
- **Search the Spotify music catalog** (albums, artists, shows)
- **Send transactional emails** via Twilio

All of this is governed by SAP Integration Suite — every call is authenticated, logged, and policy-controlled.

Next: [Why This Matters →](07-why-this-matters.md)
