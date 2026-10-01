#!/usr/bin/env python3
"""
Ops Command Center - an LLM-driven MCP agent CLI.

Connects to multiple SAP Integration Suite MCP servers (each secured with
OAuth2 client-credentials), discovers their tools, and lets you drive them
with natural language. An LLM decides which server/tool to call.

Usage:
    python3 mcp_agent.py

Then type `start` to boot the command center, or just ask in plain English.
"""

import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp.json")
MCP_ACCEPT = "application/json, text/event-stream"
SSL_CTX = ssl._create_unverified_context()
DEBUG = os.environ.get("MCP_DEBUG", "").lower() in ("1", "true", "yes")

# ---------- terminal colors ----------
class C:
    R = "\033[0m"; B = "\033[1m"; DIM = "\033[2m"
    CYAN = "\033[36m"; GREEN = "\033[32m"; YELLOW = "\033[33m"
    RED = "\033[31m"; BLUE = "\033[34m"; MAG = "\033[35m"; GREY = "\033[90m"

def c(text, color):
    return f"{color}{text}{C.R}"

def dbg(label, data):
    if not DEBUG:
        return
    sep = c("─" * 60, C.GREY)
    print(sep)
    print(c(f"[DEBUG] {label}", C.YELLOW))
    if isinstance(data, (dict, list)):
        print(c(json.dumps(data, indent=2, ensure_ascii=False), C.GREY))
    else:
        print(c(str(data), C.GREY))
    print(sep)


# ---------- low-level HTTP ----------
def http_post(url, data, headers, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    return urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)


def parse_mcp_response(raw, content_type):
    """MCP streamable-http may return JSON or an SSE stream. Handle both."""
    text = raw.decode("utf-8", errors="replace").strip()
    if "text/event-stream" in (content_type or "") or text.startswith("event:") or text.startswith("data:"):
        # extract the last `data:` JSON payload
        payload = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                payload = line[len("data:"):].strip()
        if payload:
            return json.loads(payload)
        raise ValueError(f"No data in SSE stream: {text[:200]}")
    return json.loads(text)


# ---------- MCP server wrapper ----------
class MCPServer:
    def __init__(self, cfg):
        self.alias = cfg["alias"]
        self.name = cfg["name"]
        self.domain = cfg["domain"]
        self.url = cfg["url"]
        self.token_url = cfg["token_url"]
        self.client_id = cfg["client_id"]
        self.client_secret = cfg["client_secret"]
        self._token = None
        self._token_exp = 0
        self.session_id = None
        self.tools = []
        self._rpc_id = 0

    # -- OAuth2 client-credentials --
    def get_token(self, force=False):
        if not force and self._token and time.time() < self._token_exp - 60:
            dbg(f"MCP TOKEN [{self.alias}] cache hit", {"expires_in": int(self._token_exp - time.time())})
            return self._token
        dbg(f"MCP TOKEN [{self.alias}] fetching", {"token_url": self.token_url, "client_id": self.client_id})
        body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        resp = http_post(self.token_url, body, {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }, timeout=30)
        data = json.load(resp)
        self._token = data["access_token"]
        self._token_exp = time.time() + int(data.get("expires_in", 3600))
        dbg(f"MCP TOKEN [{self.alias}] obtained", {"expires_in": data.get("expires_in"), "token_type": data.get("token_type")})
        return self._token

    # -- JSON-RPC over MCP streamable-http --
    def rpc(self, method, params=None, retry_auth=True):
        self._rpc_id += 1
        payload = {
            "jsonrpc": "2.0", "id": self._rpc_id,
            "method": method, "params": params or {},
        }
        body = json.dumps(payload).encode()
        headers = {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
            "Accept": MCP_ACCEPT,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        dbg(f"MCP REQUEST [{self.alias}] → {self.url}", {
            "method": method,
            "params": params or {},
            "session_id": self.session_id,
        })
        try:
            resp = http_post(self.url, body, headers)
        except urllib.error.HTTPError as e:
            if e.code == 401 and retry_auth:
                self.get_token(force=True)
                return self.rpc(method, params, retry_auth=False)
            raise RuntimeError(f"{self.name} HTTP {e.code}: {e.read().decode()[:200]}")
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            self.session_id = sid
        raw = resp.read()
        out = parse_mcp_response(raw, resp.headers.get("Content-Type"))
        dbg(f"MCP RESPONSE [{self.alias}] ← {method}", out)
        if isinstance(out, dict) and out.get("error"):
            raise RuntimeError(f"{self.name} RPC error: {out['error']}")
        return out.get("result", {})

    def connect(self):
        self.get_token(force=True)
        self.rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ops-command-center", "version": "1.0"},
        })
        self.tools = self.rpc("tools/list").get("tools", [])
        return self.tools

    def call_tool(self, tool_name, arguments):
        return self.rpc("tools/call", {"name": tool_name, "arguments": arguments})


