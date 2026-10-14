# 5. AI Agent Client

With all four MCP Servers deployed and subscribed, you can connect an AI agent that talks to all of them at once — the **Supplier Risk Intelligence** agent from the overview story. This section covers two options; choose the one that fits your environment.

| Option | What you need | Best for |
|---|---|---|
| **A — LLM-Powered Agent** | An Anthropic (or compatible) API key | Natural-language questions; the AI reasons and chains calls across all four servers |
| **B — Simple Menu Client** | Nothing beyond Python 3 | Quick demo with no API key; pick operations from a numbered menu |

Both read the same `mcp.json` and both ship with an optional **live flow visualization** that animates each MCP call in your browser.

---

## Shared Setup — `mcp.json`

Both options read their server credentials from a single `mcp.json` file. Start here regardless of which option you choose.

### Download the bundle

Everything you need is in one zip. Download it and unzip into a single folder:

[Download sap-mcp-agent.zip](downloads/sap-mcp-agent.zip){ .md-button .md-button--primary download="sap-mcp-agent.zip" }

| File | What it does |
|---|---|
| `mcp.json` | Your **configuration** — the four servers' URLs and credentials, plus an optional AI key. You edit this; both clients read it. |
| `mcp_agent.py` | **Option A** — the LLM-powered agent. Sends your natural-language question to Claude, which picks and chains tool calls across the four servers. |
| `mcp_client_simple.py` | **Option B** — the no-AI menu client. Routes numbered menu choices straight to specific tools; needs no API key. |
| `flow_server.py` | Optional live visualization used by **both** clients — it animates each MCP call in your browser. Delete it and both clients run exactly the same, just without the animation. |

Keep all four files in the **same folder**.

### Fill in your credentials

Open **`mcp.json`** — it already contains all four servers in the right shape. Replace every `YOUR_...` placeholder with the real values from your four Developer Hub subscriptions:

```json
{
  "servers": [
    {
      "alias": "po",
      "name": "purchaseordermcp",
      "domain": "Procurement / Purchase Orders",
      "url": "https://YOUR_IS_TENANT.integration.cloud.sap/purchaseordermcp",
      "token_url": "https://YOUR_AUTH_DOMAIN.authentication.REGION.hana.ondemand.com/oauth/token",
      "client_id": "YOUR_CLIENT_ID_FOR_PO",
      "client_secret": "YOUR_CLIENT_SECRET_FOR_PO"
    }
    // bp, inbound, and stock follow with the same shape — all four are already in the file
  ],

  "llm": {
    "base_url": "https://api.anthropic.com/",
    "api_key": "YOUR_ANTHROPIC_API_KEY_OPTIONAL",
    "model": "claude-sonnet-4-6",
    "max_tokens": 2048
  }
}
```

- Each `url` is on that MCP Server artifact's **Overview** tab in Integration Suite.
- Each `token_url`, `client_id`, and `client_secret` come from that server's **Developer Hub subscription** credentials page ([Part I of Section 1](bah-01-purchase-order.md#part-i-subscribe-and-get-credentials)).
- The **`llm` block is optional** — fill `api_key` only if you have an Anthropic key and want to use **Option A**. **Option B** ignores it entirely.

!!! info "No AI key? You can still do the whole workshop"
    The `llm` block is read **only** by **Option A** (the natural-language agent). If you have no AI key, use **Option B — Simple Menu Client**: it connects to the same four servers using just the `servers` credentials and ignores the `llm` block entirely. You still exercise the full MCP chain: OAuth2 token → `initialize` → `tools/list` → `tools/call` → live SAP data.

!!! warning "Keep mcp.json private"
    `mcp.json` contains live credentials. Keep it on your machine only — don't share it, paste it into chat, or include it in screenshots.

---

## Option A — LLM-Powered Agent

### Requirements

- Python 3.8+ (standard library only — no `pip install` needed)
- A valid `mcp.json` with your four servers' credentials **and** an Anthropic API key in the `llm` block

### Run

```bash
python3 mcp_agent.py
```

Type `start` when prompted. The agent will:

1. Authenticate to all four MCP Servers using OAuth2 client credentials
2. Discover every tool from each server
3. Print the **Supplier Risk Intelligence** boot banner with each server's status and tool count
4. Open the live flow visualization in your browser (unless `MCP_VIZ=0`)
5. Wait for your natural-language question

### Example questions

=== "Single system"
    ```
    which suppliers have the most open purchase orders?
    how much stock do we have for material TG0013?
    what deliveries are in transit for supplier 17300001?
    ```

=== "Supplier lookup"
    ```
    show me all open POs for supplier 17300001
    who is supplier 17300001 — name, country, status?
    ```

=== "Cross-system risk (the showcase)"
    ```
    give me a full risk picture for supplier 17300001
    ```

