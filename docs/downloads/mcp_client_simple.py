#!/usr/bin/env python3
"""
MCP Client — Simple Menu-Driven Client for SAP Integration Suite MCP Servers

Connects to the four Supplier Risk Intelligence MCP Servers configured in
mcp.json and lets you call common operations through a numbered menu.
No LLM or API key required.

Servers:
  • purchaseordermcp    — open POs, spend exposure by supplier
  • businesspartnermcp  — supplier master data and contact details
  • inbounddeliverymcp  — in-transit shipments and delivery status
  • materialstockmcp    — current warehouse stock levels by material

Usage:
    python3 mcp_client_simple.py

Requirements:
    Python 3.8+, stdlib only. mcp.json must be in the same directory.
    For the live flow visualization, flow_server.py must also be present
    (ships alongside this file). Set MCP_VIZ=0 to disable it.
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

# Optional live visualization — same flow_server used by mcp_agent.py.
# If the file isn't present or fails to import, viz calls are silent no-ops.
try:
    import flow_server as viz
except Exception:
    class _VizStub:
        def emit(self, *a, **k): pass   # no-op when viz not available
        def start(self, *a, **k): return None
    viz = _VizStub()


# ── Terminal colours ──────────────────────────────────────────────────────────

class C:
    R = "\033[0m"; B = "\033[1m"; DIM = "\033[2m"
    CYAN = "\033[36m"; GREEN = "\033[32m"; YELLOW = "\033[33m"
    RED = "\033[31m"; GREY = "\033[90m"; MAG = "\033[35m"; BLUE = "\033[34m"


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
        viz.emit("server_connecting", alias=self.alias, name=self.name, domain=self.domain)
        self.get_token(force=True)
        self.rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-client-simple", "version": "1.0"},
        })
        self.tools = self.rpc("tools/list").get("tools", [])
        viz.emit("server_online", alias=self.alias, name=self.name,
                 domain=self.domain, tool_count=len(self.tools))
        return self.tools

    def call_tool(self, tool_name, arguments, label=""):
        """Call a tool and emit viz events. Returns (text, is_error)."""
        viz.emit("direct_call", alias=self.alias, name=self.name,
                 tool=tool_name, args=json.dumps(arguments)[:120])
        print(clr(f"  ⚙  {self.name}", C.BLUE) + clr(f" → {tool_name}", C.B))
        result = self.rpc("tools/call", {"name": tool_name, "arguments": arguments})
        content = result.get("content", [])
        parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        text = "\n".join(parts)
        is_error = bool(result.get("isError"))
        viz.emit("tool_result", alias=self.alias, tool=tool_name,
                 ok=not is_error, size=len(text), direct=True)
        status = clr("ok", C.GREEN) if not is_error else clr("error", C.RED)
        print(clr(f"     ↳ {status}  {len(text)} chars", C.GREY))
        return text, is_error


# ── Result formatters ─────────────────────────────────────────────────────────

def fmt_po_list(text):
    try:
        data = json.loads(text)
        items = data.get("value", [])
        if not items:
            return "  No purchase orders found."
        lines = [clr(f"\n  {'PO Number':<16} {'Type':<8} {'Supplier':<14} {'Co.Code':<10} {'Currency'}", C.B)]
        lines.append("  " + "─" * 60)
        for po in items[:20]:
            lines.append(
                f"  {po.get('PurchaseOrder',''):<16} "
                f"{po.get('PurchaseOrderType',''):<8} "
                f"{po.get('Supplier',''):<14} "
                f"{po.get('CompanyCode',''):<10} "
                f"{po.get('DocumentCurrency','')}"
            )
        if len(items) > 20:
            lines.append(clr(f"  … and {len(items)-20} more", C.GREY))
        lines.append(clr(f"\n  Total: {len(items)} purchase orders", C.GREEN))
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_po_detail(text):
    try:
        data = json.loads(text)
        if "value" in data:
            data = data["value"][0] if data["value"] else {}
        if not data:
            return "  Purchase order not found."
        lines = [clr("\n  Purchase Order Details", C.B)]
        lines.append("  " + "─" * 48)
        for k in ["PurchaseOrder", "PurchaseOrderType", "Supplier", "CompanyCode",
                  "PurchasingOrganization", "PurchasingGroup",
                  "PurchaseOrderDate", "DocumentCurrency", "PaymentTerms"]:
            v = data.get(k)
            if v:
                lines.append(f"  {clr(k+':', C.GREY):<36} {v}")
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_supplier_list(text):
    try:
        data = json.loads(text)
        items = data.get("value", [])
        if not items:
            return "  No suppliers found."
        lines = [clr(f"\n  {'Supplier #':<14} {'Name':<36} {'Country'}", C.B)]
        lines.append("  " + "─" * 60)
        for bp in items[:20]:
            name = (bp.get("BusinessPartnerFullName")
                    or bp.get("BusinessPartnerName")
                    or bp.get("SearchTerm1", ""))
            country = bp.get("Country", bp.get("CountryOfOrigin", ""))
            lines.append(
                f"  {bp.get('BusinessPartner',''):<14} "
                f"{name[:35]:<36} "
                f"{country}"
            )
        if len(items) > 20:
            lines.append(clr(f"  … and {len(items)-20} more", C.GREY))
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_supplier_detail(text):
    try:
        data = json.loads(text)
        if "value" in data:
            data = data["value"][0] if data["value"] else {}
        if not data:
            return "  Supplier not found."
        lines = [clr("\n  Supplier / Business Partner Details", C.B)]
        lines.append("  " + "─" * 48)
        for k in ["BusinessPartner", "BusinessPartnerFullName", "BusinessPartnerName",
                  "BusinessPartnerType", "BusinessPartnerCategory",
                  "Country", "SearchTerm1", "CreationDate"]:
            v = data.get(k)
            if v:
                lines.append(f"  {clr(k+':', C.GREY):<44} {v}")
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_inbound_list(text):
    try:
        data = json.loads(text)
        items = data.get("value", [])
        if not items:
            return "  No inbound deliveries found."
        lines = [clr(f"\n  {'Delivery':<14} {'Type':<8} {'Supplier':<14} {'GR Date':<14} {'Ship.Point'}", C.B)]
        lines.append("  " + "─" * 66)
        for d in items[:20]:
            lines.append(
                f"  {d.get('InboundDelivery', d.get('DeliveryDocument','')):<14} "
                f"{d.get('DeliveryDocumentType',''):<8} "
                f"{d.get('Supplier',''):<14} "
                f"{str(d.get('PlannedGoodsReceiptDate', d.get('DeliveryDate','')))[:13]:<14} "
                f"{d.get('ShippingPoint','')}"
            )
        if len(items) > 20:
            lines.append(clr(f"  … and {len(items)-20} more", C.GREY))
        lines.append(clr(f"\n  Total: {len(items)} deliveries", C.GREEN))
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_inbound_detail(text):
    try:
        data = json.loads(text)
        if "value" in data:
            data = data["value"][0] if data["value"] else {}
        if not data:
            return "  Delivery not found."
        lines = [clr("\n  Inbound Delivery Details", C.B)]
        lines.append("  " + "─" * 48)
        for k in ["InboundDelivery", "DeliveryDocument", "DeliveryDocumentType",
                  "Supplier", "ShippingPoint", "PlannedGoodsReceiptDate",
                  "DeliveryDate", "TotalGrossWeight", "WeightUnit"]:
            v = data.get(k)
            if v:
                lines.append(f"  {clr(k+':', C.GREY):<44} {v}")
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_stock_list(text):
    try:
        data = json.loads(text)
        items = data.get("value", [])
        if not items:
            return "  No stock records found."
        lines = [clr(f"\n  {'Material':<16} {'Plant':<8} {'Storage Loc':<14} {'Qty':<14} {'Unit'}", C.B)]
        lines.append("  " + "─" * 60)
        for s in items[:20]:
            qty = (s.get("MatlWrhsStkQtyInMatBaseUnit")
                   or s.get("UnrestrictedStockQuantity")
                   or s.get("StockQuantity", ""))
            lines.append(
                f"  {s.get('Material',''):<16} "
                f"{s.get('Plant',''):<8} "
                f"{s.get('StorageLocation',''):<14} "
                f"{str(qty):<14} "
                f"{s.get('BaseUnit', s.get('MaterialBaseUnit',''))}"
            )
        if len(items) > 20:
            lines.append(clr(f"  … and {len(items)-20} more", C.GREY))
        lines.append(clr(f"\n  Total: {len(items)} stock records", C.GREEN))
        return "\n".join(lines)
    except Exception:
        return text[:2000]


def fmt_stock_detail(text):
    try:
        data = json.loads(text)
        if "value" in data:
            data = data["value"][0] if data["value"] else {}
        if not data:
            return "  No stock found for that material."
        lines = [clr("\n  Material Stock Details", C.B)]
        lines.append("  " + "─" * 48)
        for k in ["Material", "Plant", "StorageLocation",
                  "MatlWrhsStkQtyInMatBaseUnit", "UnrestrictedStockQuantity",
                  "StockQuantity", "BaseUnit", "MaterialBaseUnit"]:
            v = data.get(k)
            if v is not None and v != "":
                lines.append(f"  {clr(k+':', C.GREY):<48} {v}")
        return "\n".join(lines)
    except Exception:
        return text[:2000]


# ── Input helper ──────────────────────────────────────────────────────────────

def ask(prompt, default=""):
    val = input(clr(f"  {prompt} ", C.CYAN)).strip()
    return val or default


# ── Menu actions ──────────────────────────────────────────────────────────────

def action_list_po(servers):
    srv = servers.get("po")
    if not srv:
        print(clr("  ✖ purchaseordermcp not connected", C.RED)); return
    viz.emit("user_query", text="List all purchase orders")
    print(clr("  Fetching purchase orders…", C.DIM))
    text, err = srv.call_tool("get_PurchaseOrder", {})
    print(fmt_po_list(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
    viz.emit("turn_done")


def action_get_po(servers):
    srv = servers.get("po")
    if not srv:
        print(clr("  ✖ purchaseordermcp not connected", C.RED)); return
    po_id = ask("Purchase Order number:")
    if not po_id:
        return
    viz.emit("user_query", text=f"Get purchase order {po_id}")
    print(clr("  Fetching…", C.DIM))
    text, err = srv.call_tool("get_PurchaseOrder_PurchaseOrder",
                              {"PurchaseOrder": po_id})
    print(fmt_po_detail(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
    viz.emit("turn_done")


def action_list_suppliers(servers):
    srv = servers.get("bp")
    if not srv:
        print(clr("  ✖ businesspartnermcp not connected", C.RED)); return
    viz.emit("user_query", text="List all suppliers / business partners")
    print(clr("  Fetching suppliers…", C.DIM))
    text, err = srv.call_tool("get_BusinessPartner", {})
    print(fmt_supplier_list(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
    viz.emit("turn_done")


def action_get_supplier(servers):
    srv = servers.get("bp")
    if not srv:
        print(clr("  ✖ businesspartnermcp not connected", C.RED)); return
    num = ask("Supplier / Business Partner number (e.g. 17300001):")
    if not num:
        return
    viz.emit("user_query", text=f"Get supplier {num}")
    print(clr("  Fetching…", C.DIM))
    text, err = srv.call_tool("get_BusinessPartner_BusinessPartner",
                              {"BusinessPartner": num})
    print(fmt_supplier_detail(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
    viz.emit("turn_done")


def action_list_inbound(servers):
    srv = servers.get("inbound")
    if not srv:
        print(clr("  ✖ inbounddeliverymcp not connected", C.RED)); return
    viz.emit("user_query", text="List inbound deliveries in transit")
    print(clr("  Fetching inbound deliveries…", C.DIM))
    # Try common tool names; the actual name depends on what the server exposes
    for tool in ["get_InboundDelivery", "get_A_InbDeliveryHeader",
                 "get_InboundDeliveries", "get_A_InboundDelivery"]:
        if any(t["name"] == tool for t in srv.tools):
            text, err = srv.call_tool(tool, {})
            print(fmt_inbound_list(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
            break
    else:
        # Fallback: call the first available tool
        if srv.tools:
            first = srv.tools[0]["name"]
            print(clr(f"  Using tool: {first}", C.GREY))
            text, err = srv.call_tool(first, {})
            print(fmt_inbound_list(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
        else:
            print(clr("  No tools available on inbounddeliverymcp", C.RED))
    viz.emit("turn_done")


def action_get_inbound(servers):
    srv = servers.get("inbound")
    if not srv:
        print(clr("  ✖ inbounddeliverymcp not connected", C.RED)); return
    doc_id = ask("Inbound Delivery number:")
    if not doc_id:
        return
    viz.emit("user_query", text=f"Get inbound delivery {doc_id}")
    print(clr("  Fetching…", C.DIM))
    for tool in ["get_InboundDelivery_InboundDelivery",
                 "get_A_InbDeliveryHeader_DeliveryDocument"]:
        if any(t["name"] == tool for t in srv.tools):
            text, err = srv.call_tool(tool, {"InboundDelivery": doc_id,
                                             "DeliveryDocument": doc_id})
            print(fmt_inbound_detail(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
            break
    else:
        print(clr("  Could not find a single-delivery tool. Available tools:", C.YELLOW))
        for t in srv.tools[:6]:
            print(clr(f"    • {t['name']}", C.GREY))
    viz.emit("turn_done")


def action_list_stock(servers):
    srv = servers.get("stock")
    if not srv:
        print(clr("  ✖ materialstockmcp not connected", C.RED)); return
    viz.emit("user_query", text="List all material stock levels")
    print(clr("  Fetching stock records…", C.DIM))
    for tool in ["get_MaterialStock", "get_A_MatlStkInAcctMod",
                 "get_Stock", "get_MaterialStockInAccountingDocument"]:
        if any(t["name"] == tool for t in srv.tools):
            text, err = srv.call_tool(tool, {})
            print(fmt_stock_list(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
            break
    else:
        if srv.tools:
            first = srv.tools[0]["name"]
            print(clr(f"  Using tool: {first}", C.GREY))
            text, err = srv.call_tool(first, {})
            print(fmt_stock_list(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
        else:
            print(clr("  No tools available on materialstockmcp", C.RED))
    viz.emit("turn_done")


def action_get_stock(servers):
    srv = servers.get("stock")
    if not srv:
        print(clr("  ✖ materialstockmcp not connected", C.RED)); return
    mat = ask("Material number (e.g. TG0013):")
    if not mat:
        return
    viz.emit("user_query", text=f"Check stock for material {mat}")
    print(clr("  Fetching…", C.DIM))
    for tool in ["get_MaterialStock_Material", "get_A_MatlStkInAcctMod_Material"]:
        if any(t["name"] == tool for t in srv.tools):
            text, err = srv.call_tool(tool, {"Material": mat})
            print(fmt_stock_detail(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
            break
    else:
        # Fallback with filter on first list tool
        if srv.tools:
            first = srv.tools[0]["name"]
            text, err = srv.call_tool(first, {"$filter": f"Material eq '{mat}'"})
            print(fmt_stock_list(text) if not err else clr(f"  Error: {text[:200]}", C.RED))
        else:
            print(clr("  No tools available on materialstockmcp", C.RED))
    viz.emit("turn_done")


def action_list_tools(servers):
    """Show every tool available across all connected servers."""
    print()
    total = 0
    for alias, srv in servers.items():
        print(clr(f"  {srv.name}  ({len(srv.tools)} tools)", C.B))
        for t in srv.tools:
            desc = t.get("description", "")[:70]
            print(f"    {clr('•', C.CYAN)} {t['name']:<40} {clr(desc, C.GREY)}")
        total += len(srv.tools)
    print(clr(f"\n  Total: {total} tools across {len(servers)} servers", C.GREEN))


# ── Menu definition ───────────────────────────────────────────────────────────

MENU = [
    ("── Purchase Orders ────────────────────", None),
    ("List Purchase Orders",                   action_list_po),
    ("Get Purchase Order by ID",               action_get_po),
    ("── Suppliers / Business Partners ─────", None),
    ("List Suppliers",                          action_list_suppliers),
    ("Get Supplier by Number",                  action_get_supplier),
    ("── Inbound Deliveries ─────────────────", None),
    ("List Inbound Deliveries",                 action_list_inbound),
    ("Get Delivery by ID",                      action_get_inbound),
    ("── Material Stock ─────────────────────", None),
    ("Check Stock for a Material",              action_get_stock),
    ("List All Stock",                          action_list_stock),
    ("── Diagnostics ────────────────────────", None),
    ("Show all available tools",                action_list_tools),
]


def print_menu(servers):
    print()
    print(clr("  ╔══════════════════════════════════════════════════╗", C.CYAN))
    print(clr("  ║   SUPPLIER RISK — MCP Client (No LLM)           ║", C.CYAN))
    print(clr("  ║   SAP Integration Suite · Direct tool access    ║", C.CYAN))
    print(clr("  ╚══════════════════════════════════════════════════╝", C.CYAN))
    total_tools = sum(len(s.tools) for s in servers.values())
    connected = sum(1 for s in servers.values() if s.tools)
    print(clr(f"\n  {connected}/4 servers connected  ·  {total_tools} tools available\n", C.GREEN))
    idx = 1
    for label, fn in MENU:
        if fn is None:
            print(clr(f"  {label}", C.GREY))
        else:
            print(f"  {clr(str(idx), C.YELLOW)}  {label}")
            idx += 1
    print(f"\n  {clr('0', C.YELLOW)}  Exit")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(CONFIG_PATH):
        print(clr(f"✖ mcp.json not found at {CONFIG_PATH}", C.RED))
        print("  Create it from mcp.sample.json and fill in your credentials.")
        sys.exit(1)

    # Start live flow visualization unless disabled (MCP_VIZ=0)
    if os.environ.get("MCP_VIZ", "1").lower() not in ("0", "false", "no"):
        url = viz.start(port=8901, open_browser=True)
        if url:
            print(clr(f"\n  ◆ Live flow visualization: {url}", C.MAG))

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    all_servers = [MCPServer(s) for s in cfg["servers"]]
    servers = {}

    print(clr("\n  Connecting to MCP Servers…", C.DIM))
    viz.emit("boot_start", servers=len(all_servers))

    for srv in all_servers:
        try:
            srv.connect()
            servers[srv.alias] = srv
            print(f"  {clr('●', C.GREEN)} {srv.name:<26} {clr('ONLINE', C.GREEN)}  "
                  f"{clr(str(len(srv.tools))+' tools', C.YELLOW)}")
            preview = ", ".join(t["name"] for t in srv.tools[:3])
            if len(srv.tools) > 3:
                preview += f", +{len(srv.tools)-3} more"
            print(f"      {clr('↳ '+preview, C.GREY)}")
        except Exception as e:
            viz.emit("server_offline", alias=srv.alias, name=srv.name, error=str(e)[:80])
            print(f"  {clr('●', C.RED)} {srv.name:<26} {clr('OFFLINE', C.RED)}  {str(e)[:60]}")

    total_tools = sum(len(s.tools) for s in servers.values())
    viz.emit("boot_complete", servers=len(servers), total_tools=total_tools, model="none")
    viz.emit("menu_ready")

    print(clr(f"\n  {len(servers)}/4 servers online · {total_tools} tools ready.", C.GREEN))
    print(clr("  Hint: supplier 17300001 appears across all four systems.", C.GREY))

    # Build ordered action list (skip header rows)
    actions = [fn for _, fn in MENU if fn is not None]

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
                print()
                try:
                    actions[idx](servers)
                except Exception as e:
                    viz.emit("turn_done")
                    print(clr(f"  ✖ Error: {e}", C.RED))
                input(clr("\n  Press Enter to continue…", C.DIM))
            else:
                print(clr("  Invalid selection.", C.YELLOW))
        except ValueError:
            print(clr("  Please enter a number.", C.YELLOW))


if __name__ == "__main__":
    main()
