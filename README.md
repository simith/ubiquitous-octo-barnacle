# Building an MCP Server with SAP Integration Suite

> **Turn your enterprise APIs into AI-ready tools — governed, secured, and built on SAP.**

A hands-on workshop that takes you from a fresh **SAP BTP Trial** account to **four live MCP Servers** on **SAP Integration Suite**, plus an AI client that calls all of them. Every tool call is authenticated through Developer Hub, routed by the SAP IS MCP Gateway, and executed against a real backend — and the AI never sees a single backend secret.

![SAP Integration Suite MCP Gateway architecture — AI client → Developer Hub → MCP Gateway, fanning out to Purchase Order, Business Partner, Spotify, and Twilio Email backends](docs/images/fig-01.png)

## What you'll build

Four MCP Servers, each exposing a different backend as AI-callable tools, covering the two main integration patterns:

| # | MCP Server | Backend | Auth pattern |
|---|---|---|---|
| 1 | **Purchase Order** | SAP S/4HANA Cloud (OData, via BAH) | API artifact + API key (Content Modifier); Policies auto-wired |
| 2 | **Business Partner** | SAP CRM (OData, via BAH) | API artifact + API key (Content Modifier); Policies auto-wired |
| 3 | **Spotify** | Spotify Web API | External OpenAPI spec; OAuth2 Client Credentials; manual Policies |
| 4 | **Twilio Email** | Twilio Comms API | External OpenAPI spec; HTTP Basic Auth; manual Policies |

Then you connect an **AI client** that talks to all four servers at once — either an LLM-powered agent, or a menu-driven client that needs no AI API key.

## How it works

```text
Business user ──query──▶ MCP Client ──MCP + Bearer JWT──▶ SAP IS MCP Gateway ──▶ 4 MCP Servers ──▶ backends
                             │                                     ▲
                             └──── OAuth2 client credentials ──────┘
                                        (SAP Developer Hub)
```

The gateway validates the JWT, speaks JSON-RPC (`initialize` → `tools/list` → `tools/call`), and requires the header `Accept: application/json, text/event-stream` on every request. The two BAH-based servers inject their API key server-side; Spotify and Twilio use a Security Material (OAuth2 CC / Basic Auth) bound on the Policies tab.

## Repository contents

| Path | Purpose |
|---|---|
| `docs/README.md` | Workshop home — the business story and architecture |
| `docs/00-prerequisites.md` | Opening Integration Suite from the BTP Cockpit |
| `docs/01-purchase-order-mcp.md` | Full end-to-end build: API artifact → MCP Server → Developer Hub → subscribe |
| `docs/02-business-partner-mcp.md` | Same pattern, Business Partner API (abbreviated) |
| `docs/03-spotify-mcp.md` | External spec, OAuth2 Client Credentials, manual Policies |
| `docs/04-twilio-mcp.md` | External spec, HTTP Basic Auth, send email from an AI agent |
| `docs/05-ai-agent.md` | Connect an AI client — Option A (LLM agent) and Option B (menu client) |
| `docs/06-checklist.md` | Progress checklist with completion tracking |
| `docs/07-why-this-matters.md` | The big picture: what you built and why it matters |
| `docs/downloads/` | Downloadable assets (specs + client scripts, see below) |
| `docs/images/` | Screenshots (`fig-01.png` … `fig-46.png`, in doc order) |
| `mkdocs.yml` | MkDocs Material site configuration |

### Downloadable assets (`docs/downloads/`)

| File | What it is |
|---|---|
| `spotify_oas3_fixed.json` | Spotify OpenAPI 3.0 spec, corrected so SAP IS accepts it |
| `twilio_email_oas3.json` | Twilio Email OpenAPI 3.0 spec (2 tools: send + status) |
| `mcp.sample.json` | Config template — `servers[]` credentials + optional `llm` block |
| `mcp_agent.py` | **Option A** — natural-language agent (needs an LLM API key) |
| `mcp_client_simple.py` | **Option B** — menu-driven client (no AI key required) |

## Before you start

- An **SAP BTP Trial account** — [create one](https://developers.sap.com/tutorials/hcp-create-trial-account/)
- **SAP Integration Suite** subscribed and activated — [set it up](https://developers.sap.com/tutorials/cp-starter-isuite-onboard-subscribe)
- **Python 3.8+** installed locally (for the AI client section)

Spotify and Twilio are optional and independent — the AI client works with whichever servers you deploy.

## Reading the workshop

Start at [`docs/README.md`](docs/README.md) and follow the sections in order.

To preview the site locally with full navigation and the progress tracker:

```bash
pip install mkdocs-material
mkdocs serve
# open http://127.0.0.1:8000
```

## The two integration patterns at a glance

- **BAH APIs (Purchase Order, Business Partner)** — wrapped in an **API artifact** whose Content Modifier injects the API key as a header. When the MCP Server is created *from an API artifact*, its Policies HTTP connection is **auto-wired** — no manual setup.
- **External specs (Spotify, Twilio)** — the OpenAPI spec is uploaded **directly** to the MCP Server. You create a **Security Material** (OAuth2 Client Credentials for Spotify, User Credentials for Twilio) and **manually configure the Policies HTTP Connection** to bind it. Skipping this returns `Error occurred while fetching egress connection details`.

> **Security:** Never commit `clientsecret`, API keys, bearer tokens, or `mcp.json` files containing real credentials to GitHub. The `mcp.sample.json` template ships with placeholders only.