# ---------- LLM (Anthropic Messages API via gateway) ----------
class LLM:
    def __init__(self, cfg):
        self.base = cfg["base_url"].rstrip("/")
        self.key = cfg["api_key"]
        self.model = cfg["model"]
        self.max_tokens = cfg.get("max_tokens", 2048)

    def messages(self, system, messages, tools=None):
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
        dbg("LLM REQUEST → " + self.base + "/v1/messages", {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "num_tools": len(tools) if tools else 0,
            "num_messages": len(messages),
            "last_message": messages[-1] if messages else None,
        })
        body = json.dumps(payload).encode()
        resp = http_post(self.base + "/v1/messages", body, {
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.key,
            "authorization": f"Bearer {self.key}",
        }, timeout=120)
        result = json.load(resp)
        dbg("LLM RESPONSE ←", {
            "stop_reason": result.get("stop_reason"),
            "usage": result.get("usage"),
            "content": result.get("content"),
        })
        return result


# ---------- Tool registry: map safe LLM tool names -> (server, mcp tool) ----------
def build_tool_registry(servers):
    """Anthropic tool names must match ^[a-zA-Z0-9_-]{1,64}$. Prefix with alias,
    truncate + dedupe if needed. Returns (anthropic_tools, registry)."""
    anthropic_tools = []
    registry = {}
    for srv in servers:
        for t in srv.tools:
            base = f"{srv.alias}_{t['name']}"
            safe = base[:64]
            n = 1
            while safe in registry:
                suffix = f"_{n}"
                safe = base[:64 - len(suffix)] + suffix
                n += 1
            schema = t.get("inputSchema") or {"type": "object", "properties": {}}
            registry[safe] = (srv, t["name"])
            anthropic_tools.append({
                "name": safe,
                "description": f"[{srv.domain}] {t.get('description','').strip()[:400]}",
                "input_schema": schema,
            })
    return anthropic_tools, registry


# ---------- story / system prompt ----------
def system_prompt(servers):
    lines = [
        "You are the OPS COMMAND CENTER — an autonomous operations agent for a company "
        "running on SAP Integration Suite. You reach live business systems through MCP "
        "tools exposed over an SAP MCP gateway. You have four domains online:",
        "",
    ]
    for s in servers:
        lines.append(f"  • {s.domain} (server: {s.name}, {len(s.tools)} tools)")
    lines += [
        "",
        "Behaviour:",
        "- When the user asks for something, pick the right tool(s) and call them. You may chain tools.",
        "- Business partners = customers/contacts. Procurement = purchase orders. Comms = email. Media = Spotify.",
        "- For Spotify get_search, the `type` parameter MUST be an array, e.g. [\"artist\"].",
        "- For email (Twilio): set the sender to from.address = \"<YOUR_TWILIO_ACCOUNT_SID>@twilio.email\" "
        "(from.name can be any label, e.g. \"Trial with Twilio\"). The Twilio trial only DELIVERS to "
        "verified recipients; if a send is rejected, say so and explain the verified-recipient rule.",
        "- The post_Emails tool takes its arguments wrapped as {\"requestBody\": {\"from\": {\"address\": ..., \"name\": ...}, "
        "\"to\": [{\"address\": ...}], \"content\": {\"subject\": ..., \"html\": ...}}}.",
        "- After tool results come back, summarise them for a human in crisp, plain language. "
        "Show key fields (IDs, names, amounts, statuses) — don't dump raw JSON unless asked.",
        "- If a tool errors, briefly diagnose (auth, bad key, server-side bug) and suggest the fix.",
        "- Stay in character as a calm, capable mission-control operator. Keep it concise.",
    ]
    return "\n".join(lines)


# ---------- rendering tool results ----------
def extract_tool_result_text(result):
    """MCP tools/call returns {content:[{type:text,text:...}], ...}. Flatten to text."""
    if not isinstance(result, dict):
        return json.dumps(result)
    parts = []
    for item in result.get("content", []):
        if item.get("type") == "text":
            parts.append(item.get("text", ""))
        else:
            parts.append(json.dumps(item))
    text = "\n".join(parts) if parts else json.dumps(result)
    return text


