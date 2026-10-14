# Building MCP Servers with SAP Integration Suite

> Turn your enterprise SAP APIs into AI-ready tools — governed, secured, and built on SAP.

---

## The Problem

Your business runs on SAP — purchase orders, supplier master data, inbound deliveries, warehouse stock. AI agents are powerful, but wiring them directly into these systems means handing over credentials, losing audit control, and rebuilding the plumbing for every new tool.

**Model Context Protocol (MCP)** is the standard way for an AI agent to discover and call tools. When those tools run on **SAP Integration Suite**, every call is authenticated, logged, and policy-controlled — and the AI never sees a single backend password.

## A Real Scenario — Supplier Risk Intelligence

Maya runs supply-chain operations. Every morning she opens four screens to answer one question — *"Which suppliers are a risk this week?"* She checks **open purchase orders** (how much is committed?), **supplier master data** (who are they, are they active?), **inbound deliveries** (what is in transit and is it late?), and **warehouse stock** (is there buffer if a delivery slips?). Cross-referencing them by hand takes most of her morning.

With an MCP-powered agent she asks the question once. The agent queries all four SAP systems through governed MCP tools, cross-references them on the supplier ID, and briefs her in seconds — *"Supplier 17300001 has high open-PO exposure, a delivery arriving late, and low stock on the affected material. High risk."* **This workshop teaches you to build exactly that.**

---

## Architecture

![SAP Integration Suite MCP Gateway architecture — AI client authenticates via the Developer Hub, every tool call flows through the MCP Gateway to four MCP Servers, each auto-wired to its own API Artifact (Content Modifier injects the APIKey) and routed to the single SAP Business Accelerator Hub backend](images/edited/bah-architecture.png)

The AI client authenticates once through the **Developer Hub** (OAuth2 client credentials → Bearer JWT), then every tool call flows through the **SAP IS MCP Gateway**, which validates the token and routes to one of four MCP Servers. Each server is auto-wired to its own **API Artifact** — a Content Modifier injects the sandbox `APIKey` — and all four reach the same **SAP Business Accelerator Hub** backend. The client never holds a single backend secret.

---

## Start Here — The SAP BAH MCP Gateway Workshop

The main workshop builds **four MCP Servers** on SAP Integration Suite, each wrapping a native SAP S/4HANA Cloud API from the **SAP Business Accelerator Hub (BAH)**, then connects them all to one AI agent — the Supplier Risk Intelligence agent above.

Because every backend is a BAH API, the pattern is **identical across all four servers**: `API Artifact → Content Modifier (APIKey) → MCP Server`. Build the first one carefully and the other three are a short set of value substitutions.

| # | MCP Server | SAP system | What the agent can ask it |
|---|---|---|---|
| 1 | **Purchase Order** | Procurement | Open POs and spend exposure by supplier |
| 2 | **Business Partner** | Supplier master | Supplier name, contact, country, status |
| 3 | **Inbound Delivery** | Logistics | Shipments in transit, materials, expected dates |
| 4 | **Material Stock** | Warehouse | Current stock on hand by material and plant |

Then you point **one AI agent at all four servers** and run the full supplier-risk scenario — either with an LLM reasoning engine, or a simple menu-driven client that needs no AI API key.

**→ [Begin the SAP BAH MCP Workshop](bah-00-overview.md)**

| | Section | What happens |
|---|---|---|
| 0 | [Overview](bah-00-overview.md) | The story, the architecture, and what you'll build |
| 1 | [Purchase Order MCP](bah-01-purchase-order.md) | Full end-to-end: API artifact, Content Modifier, MCP Server, Developer Hub, subscribe, test |
| 2 | [Business Partner MCP](bah-02-business-partner.md) | Same pattern, BP-specific values |
| 3 | [Inbound Delivery MCP](bah-03-inbound-delivery.md) | Same pattern, Inbound Delivery-specific values |
| 4 | [Material Stock MCP](bah-04-material-stock.md) | Same pattern, Material Stock-specific values |
| 5 | [AI Agent Client](bah-05-ai-agent.md) | Connect all four servers and run the full risk scenario |

**Estimated time:** 2–3 hours end-to-end.

---

## Optional Extension — Integrating External Public APIs

Once you've built the four SAP servers and seen the agent reason across them, you may want to try the same MCP pattern against **real-world public APIs** outside SAP. The companion tutorial does exactly that with **Spotify** and **Twilio** — useful when the backend is *not* a BAH API and you need to wire up authentication yourself.

It shows the parts the SAP BAH flow handles for you automatically:

- **Spotify** — upload an external OpenAPI spec, create an **OAuth2 Client Credentials** security material, and configure the MCP Server's **Policies** HTTP connection by hand.
- **Twilio Email** — the same, but with **Basic Auth**, plus how SAP IS wraps `POST` tool arguments in a `requestBody` envelope.

Treat this as a "try it with your own API" sandbox — the mechanics transfer directly to any public or partner API you want to expose as MCP tools.

**→ Explore the External API Tutorial: [Spotify MCP](03-spotify-mcp.md) · [Twilio Email MCP](04-twilio-mcp.md)**

---

## Before You Start

You need:

- An **SAP BTP account** with **Integration Suite** subscribed and the **Integration Cell** runtime available — [set it up here](https://developers.sap.com/tutorials/cp-starter-isuite-onboard-subscribe). New to BTP? [Create a trial account](https://developers.sap.com/tutorials/hcp-create-trial-account/).
- A free **SAP Business Accelerator Hub** account for the API specs and sandbox API key — [api.sap.com](https://api.sap.com).
- Python 3.8+ installed locally (for the AI agent in Section 5). *Optional — a no-AI menu client is included too.*

> **Security:** Never commit credentials, API keys, bearer tokens, or `mcp.json` files containing real secrets to GitHub.