!!! tip "The showcase query"
    *"Give me a full risk picture for supplier 17300001"* makes the agent chain calls across **all four** servers — open-PO exposure, supplier master, in-transit deliveries, and stock buffer — then summarise it as a single risk briefing. Supplier **17300001** and material **TG0013** are seeded across all four sandbox systems, so this always returns a complete picture.

!!! note "How the agent works"
    The agent sends your text to Claude along with the description of every available tool. Claude decides which server and tool to call, executes it through the MCP gateway, reads the result, and writes a plain-English summary — chaining multiple calls in one turn when needed. The LLM never sees your backend credentials, only tool names and their results.

### Can I use Claude Desktop instead?

Not directly — and it's worth understanding why, because it explains what `mcp_agent.py` does for you.

The SAP IS MCP gateway requires two things on every call:

1. An **OAuth2 _client-credentials_ bearer token** — your client exchanges the subscription's `client_id` + `client_secret` at the `token_url` for a short-lived token, then sends it as `Authorization: Bearer …`.
2. The header **`Accept: application/json, text/event-stream`**.

Claude Desktop's built-in remote-MCP connector is designed for servers that use **interactive (authorization-code) OAuth** — it logs you in through a browser. It does **not** perform the machine-to-machine *client-credentials* exchange these subscriptions use, so pointing it straight at your MCP URL will fail to authenticate.

**Use the provided `mcp_agent.py` (Option A)** — it performs the token exchange and sets the required header for all four servers, and it's the path validated in this workshop. If you specifically want Claude Desktop, you'd need a small local **stdio-to-HTTP bridge** that fetches the client-credentials token and forwards requests with both headers — that's beyond this workshop's scope.

---

## Option B — Simple Menu Client (No AI Key Required)

A deterministic, menu-driven client. It connects to the same four servers using your `mcp.json` and routes each menu choice to a specific tool — no LLM involved.

### Requirements

- Python 3.8+ (standard library only)
- A valid `mcp.json` — the `llm` block is not required; leave the placeholder or delete the block

### Run

```bash
python3 mcp_client_simple.py
```

The client authenticates to all four servers and shows a menu:

```
╔══════════════════════════════════════════════════╗
║   SUPPLIER RISK — MCP Client (No LLM)           ║
║   SAP Integration Suite · Direct tool access    ║
╚══════════════════════════════════════════════════╝

  4/4 servers connected  ·  40 tools available

  ── Purchase Orders ────────────────────
  1  List Purchase Orders
  2  Get Purchase Order by ID
  ── Suppliers / Business Partners ─────
  3  List Suppliers
  4  Get Supplier by Number
  ── Inbound Deliveries ─────────────────
  5  List Inbound Deliveries
  6  Get Delivery by ID
  ── Material Stock ─────────────────────
  7  Check Stock for a Material
  8  List All Stock
  ── Diagnostics ────────────────────────
  9  Show all available tools

  0  Exit
```

Pick a number, provide any input it asks for (a PO ID, supplier number, material like `TG0013`), and the result is printed in a readable format. Like the agent, it opens the live flow visualization in your browser unless `MCP_VIZ=0`.

!!! tip "What values to enter"
    The seeded demo data is consistent across all four sandbox systems:

    - **Supplier / Business Partner number** → `17300001` (the showcase supplier — appears in every system)
    - **Material** → `TG0013`
    - **Purchase Order ID** and **Inbound Delivery number** vary per sandbox, so there's no fixed value to type. Run the matching **List** option first (**List Purchase Orders**, **List Inbound Deliveries**), then copy an ID from the results into the **Get … by ID** option.

### What Option B demonstrates

Even without an LLM, this client proves the full MCP chain is live for all four servers:

- OAuth2 token acquisition from each Developer Hub subscription
- MCP `initialize` → `tools/list` → `tools/call` sequence
- The `Accept: application/json, text/event-stream` header requirement
- Live records from each SAP backend

---

## The `Accept` Header — What Every Client Must Include

If you build your own client in any language, **every** request to the SAP IS MCP gateway must include:

```
Accept: application/json, text/event-stream
```

Without it the gateway returns `400 Bad Request`. The SAP IS MCP endpoint supports both plain JSON and Server-Sent Events (SSE) responses — this header tells it the client can handle either.

---

## Checklist

- [ ] `mcp.json` created with all four servers' credentials filled in
- [ ] Chose Option A (AI key) or Option B (no key)
- [ ] Client connected to all four servers (4/4 online)
- [ ] At least one tool call returned live data from each server
- [ ] *(Showcase)* Ran the full risk-picture query across all four systems

You've built four MCP Servers on SAP Integration Suite and connected an agent that reasons across all of them. 🎉

Next: [Why This Matters →](bah-06-why-this-matters.md)