# ---------- boot banner ----------
def boot(servers, llm):
    print()
    print(c("  ╔══════════════════════════════════════════════════════════╗", C.CYAN))
    print(c("  ║", C.CYAN) + c("            O P S   C O M M A N D   C E N T E R           ", C.B) + c("║", C.CYAN))
    print(c("  ║", C.CYAN) + c("        SAP Integration Suite · MCP Agent Gateway         ", C.GREY) + c("║", C.CYAN))
    print(c("  ╚══════════════════════════════════════════════════════════╝", C.CYAN))
    print()
    print(c("  » Powering on. Authenticating with mission systems...", C.DIM))
    print()
    total_tools = 0
    for s in servers:
        try:
            tools = s.connect()
            total_tools += len(tools)
            dot = c("●", C.GREEN)
            print(f"    {dot} {c(s.name.ljust(20), C.B)} {c('ONLINE', C.GREEN)}  "
                  f"{c(str(len(tools))+' tools', C.YELLOW)}  {c(s.domain, C.GREY)}")
            preview = ", ".join(t["name"] for t in tools[:4])
            if len(tools) > 4:
                preview += f", +{len(tools)-4} more"
            print(f"      {c('↳ '+preview, C.GREY)}")
        except Exception as e:
            print(f"    {c('●', C.RED)} {c(s.name.ljust(20), C.B)} {c('OFFLINE', C.RED)}  {c(str(e)[:60], C.GREY)}")
    print()
    print(c("  » Reasoning core:", C.DIM), c(llm.model, C.MAG))
    print(c(f"  » {total_tools} tools live across {len(servers)} domains. Command center is READY.", C.GREEN))
    print()
    print(c("  Try:", C.B))
    print(c("    • list all purchase orders", C.GREY))
    print(c("    • show me the business partners / customers", C.GREY))
    print(c("    • search spotify for Coldplay and list their top albums", C.GREY))
    print(c("    • email me@example.com that PO #4500000000 shipped", C.GREY))
    print(c("    • type 'exit' to shut down", C.GREY))
    print()


# ---------- agentic loop for one user turn ----------
def agent_turn(user_text, history, registry, tools, system, llm, max_iters=6):
    history.append({"role": "user", "content": user_text})
    for _ in range(max_iters):
        resp = llm.messages(system, history, tools)
        blocks = resp.get("content", [])
        history.append({"role": "assistant", "content": blocks})

        # print any text the model produced
        for b in blocks:
            if b.get("type") == "text" and b.get("text", "").strip():
                print(c("\n  ⬢ ", C.CYAN) + b["text"].strip() + "\n")

        tool_uses = [b for b in blocks if b.get("type") == "tool_use"]
        if not tool_uses:
            return  # model is done

        tool_results = []
        for tu in tool_uses:
            safe_name = tu["name"]
            args = tu.get("input", {})
            srv, mcp_tool = registry.get(safe_name, (None, None))
            if srv is None:
                tool_results.append({"type": "tool_result", "tool_use_id": tu["id"],
                                     "content": f"Unknown tool {safe_name}", "is_error": True})
                continue
            print(c(f"  ⚙  {srv.name}", C.BLUE) + c(f" → {mcp_tool}", C.B)
                  + c(f"  {json.dumps(args)[:120]}", C.GREY))
            try:
                result = srv.call_tool(mcp_tool, args)
                text = extract_tool_result_text(result)
                is_err = bool(result.get("isError"))
                status = c("error", C.RED) if is_err else c("ok", C.GREEN)
                print(c(f"     ↳ {status} {len(text)} chars", C.GREY))
                tool_results.append({"type": "tool_result", "tool_use_id": tu["id"],
                                     "content": text[:12000], "is_error": is_err})
            except Exception as e:
                print(c(f"     ↳ {c('exception', C.RED)} {str(e)[:100]}", C.GREY))
                tool_results.append({"type": "tool_result", "tool_use_id": tu["id"],
                                     "content": str(e), "is_error": True})
        history.append({"role": "user", "content": tool_results})
    print(c("  ⚠ Reached max tool iterations for this turn.", C.YELLOW))


# ---------- main ----------
def main():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    llm = LLM(cfg["llm"])
    servers = [MCPServer(s) for s in cfg["servers"]]

    print(c("\n  Type 'start' to boot the Ops Command Center (or 'exit' to quit).", C.DIM))
    state = {"booted": False, "registry": {}, "tools": [], "system": ""}

    def do_boot():
        boot(servers, llm)
        online = [s for s in servers if s.tools]
        state["tools"], state["registry"] = build_tool_registry(online)
        state["system"] = system_prompt(online)
        state["booted"] = True

    START_WORDS = ("start", "boot", "power on", "init", "initialize")

    while True:
        try:
            user = input(c("\n  ops› ", C.CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print(c("\n  » Command center shutting down. Goodbye.\n", C.DIM))
            break

        if not user:
            continue
        low = user.lower()
        if low in ("exit", "quit", "shutdown", "stop"):
            print(c("\n  » Command center shutting down. Goodbye.\n", C.DIM))
            break

        if low in START_WORDS:
            do_boot()
            continue

        if not state["booted"]:
            do_boot()  # auto-boot on first real command

        try:
            agent_turn(user, main.history, state["registry"],
                       state["tools"], state["system"], llm)
        except Exception as e:
            print(c(f"  ✖ turn failed: {e}", C.RED))


main.history = []

if __name__ == "__main__":
    main()
