# Building an MCP Server with SAP Integration Suite

> From enterprise APIs to AI-ready tools — without building an MCP server from scratch.

This tutorial walks you through building and connecting an **MCP Server using SAP Integration Suite** in an **SAP BTP Trial** environment — from a fresh account to a deployed MCP endpoint consumable by AI clients such as **Joule Work Desktop** and **Claude Desktop**.

[Download PDF](tutorial.pdf){ .md-button .md-button--primary }

---

## What you will build

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

---

## Steps

| | Step | What happens |
|---|---|---|
| 1 | [Prerequisites](01-prerequisites.md) | BTP Trial, Integration Suite, roles, service key, destination |
| 2 | [Build MCP Server](02-build-mcp-server.md) | Integration Package, API artifact, MCP Server artifact |
| 3 | [Govern & Deploy](03-govern-and-deploy.md) | IP Filter, Surge Protection, Quota, deployment |
| 4 | [Connect AI Clients](04-connect-ai-clients.md) | Joule Work Desktop and Claude Desktop |
| 5 | [End-to-End Checklist](05-end-to-end-checklist.md) | Quick validation sheet |

---

## Before you start

You need:

- An SAP BTP Trial account
- Access to SAP Integration Suite
- An API or backend that the MCP Server will expose
- An MCP-compatible AI client for the final test

> **Security:** Never commit `clientsecret`, API keys, bearer tokens, or other credentials to GitHub.

---

## Download PDF

Click **Download PDF** above to download a pre-built PDF of the complete tutorial.
The PDF is automatically regenerated on every push to `main`.
