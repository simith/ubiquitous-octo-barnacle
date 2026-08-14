# Building an MCP Server with SAP Integration Suite

> **From enterprise APIs to AI-ready tools — without building an MCP server from scratch.**

This repository turns the original Word tutorial into a GitHub-first, developer-friendly walkthrough for building and connecting an **MCP Server using SAP Integration Suite** in an **SAP BTP Trial** environment.

The tutorial takes you from a fresh BTP trial account to a deployed MCP endpoint that can be consumed by MCP-compatible AI clients such as **Joule Work Desktop** and **Claude Desktop**.

## What you'll build

```text
                    ┌──────────────────────┐
                    │     AI Client        │
                    │ Joule / Claude       │
                    └──────────┬───────────┘
                               │ MCP
                               ▼
                    ┌──────────────────────┐
                    │  MCP Server Artifact │
                    │ SAP Integration Suite│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    API Artifact      │
                    │   HTTP API Proxy     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Backend API        │
                    │ SAP / External API   │
                    └──────────────────────┘
```

Along the way, you'll configure authentication and governance policies including **IP Filter, Surge Protection, and Quota**.

## Repository contents

| Path | Purpose |
|---|---|
| `docs/01-prerequisites.md` | BTP Trial, Integration Suite, roles, service key and destination |
| `docs/02-build-mcp-server.md` | Package, API artifact and MCP Server artifact |
| `docs/03-govern-and-deploy.md` | MCP policies and deployment |
| `docs/04-connect-ai-clients.md` | Joule Work Desktop and Claude Desktop |
| `docs/05-end-to-end-checklist.md` | Quick validation checklist |
| `images/` | Screenshots extracted from the original tutorial |
| `LICENSE` | Repository license |
| `.gitignore` | Prevents secrets and local files from being committed |

## Before you start

You need:

- An SAP BTP Trial account
- Access to SAP Integration Suite
- An API/backend that the MCP Server will expose
- An MCP-compatible AI client for the final test

> **Security:** Never commit `clientsecret`, API keys, bearer tokens, or other credentials to GitHub.

## The journey

### 1. Prepare SAP BTP

Create the BTP Trial environment, subscribe to Integration Suite, assign the required trial roles, create an OAuth2 service instance/service key, and configure a destination.

→ [Start with the prerequisites](docs/01-prerequisites.md)

### 2. Turn the API into an MCP Server

Create an Integration Package, add an API artifact, deploy it, then create an MCP Server artifact linked to the API.

→ [Build the MCP Server](docs/02-build-mcp-server.md)

### 3. Add enterprise governance

Configure authentication and authorization together with IP filtering, surge protection and quota controls. Deploy the MCP Server and obtain its MCP URL.

→ [Govern and deploy](docs/03-govern-and-deploy.md)

### 4. Connect an AI client

Use the MCP URL and OAuth2 credentials to connect Joule Work Desktop or Claude Desktop.

→ [Connect an AI client](docs/04-connect-ai-clients.md)

## End state

At the end of the tutorial, your MCP Server is live and secured. AI agents can discover and call the backend API tools through MCP, while requests pass through the configured governance policies.

---

## Source

This repository is a GitHub-oriented reworking of the supplied **“Building an MCP Server with SAP Integration Suite”** tutorial, Version 1.0, for the BTP Trial environment. The source tutorial covers the complete flow from BTP setup through AI-client connection. fileciteturn0file0L31-L60

## Suggested GitHub presentation

For a public repository, consider adding:

- A short demo GIF at the top of the README
- An architecture diagram
- A “30-minute quick start” section
- A troubleshooting page
- A `docs/` navigation sidebar if published with GitHub Pages
- A small sample API/OpenAPI definition so readers can reproduce the scenario
