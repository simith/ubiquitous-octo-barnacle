# SAP BAH MCP Workshop — Overview

This workshop builds **four MCP Servers** on SAP Integration Suite, each wrapping a standard SAP S/4HANA Cloud API from the **SAP Business Accelerator Hub (BAH)** — then connects them all to a single AI agent that can reason across the four systems at once.

Unlike the companion tutorial (which uses public third-party APIs like Spotify and Twilio), **every server here is a native SAP API from BAH**. That makes the pattern identical across all four servers: `API artifact → Content Modifier → MCP Server from API`. Build the first one carefully and the other three are a short set of value substitutions.

---

## The Story — Supplier Risk Intelligence

> Maya runs supply-chain operations. Every morning she opens four screens to answer one question — *"Which suppliers are a risk this week?"* She checks **open purchase orders** (how much is she committed to spend?), **supplier master data** (who are they, are they active?), **inbound deliveries** (what is in transit and is it late?), and **warehouse stock** (do we have buffer if a delivery slips?). Cross-referencing them by hand takes most of her morning.
>
> With an MCP-powered agent built on SAP Integration Suite, Maya asks the question once. The agent queries all four SAP systems through governed MCP tools, cross-references them on the supplier ID, and briefs her in seconds — *"Supplier 17300001 has high open-PO exposure, a delivery arriving late, and low stock on the affected material. High risk."*

Each of the four MCP Servers you build is one of those four screens — and the agent in [Section 5](bah-05-ai-agent.md) is what ties them together.

---

## Architecture

![SAP Integration Suite MCP Gateway architecture — AI client authenticates via the Developer Hub, every tool call flows through the MCP Gateway to four MCP Servers, each auto-wired to its own API Artifact (Content Modifier injects the APIKey) and routed to the single SAP Business Accelerator Hub backend](images/edited/bah-architecture.png)

The AI client authenticates once through the **Developer Hub** (OAuth2 client credentials → Bearer JWT), then every tool call flows through the **SAP IS MCP Gateway**, which validates the token and routes to one of the four MCP Servers. Each server is auto-wired to its own **API Artifact** — a Content Modifier injects the sandbox `APIKey` — and all four reach the same **SAP Business Accelerator Hub** backend over HTTPS. The client never holds a single backend secret.

Every server follows the **same uniform pattern** — `MCP Server → API Artifact (APIKey) → SAP BAH`. There are no external third-party APIs and no per-server OAuth2/Basic-Auth security materials; the one BAH API key authenticates all four.

---

## What You Will Build

| # | MCP Server | SAP system | What the agent can ask it |
|---|---|---|---|
| 1 | **Purchase Order** | Procurement | Open POs and spend exposure by supplier |
| 2 | **Business Partner** | Supplier master | Supplier name, contact, country, status |
| 3 | **Inbound Delivery** | Logistics | Shipments in transit, materials, expected dates |
| 4 | **Material Stock** | Warehouse | Current stock on hand by material and plant |

All four are **read-only** (the SAP sandbox does not allow writes), which is exactly what a risk-analysis agent needs.

---

## Workshop Sections

| Section | Depth | What it covers |
|---|---|---|
| [1. Purchase Order MCP](bah-01-purchase-order.md) | **Full end-to-end** | Every step, start to finish. Read this one carefully. |
| [2. Business Partner MCP](bah-02-business-partner.md) | Follow Section 1 | Only the Business Partner-specific values |
| [3. Inbound Delivery MCP](bah-03-inbound-delivery.md) | Follow Section 1 | Only the Inbound Delivery-specific values |
| [4. Material Stock MCP](bah-04-material-stock.md) | Follow Section 1 | Only the Material Stock-specific values |
| [5. AI Agent Client](bah-05-ai-agent.md) | Connect everything | Point one agent at all four servers |

---

## Track Your Progress

Each section (1–5) ends with a checklist. Tick the boxes as you go — they're saved in your browser and persist between sessions, and the bar below (plus the **Tutorial Progress** indicator in the header) updates automatically.

<div id="tp-overview"></div>

---

## What You Need

- A **SAP BTP** account with **Integration Suite** subscribed and the **Integration Cell** runtime available. If you don't have this yet, see [Prerequisites](00-prerequisites.md).
- A free **SAP Business Accelerator Hub** account (for the API specs and the sandbox API key) — [api.sap.com](https://api.sap.com).
- Python 3.8+ if you want to run the AI agent in [Section 5](bah-05-ai-agent.md). *(Optional — a no-AI menu client is included too.)*

Next: [Build the Purchase Order MCP Server →](bah-01-purchase-order.md)
