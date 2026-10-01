#!/usr/bin/env python3
"""
MCP Client — Simple Menu-Driven Client for SAP Integration Suite MCP Servers

Connects to the four MCP Servers configured in mcp.json and lets you call
common operations through a numbered menu. No LLM or API key required.

Usage:
    python3 mcp_client_simple.py

Requirements:
    Python 3.8+, stdlib only. mcp.json must be in the same directory.
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


# ── Terminal colours ──────────────────────────────────────────────────────────

class C:
    R = "\033[0m"; B = "\033[1m"; DIM = "\033[2m"
    CYAN = "\033[36m"; GREEN = "\033[32m"; YELLOW = "\033[33m"
    RED = "\033[31m"; GREY = "\033[90m"; MAG = "\033[35m"


def clr(text, color):
    return f"{color}{text}{C.R}"


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def http_post(url, data, headers, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    return urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)


def parse_mcp_response(raw, content_type):
    text = raw.decode("utf-8", errors="replace").strip()
    if ("text/event-stream" in (content_type or "")
            or text.startswith("event:")
            or text.startswith("data:")):
        payload = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                payload = line[5:].strip()
        if payload:
            return json.loads(payload)
        raise ValueError("No data in SSE stream")
    return json.loads(text)


# ── MCP Server ────────────────────────────────────────────────────────────────

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

    def get_token(self, force=False):
        if not force and self._token and time.time() < self._token_exp - 60:
            return self._token
        body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        resp = http_post(self.token_url, body, {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }, timeout=30)
        data = json.load(resp)
        self._token = data["access_token"]
        self._token_exp = time.time() + int(data.get("expires_in", 3600))
        return self._token

    def rpc(self, method, params=None, retry_auth=True):
        self._rpc_id += 1
        body = json.dumps({
            "jsonrpc": "2.0", "id": self._rpc_id,
            "method": method, "params": params or {},
        }).encode()
        headers = {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
            "Accept": MCP_ACCEPT,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
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
        out = parse_mcp_response(resp.read(), resp.headers.get("Content-Type"))
        if isinstance(out, dict) and out.get("error"):
            raise RuntimeError(f"{self.name} RPC error: {out['error']}")
        return out.get("result", {})

    def connect(self):
        self.get_token(force=True)
        self.rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-client-simple", "version": "1.0"},
        })
        self.tools = self.rpc("tools/list").get("tools", [])
        return self.tools

    def call_tool(self, tool_name, arguments):
        result = self.rpc("tools/call", {"name": tool_name, "arguments": arguments})
        content = result.get("content", [])
        parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        text = "\n".join(parts)
        is_error = bool(result.get("isError"))
        return text, is_error


# ── Result formatters ─────────────────────────────────────────────────────────

def fmt_po_list(text):
    try:
        data = json.loads(text)
        items = data.get("value", [])
        if not items:
            return "No purchase orders found."
        lines = [clr(f"\n  {'PO Number':<16} {'Type':<6} {'Supplier':<12} {'CompCode':<10} {'Currency'}", C.B)]
        lines.append("  " + "─" * 58)
        for po in items[:20]:
            lines.append(
                f"  {po.get('PurchaseOrder',''):<16} "
                f"{po.get('PurchaseOrderType',''):<6} "
                f"{po.get('Supplier',''):<12} "
                f"{po.get('CompanyCode',''):<10} "
                f"{po.get('DocumentCurrency','')}"
            )
        if len(items) > 20:
            lines.append(f"  ... and {len(items)-20} more")
        lines.append(f"\n  Total: {len(items)} purchase orders")
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_po_detail(text):
    try:
        data = json.loads(text)
        if "value" in data:
            data = data["value"][0] if data["value"] else {}
        if not data:
            return "Purchase order not found."
        lines = [clr("\n  Purchase Order Details", C.B)]
        for k in ["PurchaseOrder", "PurchaseOrderType", "Supplier", "CompanyCode",
                  "PurchasingOrganization", "PurchaseOrderDate", "DocumentCurrency",
                  "PaymentTerms", "PurchasingGroup"]:
            v = data.get(k)
            if v:
                lines.append(f"  {k:<28} {v}")
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_customers(text):
    try:
        data = json.loads(text)
        items = data.get("value", [])
        if not items:
            return "No customers found."
        lines = [clr(f"\n  {'Customer #':<14} {'Name':<30} {'Type'}", C.B)]
        lines.append("  " + "─" * 54)
        for c in items[:20]:
            name = c.get("fullName") or c.get("formattedName") or c.get("firstName", "") + " " + c.get("lastName", "")
            ctype = "Corporate" if c.get("isCompany") else "Individual"
            lines.append(f"  {c.get('customerNumber',''):<14} {name.strip():<30} {ctype}")
        if len(items) > 20:
            lines.append(f"  ... and {len(items)-20} more")
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_customer_detail(text):
    try:
        data = json.loads(text)
        if "value" in data:
            data = data["value"][0] if data["value"] else {}
        if not data:
            return "Customer not found."
        lines = [clr("\n  Customer Details", C.B)]
        for k in ["customerNumber", "fullName", "formattedName", "firstName", "lastName",
                  "isCompany", "createdAt"]:
            v = data.get(k)
            if v is not None:
                lines.append(f"  {k:<24} {v}")
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_spotify_search(text):
    try:
        data = json.loads(text)
        lines = []
        for stype in ["artists", "albums", "tracks"]:
            bucket = data.get(stype, {}).get("items", [])
            if not bucket:
                continue
            lines.append(clr(f"\n  {stype.capitalize()}", C.B))
            lines.append("  " + "─" * 50)
            for item in bucket[:5]:
                name = item.get("name", "")
                iid = item.get("id", "")
                extra = ""
                if stype == "artists":
                    extra = f"  followers: {item.get('followers',{}).get('total',0):,}"
                elif stype == "albums":
                    extra = f"  {item.get('release_date','')}"
                elif stype == "tracks":
                    artists = ", ".join(a["name"] for a in item.get("artists", []))
                    extra = f"  by {artists}"
                lines.append(f"  {name:<36} id: {iid}{extra}")
        return "\n".join(lines) if lines else "No results found."
    except Exception:
        return text[:2000]


def fmt_email_sent(text):
    try:
        data = json.loads(text)
        op_id = data.get("operationId") or data.get("code", "")
        if op_id:
            return clr(f"\n  ✅ Email queued  |  operation ID: {op_id}", C.GREEN)
        return text[:500]
    except Exception:
        return text[:500]


# ── Menu actions ──────────────────────────────────────────────────────────────

def ask(prompt, default=""):
    val = input(clr(f"  {prompt}", C.CYAN) + " ").strip()
    return val or default


def action_list_po(servers):
    srv = servers.get("po")
    if not srv:
        print(clr("  ✖ purchaseordermcp not connected", C.RED))
        return
    print(clr("  Fetching purchase orders...", C.DIM))
    text, err = srv.call_tool("get_PurchaseOrder", {})
    print(fmt_po_list(text) if not err else clr(f"  Error: {text[:200]}", C.RED))


def action_get_po(servers):
    srv = servers.get("po")
    if not srv:
        print(clr("  ✖ purchaseordermcp not connected", C.RED))
        return
    po_id = ask("Purchase Order number:")
    if not po_id:
        return
    print(clr("  Fetching...", C.DIM))
    text, err = srv.call_tool("get_PurchaseOrder_PurchaseOrder", {"PurchaseOrder": po_id})
    print(fmt_po_detail(text) if not err else clr(f"  Error: {text[:200]}", C.RED))


def action_list_customers(servers):
    srv = servers.get("bp")
    if not srv:
        print(clr("  ✖ businesspartnermcp not connected", C.RED))
        return
    print(clr("  Fetching customers...", C.DIM))
    text, err = srv.call_tool("get_customers", {})
    print(fmt_customers(text) if not err else clr(f"  Error: {text[:200]}", C.RED))


def action_get_customer(servers):
    srv = servers.get("bp")
    if not srv:
        print(clr("  ✖ businesspartnermcp not connected", C.RED))
        return
    num = ask("Customer number:")
    if not num:
        return
    print(clr("  Fetching...", C.DIM))
    text, err = srv.call_tool("get_customers_customerNumber", {"customerNumber": num})
    print(fmt_customer_detail(text) if not err else clr(f"  Error: {text[:200]}", C.RED))


def action_search_spotify(servers):
    srv = servers.get("spotify")
    if not srv:
        print(clr("  ✖ spotifymcp not connected", C.RED))
        return
    query = ask("Search query (e.g. 'Coldplay'):")
    if not query:
        return
    stype = ask("Type [artist/album/track] (default: artist):") or "artist"
    print(clr("  Searching...", C.DIM))
    text, err = srv.call_tool("get_search", {"q": query, "type": [stype], "limit": 5})
    print(fmt_spotify_search(text) if not err else clr(f"  Error: {text[:200]}", C.RED))


def action_send_email(servers):
    srv = servers.get("email")
    if not srv:
        print(clr("  ✖ emailmcp not connected", C.RED))
        return
    to_addr = ask("Recipient email:")
    if not to_addr:
        return
    subject = ask("Subject:") or "Message from MCP Client"
    body = ask("Message body (plain text):") or "This message was sent via SAP Integration Suite MCP Gateway."
    from_sid = ask("Twilio sender address (YOURSID@twilio.email):")
    if not from_sid:
        print(clr("  ✖ Sender address is required", C.RED))
        return
    print(clr("  Sending...", C.DIM))
    args = {
        "requestBody": {
            "from": {"address": from_sid},
            "to": [{"address": to_addr}],
            "content": {
                "subject": subject,
                "html": f"<p>{body}</p>",
            },
        }
    }
    text, err = srv.call_tool("post_Emails", args)
    print(fmt_email_sent(text) if not err else clr(f"  Error: {text[:200]}", C.RED))


# ── Main ──────────────────────────────────────────────────────────────────────

MENU = [
    ("── Purchase Orders ─────────────────────", None, None),
    ("List Purchase Orders",        "po",       action_list_po),
    ("Get Purchase Order by ID",    "po",       action_get_po),
    ("── Business Partners ──────────────────", None, None),
    ("List Customers",              "bp",       action_list_customers),
    ("Get Customer by Number",      "bp",       action_get_customer),
    ("── Spotify ────────────────────────────", None, None),
    ("Search Spotify",              "spotify",  action_search_spotify),
    ("── Email ──────────────────────────────", None, None),
    ("Send Email",                  "email",    action_send_email),
]


def print_menu(servers):
    print()
    print(clr("  ╔══════════════════════════════════════════╗", C.CYAN))
    print(clr("  ║   MCP CLIENT — SAP Integration Suite     ║", C.CYAN))
    print(clr("  ╚══════════════════════════════════════════╝", C.CYAN))
    total_tools = sum(len(s.tools) for s in servers.values())
    connected = sum(1 for s in servers.values() if s.tools)
    print(clr(f"\n  {connected} servers connected  |  {total_tools} tools available\n", C.GREEN))
    idx = 1
    for label, alias, fn in MENU:
        if fn is None:
            print(clr(f"  {label}", C.GREY))
        else:
            status = ""
            if alias and alias not in servers:
                status = clr(" (offline)", C.RED)
            print(f"  {clr(str(idx), C.YELLOW)}  {label}{status}")
            idx += 1
    print(f"\n  {clr('0', C.YELLOW)}  Exit")
    print()


def main():
    if not os.path.exists(CONFIG_PATH):
        print(clr(f"✖ mcp.json not found at {CONFIG_PATH}", C.RED))
        print("  Create it from mcp.sample.json and fill in your credentials.")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    all_servers = [MCPServer(s) for s in cfg["servers"]]
    servers = {}

    print(clr("\n  Connecting to MCP Servers...", C.DIM))
    for srv in all_servers:
        try:
            srv.connect()
            servers[srv.alias] = srv
            print(f"  {clr('●', C.GREEN)} {srv.name:<24} {clr('ONLINE', C.GREEN)}  "
                  f"{clr(str(len(srv.tools))+' tools', C.YELLOW)}")
        except Exception as e:
            print(f"  {clr('●', C.RED)} {srv.name:<24} {clr('OFFLINE', C.RED)}  {str(e)[:60]}")

    # Build action list (numbered, skipping headers)
    actions = [(fn, alias) for _, alias, fn in MENU if fn is not None]

    while True:
        print_menu(servers)
        try:
            choice = input(clr("  Select › ", C.CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print(clr("\n  Goodbye.\n", C.DIM))
            break
        if choice == "0":
            print(clr("\n  Goodbye.\n", C.DIM))
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(actions):
                fn, _ = actions[idx]
                fn(servers)
                input(clr("\n  Press Enter to continue...", C.DIM))
            else:
                print(clr("  Invalid selection.", C.YELLOW))
        except ValueError:
            print(clr("  Please enter a number.", C.YELLOW))


if __name__ == "__main__":
    main()
