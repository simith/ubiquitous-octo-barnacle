#!/usr/bin/env python3
"""
flow_server.py — a zero-dependency live visualization for mcp_agent.py.

Runs a tiny threaded HTTP server that serves a single animated page and an
SSE (Server-Sent Events) stream. The agent calls emit(event, **data) at each
step of its flow; the browser animates packets travelling between:

    You  →  MCP Client  →  LLM (reasoning)
                 │
                 └──→  SAP IS MCP Gateway (JWT · Policy · Audit)  →  4 MCP Servers

Stdlib only. If the server is never started, emit() is a harmless no-op, so
the agent runs identically with or without the UI.
"""

import json
import threading
import time
import queue
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_clients = []                 # list of queue.Queue, one per connected browser
_clients_lock = threading.Lock()
_replay = []                  # sticky events so late-joining browsers see state
_replay_lock = threading.Lock()
_enabled = False
_STICKY = {"boot_start", "server_connecting", "server_online",
           "server_offline", "boot_complete"}


def _record_replay(event, msg):
    with _replay_lock:
        if event == "boot_start":
            _replay.clear()
        if event in _STICKY:
            _replay.append(msg)
            if len(_replay) > 60:
                del _replay[0]


def emit(event, **data):
    """Broadcast one event to all connected browsers. No-op if UI not started."""
    if not _enabled:
        return
    msg = {"event": event, "data": data, "ts": time.time()}
    _record_replay(event, msg)
    payload = "data: " + json.dumps(msg) + "\n\n"
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait(payload)
            except Exception:
                dead.append(q)
        for q in dead:
            if q in _clients:
                _clients.remove(q)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silence request logging

    def do_GET(self):
        if self.path.startswith("/events"):
            self._stream()
        else:
            self._page()

    def _page(self):
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = queue.Queue(maxsize=1000)
        with _clients_lock:
            _clients.append(q)
        # replay sticky state to the newcomer (flagged so it skips animation)
        with _replay_lock:
            backlog = list(_replay)
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            for msg in backlog:
                rep = dict(msg)
                rep["replay"] = True
                self.wfile.write(("data: " + json.dumps(rep) + "\n\n").encode())
            self.wfile.flush()
            while True:
                try:
                    payload = q.get(timeout=15)
                    self.wfile.write(payload.encode())
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")  # heartbeat
                    self.wfile.flush()
        except OSError:
            pass
        finally:
            with _clients_lock:
                if q in _clients:
                    _clients.remove(q)


