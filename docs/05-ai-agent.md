# 5. AI Agent Client

With all four MCP Servers deployed and subscribed, you can now connect an AI agent that talks to all of them simultaneously. This section covers two options — choose the one that fits your environment.

| Option | What you need | Best for |
|---|---|---|
| **A — LLM-Powered Agent** | An Anthropic (or compatible) API key | Full natural-language interaction; the AI reasons across all servers |
| **B — Simple Menu Client** | Nothing beyond Python 3 | Quick demo without an API key; pre-built queries, no AI required |

---

## Shared Setup — `mcp.json`

Both options read their server credentials from a single `mcp.json` file. Start here regardless of which option you choose.

### Download the sample config

[Download mcp.sample.json](downloads/mcp.sample.json){ .md-button download="mcp.sample.json" }

### Fill in your credentials

Rename the file to `mcp.json` and replace every `YOUR_...` placeholder with the real values from your Developer Hub subscriptions. **The only required part is the `servers` list** — the `llm` block at the bottom is optional (see the note below):

```json
{
  "servers": [
    {
      "alias": "po",
      "name": "purchaseordermcp",
      "domain": "Procurement / Purchase Orders",
      "url": "YOUR_MCP_URL_FOR_PO",
      "token_url": "YOUR_TOKEN_URL_FOR_PO",
      "client_id": "YOUR_KEY_FOR_PO",
      "client_secret": "YOUR_SECRET_FOR_PO"
    }
    // ... bp, spotify, email servers follow the same shape
  ],

  "llm": {
    "base_url": "https://api.anthropic.com/",
    "api_key": "YOUR_ANTHROPIC_API_KEY_OPTIONAL",
    "model": "claude-sonnet-4-6",
    "max_tokens": 2048
  }
}
```

The `url` for each server is shown on the MCP Server artifact's **Overview** tab in Integration Suite. The `token_url`, `client_id`, and `client_secret` come from your **Developer Hub subscription** credentials page.

!!! info "No AI API key? Read this first — you can still do the whole workshop"
    The `llm` block exists in the file **only** for **Option A** below (the natural-language agent that uses Claude to decide which tool to call). It needs an Anthropic (or compatible) API key.

    **If you don't have an AI key, you don't need one.** Use **Option B — Simple Menu Client** instead: it connects to the same four MCP Servers using only the `servers` credentials and lets you call every tool from a numbered menu — no AI involved. Option B ignores the `llm` block entirely, so you can leave the `api_key` placeholder exactly as-is (or delete the whole `llm` block). You still exercise the complete MCP chain: OAuth2 token → `initialize` → `tools/list` → `tools/call` → live backend data.

    In short: **Option A = you have an AI key** (agent reasons for you). **Option B = you don't** (you pick tools from a menu). Both use the identical server credentials.

!!! warning "Keep mcp.json private"
    `mcp.json` contains live credentials. Keep it on your machine only — don't share it, paste it into chat, or include it in screenshots.

---

## Option A — LLM-Powered Agent

### Download

[Download mcp_agent.py](downloads/mcp_agent.py){ .md-button download="mcp_agent.py" }

### Requirements

- Python 3.8+ (no third-party packages needed — uses stdlib only)
- A valid `mcp.json` with your server credentials **and** an Anthropic API key in the `llm` section

### Run

```bash
python3 mcp_agent.py
```

Type `start` when prompted. The agent will:

1. Authenticate to all four MCP Servers using OAuth2 client credentials
2. Discover all available tools from each server
3. Print the **Ops Command Center** boot banner showing each server's status and tool count
4. Wait for your natural-language input

### Example queries

=== "Procurement"
    ```
    list all the open purchase orders
    show me purchase order 4500000001
    ```

=== "CRM"
    ```
    who are our top business partners?
    show me customer number 1925865
    ```

=== "Email"
    ```
    send an email to me@example.com saying that PO 4500000001 has been confirmed
    ```

=== "Spotify"
    ```
    search spotify for Coldplay
    get the top albums for artist 4gzpq5DPGxSnKTe4SA8HAU
    ```

=== "Cross-domain"
    ```
    list all customers, then pull the details for the first one and send them an email about their account
    ```

!!! note "How the agent works"
    The agent sends your text to an LLM (Claude) along with a description of all available tools. Claude decides which server and tool to call, executes the call through the MCP gateway, receives the result, and writes a plain-English summary. It can chain multiple tool calls in a single turn. The LLM never sees your backend credentials — only the tool names and their results.

### Using Option A with Claude Desktop

If you have Claude Desktop installed, you can connect your MCP servers directly without running `mcp_agent.py`.

Edit your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add each server as an MCP entry:

```json
{
  "mcpServers": {
    "purchaseordermcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"],
      "env": {
        "MCP_SERVER_URL": "YOUR_MCP_URL_FOR_PO",
        "MCP_TOKEN_URL": "YOUR_TOKEN_URL_FOR_PO",
        "MCP_CLIENT_ID": "YOUR_KEY_FOR_PO",
        "MCP_CLIENT_SECRET": "YOUR_SECRET_FOR_PO"
      }
    }
  }
}
```

!!! info "Claude Desktop MCP configuration"
    The exact configuration format depends on the MCP client adapter you use. The example above uses a generic HTTP MCP client. Refer to [Claude Desktop MCP documentation](https://modelcontextprotocol.io/quickstart/user) for the current recommended configuration for HTTP-based MCP servers.

---

## Option B — Simple Menu Client (No AI Key Required)

This option provides a deterministic, menu-driven client. It connects to all four MCP Servers using the same `mcp.json` credentials but routes queries based on your menu selection — no LLM involved.

### Download

[Download mcp_client_simple.py](downloads/mcp_client_simple.py){ .md-button download="mcp_client_simple.py" }

### Requirements

- Python 3.8+ (stdlib only)
- A valid `mcp.json` — the `llm` section is not required; you can remove it or leave the API key as a placeholder

### Run

```bash
python3 mcp_client_simple.py
```

The client authenticates to all servers and displays a menu:

```
╔══════════════════════════════════════╗
║   MCP CLIENT — SAP Integration Suite ║
╚══════════════════════════════════════╝

  4 servers connected | 26 tools available

  ── Purchase Orders ─────────────────
  1  List Purchase Orders
  2  Get Purchase Order by ID

  ── Business Partners ───────────────
  3  List Customers
  4  Get Customer by Number

  ── Spotify ─────────────────────────
  5  Search Spotify

  ── Email ───────────────────────────
  6  Send Email

  0  Exit
```

Select a number, provide any required inputs (ID, search term, email address), and the result is printed in a readable format.

### What Option B demonstrates

Even without an LLM, this client proves the full MCP chain is working:

- OAuth2 token acquisition from your Developer Hub subscription
- MCP `initialize` → `tools/list` → `tools/call` sequence
- The `Accept: application/json, text/event-stream` header requirement
- Live results from each backend

---

## The `Accept` Header — What Every Client Must Include

If you build your own client in any language, every request to the SAP IS MCP gateway **must** include:

```
Accept: application/json, text/event-stream
```

Without it the gateway returns `400 Bad Request`. The SAP IS MCP endpoint supports both plain JSON and Server-Sent Events (SSE) streaming responses — this header tells it the client can handle either.

---

## Checklist

- [ ] `mcp.json` created with all four servers' credentials filled in
- [ ] Chose Option A or B (or both)
- [ ] Successfully ran the client and connected to all four servers
- [ ] At least one tool call returned live data from each server

Next: [Progress Checklist →](06-checklist.md)