def start(port=8900, open_browser=True):
    """Start the viz server in a daemon thread. Returns the URL, or None."""
    global _enabled
    last_err = None
    for p in range(port, port + 12):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", p), _Handler)
        except OSError as e:
            last_err = e
            continue
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        _enabled = True
        url = f"http://127.0.0.1:{p}/"
        if open_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        return url
    print(f"[flow_server] could not bind a port: {last_err}")
    return None


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Supplier Risk Intelligence — Live MCP Flow</title>
<style>
  :root{
    --bg0:#070b16; --bg1:#0c1427; --line:#1d2b47; --line2:#28406b;
    --ink:#e9f0ff; --dim:#8da2c7; --mut:#5f719a;
    --sap:#1b90ff; --sapg:#4db1ff; --gold:#f0b429; --grn:#2ee6a6;
    --red:#ff5d6c; --vio:#b388ff; --cyan:#2fe0e0;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{
    background:radial-gradient(1200px 700px at 60% -10%, #10203f 0%, var(--bg1) 45%, var(--bg0) 100%);
    color:var(--ink); font:14px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif;
    overflow:hidden; height:100vh;
  }
  header{
    display:flex; align-items:center; gap:16px; padding:14px 22px;
    border-bottom:1px solid var(--line); background:rgba(8,13,25,.6); backdrop-filter:blur(6px);
  }
  header .logo{
    width:30px;height:30px;border-radius:7px;
    background:linear-gradient(135deg,var(--sap),#0a63c9);
    box-shadow:0 0 18px rgba(27,144,255,.6); flex:0 0 auto;
  }
  header h1{font-size:16px;margin:0;font-weight:650;letter-spacing:.3px}
  header .sub{color:var(--mut);font-size:12px;margin-top:1px}
  header .status{margin-left:auto;display:flex;gap:22px;align-items:center}
  .stat{text-align:right}
  .stat b{display:block;font-size:18px;font-weight:700}
  .stat span{font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:1px}
  .activity{
    display:flex;align-items:center;gap:9px;padding:6px 14px;border-radius:20px;
    background:rgba(27,144,255,.1);border:1px solid var(--line2);min-width:230px;
  }
  .activity .pulse{width:9px;height:9px;border-radius:50%;background:var(--mut);flex:0 0 auto}
  .activity.live .pulse{background:var(--grn);box-shadow:0 0 12px var(--grn);animation:bp 1s infinite}
  @keyframes bp{0%,100%{opacity:1}50%{opacity:.35}}
  .activity span{font-size:12.5px;color:var(--dim)}

  .wrap{display:flex;height:calc(100vh - 61px)}
  #stage{position:relative;flex:1;overflow:hidden}
  svg.edges{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}

  .node{
    position:absolute;transform:translate(-50%,-50%);
    width:168px;padding:13px 15px;border-radius:13px;
    background:linear-gradient(180deg,#111c33,#0c1526);
    border:1px solid var(--line2);
    box-shadow:0 8px 30px rgba(0,0,0,.45);
    transition:border-color .25s, box-shadow .25s, transform .15s;
    z-index:3;
  }
  .node .t{font-weight:650;font-size:13px;display:flex;align-items:center;gap:8px}
  .node .d{font-size:11px;color:var(--mut);margin-top:3px}
  .node .meta{font-size:11px;color:var(--sapg);margin-top:7px;font-weight:600;min-height:14px}
  /* live in-block status narration */
  .st{font-size:11px;margin-top:8px;min-height:16px;display:flex;align-items:center;gap:6px;
      color:var(--dim);transition:color .2s}
  .st.on{color:var(--gold);font-weight:600}
  .st.ok{color:var(--grn);font-weight:600}
  .st .dots{display:none}
  .st.on .dots{display:inline-flex;gap:3px;flex:0 0 auto}
  .st .dots i{width:4px;height:4px;border-radius:50%;background:currentColor;animation:blink 1.1s infinite}
  .st .dots i:nth-child(2){animation-delay:.18s}
  .st .dots i:nth-child(3){animation-delay:.36s}
  @keyframes blink{0%,80%,100%{opacity:.25}40%{opacity:1}}
  .node .dot{width:9px;height:9px;border-radius:50%;background:var(--mut);flex:0 0 auto}
  .node.on{border-color:var(--grn);box-shadow:0 0 26px rgba(46,230,166,.28)}
  .node.on .dot{background:var(--grn);box-shadow:0 0 10px var(--grn)}
  .node.connecting{border-color:var(--gold)}
  .node.connecting .dot{background:var(--gold);box-shadow:0 0 10px var(--gold);animation:bp 1s infinite}
  .node.off{border-color:var(--red)}
  .node.off .dot{background:var(--red);box-shadow:0 0 10px var(--red)}
  .node.active{transform:translate(-50%,-50%) scale(1.05);border-color:var(--sapg);
    box-shadow:0 0 34px rgba(27,144,255,.5)}
  .node .ic{font-size:15px}

  /* special nodes */
  #node-user{width:120px;background:linear-gradient(180deg,#141c30,#0d1424)}
  #node-llm{width:180px;border-color:#3a2e63;background:linear-gradient(180deg,#1a1430,#120d24)}
  #node-llm .t .ic{color:var(--vio)}
  #node-llm.active{border-color:var(--vio);box-shadow:0 0 34px rgba(179,136,255,.5)}
  #node-gateway{
    width:210px;padding:16px;border-color:var(--sap);
    background:linear-gradient(180deg,#10213f,#0a1830);
    box-shadow:0 0 34px rgba(27,144,255,.25);
  }
  #node-gateway .t{font-size:13.5px}
  .gov{display:flex;gap:6px;margin-top:11px}
  .chip{
    flex:1;text-align:center;font-size:9.5px;letter-spacing:.4px;text-transform:uppercase;
    padding:5px 3px;border-radius:7px;border:1px solid var(--line2);color:var(--mut);
    background:rgba(255,255,255,.02);transition:all .2s;font-weight:700;
  }
  .chip.lit{color:#06240f;background:var(--grn);border-color:var(--grn);box-shadow:0 0 14px rgba(46,230,166,.6)}
  #node-gateway.active{box-shadow:0 0 46px rgba(27,144,255,.65);border-color:var(--sapg)}
  .shield{font-size:15px;color:var(--sapg)}

  .backend{
    position:absolute;transform:translate(-50%,-50%);font-size:10px;color:var(--mut);
    z-index:2;white-space:nowrap;pointer-events:none;
  }

  /* packets */
  .pk{position:absolute;left:0;top:0;z-index:6;pointer-events:none;will-change:transform}
  .pk .core{
    width:13px;height:13px;border-radius:50%;transform:translate(-50%,-50%);
    box-shadow:0 0 16px 4px currentColor;
  }
  .pk .lbl{
    position:absolute;left:50%;top:-20px;transform:translateX(-50%);
    font-size:10.5px;font-weight:650;white-space:nowrap;color:var(--ink);
    background:rgba(8,13,25,.9);border:1px solid var(--line2);
    padding:2px 8px;border-radius:10px;
  }

  /* side log */
  #log{
    width:360px;flex:0 0 360px;border-left:1px solid var(--line);
    background:rgba(8,12,22,.55);display:flex;flex-direction:column;
  }
  #log h2{margin:0;padding:13px 18px;font-size:12px;letter-spacing:1.2px;
    text-transform:uppercase;color:var(--dim);border-bottom:1px solid var(--line)}
  #logbody{overflow-y:auto;padding:8px 12px;flex:1}
  .ev{display:flex;gap:9px;padding:6px 6px;border-radius:8px;font-size:12px;animation:fade .3s}
  @keyframes fade{from{opacity:0;transform:translateY(-4px)}to{opacity:1}}
  .ev .tag{flex:0 0 auto;font-size:9px;font-weight:800;letter-spacing:.5px;padding:2px 7px;
    border-radius:6px;height:fit-content;margin-top:1px}
  .ev .msg{color:var(--dim)}
  .ev .msg b{color:var(--ink);font-weight:600}
  .t-sys{background:#15325c;color:var(--sapg)}
  .t-llm{background:#2a1f52;color:var(--vio)}
  .t-tool{background:#123b2c;color:var(--grn)}
  .t-user{background:#3a3410;color:var(--gold)}
  .t-err{background:#45141a;color:var(--red)}
  .answer{
    margin:8px 10px;padding:11px 13px;border-radius:11px;border:1px solid var(--line2);
    background:rgba(27,144,255,.08);font-size:12.5px;color:var(--ink);animation:fade .3s;
  }
  .answer .h{font-size:10px;color:var(--sapg);text-transform:uppercase;letter-spacing:1px;margin-bottom:5px;font-weight:700}
  .hint{color:var(--mut);font-size:11.5px;padding:14px 18px;text-align:center}
</style>
</head>
<body>
<header>
  <div class="logo"></div>
  <div>
    <h1>Supplier Risk Intelligence</h1>
    <div class="sub">Live MCP flow · SAP Integration Suite Gateway</div>
  </div>
  <div class="status">
    <div class="activity" id="activity"><span class="pulse"></span><span id="act-text">Waiting for agent…</span></div>
    <div class="stat"><b id="st-servers">0</b><span>Servers</span></div>
    <div class="stat"><b id="st-tools">0</b><span>Tools</span></div>
    <div class="stat"><b id="st-calls">0</b><span>Tool calls</span></div>
  </div>
</header>

<div class="wrap">
  <div id="stage">
    <svg class="edges" id="edges"></svg>

    <div class="node" id="node-user">
      <div class="t"><span class="dot"></span><span class="ic">🧑‍💼</span> You</div>
      <div class="d">Business user</div>
      <div class="st" id="st-user"><span class="dots"><i></i><i></i><i></i></span><span class="txt"></span></div>
    </div>

    <div class="node" id="node-llm">
      <div class="t"><span class="dot"></span><span class="ic">🧠</span> LLM Reasoning</div>
      <div class="d" id="llm-model">Claude · the brain</div>
      <div class="st" id="st-llm"><span class="dots"><i></i><i></i><i></i></span><span class="txt">waiting</span></div>
    </div>

    <div class="node" id="node-client">
      <div class="t"><span class="dot"></span><span class="ic">🖥️</span> MCP Client</div>
      <div class="d">mcp_agent.py</div>
      <div class="st" id="st-client"><span class="dots"><i></i><i></i><i></i></span><span class="txt">idle</span></div>
    </div>

    <div class="node" id="node-gateway">
      <div class="t"><span class="shield">🛡️</span> SAP IS MCP Gateway</div>
      <div class="d">JSON-RPC · OAuth2 · routing</div>
      <div class="gov">
        <div class="chip" id="chip-jwt">JWT</div>
        <div class="chip" id="chip-pol">Policy</div>
        <div class="chip" id="chip-aud">Audit</div>
      </div>
      <div class="st" id="st-gateway"><span class="dots"><i></i><i></i><i></i></span><span class="txt">standing by</span></div>
    </div>
  </div>

  <div id="log">
    <h2>Live Event Stream</h2>
    <div id="logbody">
      <div class="hint">Open the CLI, type <b>start</b>, then ask a question.<br>Events will stream here in real time.</div>
    </div>
  </div>
</div>

<script>
const stage = document.getElementById('stage');
const edgesSvg = document.getElementById('edges');
const logBody = document.getElementById('logbody');
const nodes = {
  user: document.getElementById('node-user'),
  client: document.getElementById('node-client'),
  llm: document.getElementById('node-llm'),
  gateway: document.getElementById('node-gateway'),
};
const serverNodes = {};   // alias -> {node, backend}
let edges = [];           // [fromId, toId]
let callCount = 0, toolTotal = 0, serverCount = 0;
let pendingResults = false, hintCleared = false;

const BACKENDS = {
  po:"SAP S/4HANA · Purchase Orders",
  bp:"SAP S/4HANA · Business Partners",
  inbound:"SAP S/4HANA · Inbound Deliveries",
  stock:"SAP S/4HANA · Material Stock",
};
const PALETTE = ['#2ee6a6','#f0b429','#2fe0e0','#b388ff','#ff8a5d','#5d9bff'];

function layout(){
  // fixed nodes (percentages of stage)
  place(nodes.user,    6, 50);
  place(nodes.client, 27, 54);
  place(nodes.llm,    27, 20);
  place(nodes.gateway,52, 54);
  const aliases = Object.keys(serverNodes);
  const n = aliases.length || 1;
  aliases.forEach((a,i)=>{
    const top = n===1 ? 50 : 14 + (72*i/(n-1));
    place(serverNodes[a].node, 82, top);
    place(serverNodes[a].backend, 82, top+8.5);
  });
  drawEdges();
}
function place(el, xPct, yPct){ el.style.left=xPct+'%'; el.style.top=yPct+'%'; }

function center(el){
  const s = stage.getBoundingClientRect(), r = el.getBoundingClientRect();
  return {x: r.left - s.left + r.width/2, y: r.top - s.top + r.height/2};
}
function node(id){ return nodes[id] || (serverNodes[id] && serverNodes[id].node); }

function drawEdges(){
  edges = [['user','client'],['client','llm'],['client','gateway']];
  Object.keys(serverNodes).forEach(a=>edges.push(['gateway',a]));
  edgesSvg.innerHTML = '';
  for(const [f,t] of edges){
    const a=node(f), b=node(t); if(!a||!b) continue;
    const p=center(a), q=center(b);
    const ln=document.createElementNS('http://www.w3.org/2000/svg','line');
    ln.setAttribute('x1',p.x); ln.setAttribute('y1',p.y);
    ln.setAttribute('x2',q.x); ln.setAttribute('y2',q.y);
    ln.setAttribute('stroke','#28406b'); ln.setAttribute('stroke-width','2');
    ln.setAttribute('stroke-linecap','round');
    edgesSvg.appendChild(ln);
  }
}

function ensureServer(alias, name, domain){
  if(serverNodes[alias]) return;
  const el = document.createElement('div');
  el.className='node'; el.id='node-'+alias;
  el.innerHTML = `<div class="t"><span class="dot"></span><span class="ic">🧩</span> ${name||alias}</div>
                  <div class="d">${domain||''}</div>
                  <div class="st" id="st-srv-${alias}"><span class="dots"><i></i><i></i><i></i></span><span class="txt"></span></div>`;
  stage.appendChild(el);
  const be = document.createElement('div');
  be.className='backend'; be.textContent = BACKENDS[alias] || 'Backend';
  stage.appendChild(be);
  serverNodes[alias] = {node:el, backend:be, tools:0};
  layout();
}

const easing = t => t<.5 ? 4*t*t*t : 1-Math.pow(-2*t+2,3)/2;

function packet(pathIds, opts){
  opts = opts||{};
  const pts = pathIds.map(id=>{ const el=node(id); return el?center(el):null; }).filter(Boolean);
  if(pts.length<2){ opts.onDone&&opts.onDone(); return; }
  const color = opts.color||'#2fe0e0';
  const pk = document.createElement('div'); pk.className='pk';
  pk.innerHTML = `<div class="core" style="color:${color};background:${color}"></div>`+
                 (opts.label?`<div class="lbl">${opts.label}</div>`:'');
  stage.appendChild(pk);
  const dur = opts.dur||680;
  let seg=0;
  function run(){
    if(seg>=pts.length-1){ pk.remove(); opts.onDone&&opts.onDone(); return; }
    const a=pts[seg], b=pts[seg+1], t0=performance.now();
    function frame(now){
      let t=Math.min(1,(now-t0)/dur), e=easing(t);
      pk.style.transform=`translate(${a.x+(b.x-a.x)*e}px,${a.y+(b.y-a.y)*e}px)`;
      if(t<1){ requestAnimationFrame(frame); }
      else {
        if(pathIds[seg+1]==='gateway' || pathIds[seg]==='gateway') flashGateway();
        seg++; run();
      }
    }
    requestAnimationFrame(frame);
  }
  run();
}

function flashGateway(){
  nodes.gateway.classList.add('active');
  const chips=['chip-jwt','chip-pol','chip-aud'];
  chips.forEach((id,i)=>setTimeout(()=>{
    document.getElementById(id).classList.add('lit');
    setTimeout(()=>document.getElementById(id).classList.remove('lit'),520);
  }, i*120));
  clearTimeout(flashGateway._t);
  flashGateway._t=setTimeout(()=>nodes.gateway.classList.remove('active'),700);
}

function activate(id, on){
  const el=node(id); if(el) el.classList.toggle('active', on!==false);
}
function deactivateAll(){
  Object.values(nodes).forEach(n=>n.classList.remove('active'));
  Object.values(serverNodes).forEach(s=>s.node.classList.remove('active'));
}

// live in-block narration. key ∈ {user,client,llm,gateway} or a server alias.
// mode: 'busy' (amber + animated dots), 'ok' (green), '' (neutral/idle)
function status(key, text, mode){
  const id = serverNodes[key] ? 'st-srv-'+key : 'st-'+key;
  const el = document.getElementById(id);
  if(!el) return;
  const txt = el.querySelector('.txt');
  if(txt) txt.textContent = text; else el.textContent = text;
  el.classList.toggle('on', mode==='busy');
  el.classList.toggle('ok', mode==='ok');
}
function idleStatuses(){
  status('user','', '');
  status('client','idle','');
  status('llm','waiting','');
  status('gateway','standing by','');
  Object.keys(serverNodes).forEach(a=>status(a, serverNodes[a].tools+' tools ready',''));
}

function setActivity(txt, live){
  document.getElementById('act-text').textContent = txt;
  document.getElementById('activity').classList.toggle('live', !!live);
}
function log(tag, cls, html){
  if(!hintCleared){ logBody.innerHTML=''; hintCleared=true; }
  const d=document.createElement('div'); d.className='ev';
  d.innerHTML=`<span class="tag ${cls}">${tag}</span><span class="msg">${html}</span>`;
  logBody.insertBefore(d, logBody.firstChild);
  while(logBody.children.length>90) logBody.removeChild(logBody.lastChild);
}
function answer(text){
  if(!hintCleared){ logBody.innerHTML=''; hintCleared=true; }
  const d=document.createElement('div'); d.className='answer';
  d.innerHTML=`<div class="h">◆ Agent response</div>${text}`;
  logBody.insertBefore(d, logBody.firstChild);
}
function colorFor(alias){
  const keys=Object.keys(serverNodes); const i=keys.indexOf(alias);
  return PALETTE[(i<0?0:i)%PALETTE.length];
}
const esc = s => (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));

function handle(ev, data, replay){
  switch(ev){
    case 'boot_start':
      Object.keys(serverNodes).forEach(a=>{serverNodes[a].node.remove();serverNodes[a].backend.remove();});
      for(const k in serverNodes) delete serverNodes[k];
      callCount=toolTotal=serverCount=0; refreshStats(); layout();
      activate('client'); setActivity('Booting · authenticating…', true);
      status('client','powering on…','busy');
      status('gateway','opening secure channel…','busy');
      if(!replay) log('BOOT','t-sys','MCP Client powering on');
      break;

    case 'server_connecting':
      ensureServer(data.alias, data.name, data.domain);
      serverNodes[data.alias].node.classList.add('connecting');
      setActivity('Connecting to '+(data.name||data.alias)+'…', true);
      status(data.alias,'authenticating…','busy');
      status('gateway','issuing OAuth2 token…','busy');
      if(!replay){
        log('AUTH','t-sys',`<b>${esc(data.name)}</b> · OAuth2 token + initialize`);
        packet(['client','gateway',data.alias],{color:colorFor(data.alias),label:'OAuth2 + initialize',dur:620});
      }
      break;

    case 'server_online':{
      const sv=serverNodes[data.alias]; if(!sv){ensureServer(data.alias,data.name,data.domain);}
      const el=serverNodes[data.alias].node;
      el.classList.remove('connecting'); el.classList.add('on');
      serverNodes[data.alias].tools = data.tool_count||0;
      status(data.alias, (data.tool_count||0)+' tools ready','ok');
      serverCount++; toolTotal+=data.tool_count||0; refreshStats();
      if(!replay){
        log('ONLINE','t-tool',`<b>${esc(data.name)}</b> ready · ${data.tool_count} tools`);
        packet([data.alias,'gateway','client'],{color:colorFor(data.alias),label:'tools/list',dur:620});
      }
      break;}

    case 'server_offline':{
      ensureServer(data.alias, data.name, '');
      const el=serverNodes[data.alias].node; el.classList.remove('connecting'); el.classList.add('off');
      status(data.alias,'offline','');
      if(!replay) log('OFFLINE','t-err',`<b>${esc(data.name)}</b> · ${esc(data.error)}`);
      break;}

    case 'boot_complete':
      deactivateAll();
      status('client','online · routing','');
      status('gateway','standing by','');
      setActivity('Ready — '+data.total_tools+' tools across '+data.servers+' servers', false);
      if(!replay){
        log('READY','t-sys',`All systems online · <b>${data.total_tools}</b> tools registered`);
        status('llm','learning the tool catalog…','busy');
        packet(['client','llm'],{color:'#b388ff',label:'register '+data.total_tools+' tools',dur:620,
          onDone:()=>status('llm', data.total_tools+' tools known · waiting','ok')});
      } else {
        status('llm', data.total_tools+' tools known · waiting','ok');
      }
      break;

    case 'user_query':
      deactivateAll(); activate('user'); setActivity('New query', true);
      status('user','asked a question','ok');
      status('client','forwarding question to LLM…','busy');
      log('ASK','t-user',esc(data.text));
      packet(['user','client'],{color:'#f0b429',label:'question',dur:620,onDone:()=>{
        activate('client');
        packet(['client','llm'],{color:'#f0b429',label:'query + tools',dur:620});
      }});
      break;

    case 'llm_thinking':
      activate('llm');
      if(pendingResults){
        pendingResults=false;
        status('llm','reading the tool results…','busy');
        status('client','passing results to LLM…','busy');
        setActivity('LLM interpreting results…', true);
        packet(['client','llm'],{color:'#2ee6a6',label:'tool results',dur:600});
      } else {
        status('llm','deciding which tools to call…','busy');
        setActivity('LLM reasoning…', true);
      }
      break;

    case 'llm_decided':{
      const n = data.calls ? data.calls.length : 0;
      status('llm','chose '+n+' tool call'+(n===1?'':'s'),'ok');
      setActivity('LLM chose '+n+' tool call(s)', true);
      (data.calls||[]).forEach(cq=>{
        log('ROUTE','t-llm',`→ <b>${esc(cq.alias)}</b> · ${esc(cq.tool)}`);
      });
      break;}

    case 'tool_call':
      callCount++; refreshStats();
      activate('llm',false); activate('client'); activate(data.alias);
      status('llm','dispatching tool call','');
      status('client','routing call → gateway…','busy');
      status('gateway','auth · policy · routing…','busy');
      status(data.alias,'running '+esc(data.tool)+'…','busy');
      setActivity('Calling '+esc(data.tool)+' on '+esc(data.alias), true);
      log('CALL','t-tool',`<b>${esc(data.alias)}</b> · ${esc(data.tool)} <span style="color:var(--mut)">${esc((data.args||'').slice(0,60))}</span>`);
      packet(['llm','client','gateway',data.alias],{color:colorFor(data.alias),label:esc(data.tool),dur:560});
      break;

    // direct_call: no LLM — used by mcp_client_simple. Packet goes client → gateway → server.
    case 'direct_call':
      callCount++; refreshStats();
      activate('client'); activate(data.alias);
      status('client','routing call → gateway…','busy');
      status('gateway','auth · policy · routing…','busy');
      status(data.alias,'running '+esc(data.tool)+'…','busy');
      setActivity('Calling '+esc(data.tool)+' on '+esc(data.alias), true);
      log('CALL','t-tool',`<b>${esc(data.alias)}</b> · ${esc(data.tool)} <span style="color:var(--mut)">${esc((data.args||'').slice(0,60))}</span>`);
      packet(['client','gateway',data.alias],{color:colorFor(data.alias),label:esc(data.tool),dur:560});
      break;

    case 'tool_result':
      pendingResults=true;
      status(data.alias, data.ok?('returned '+(data.size||0)+' B'):'call failed', data.ok?'ok':'');
      status('gateway','response audited & logged','ok');
      status('client','received tool data','ok');
      // direct_result: no LLM, deliver straight to user after client
      const returnPath = data.direct
        ? [data.alias,'gateway','client','user']
        : [data.alias,'gateway','client'];
      packet(returnPath,{
        color:data.ok?colorFor(data.alias):'#ff5d6c',
        label:data.ok?('result · '+(data.size||0)+'B'):'error',dur:560,
        onDone:()=>{activate(data.alias,false);
          if(data.direct){ activate('user'); status('user','got the result ✓','ok'); }
          status(data.alias, (serverNodes[data.alias]?serverNodes[data.alias].tools:0)+' tools ready','');}
      });
      log(data.ok?'DATA':'ERR', data.ok?'t-tool':'t-err',
          `<b>${esc(data.alias)}</b> · ${esc(data.tool)} ${data.ok?'returned '+(data.size||0)+' bytes':'failed'}`);
      break;

    case 'final_response':
      activate('llm');
      status('llm','drafting the answer…','busy');
      status('gateway','standing by','');
      setActivity('Summarising answer…', true);
      packet(['llm','client'],{color:'#2fe0e0',label:'answer',dur:600,onDone:()=>{
        activate('client');
        status('llm','answer ready','ok');
        status('client','delivering answer…','busy');
        packet(['client','user'],{color:'#2fe0e0',label:'answer',dur:600,onDone:()=>{
          activate('user');
          status('user','got the answer ✓','ok');
          status('client','online · routing','');
        }});
      }});
      if(data.text) answer(esc(data.text));
      break;

    case 'turn_done':
      setTimeout(()=>{ deactivateAll(); idleStatuses(); setActivity('Ready for next question', false); }, 1100);
      break;

    case 'menu_ready':
      // simple client: hide LLM node, show "no AI" label
      deactivateAll(); idleStatuses();
      status('llm','not used (no LLM)','');
      setActivity('Ready — pick a menu option', false);
      break;
  }
}

function refreshStats(){
  document.getElementById('st-servers').textContent=serverCount;
  document.getElementById('st-tools').textContent=toolTotal;
  document.getElementById('st-calls').textContent=callCount;
}

// ---- connect to the SSE stream ----
function connect(){
  const es = new EventSource('/events');
  es.onmessage = e=>{
    let m; try{ m=JSON.parse(e.data); }catch(_){ return; }
    try{ handle(m.event, m.data||{}, !!m.replay); }catch(err){ console.error(err); }
  };
  es.onerror = ()=>{ setActivity('Reconnecting…', false); };
}

window.addEventListener('resize', drawEdges);
layout(); connect();
</script>
</body>
</html>
"""
