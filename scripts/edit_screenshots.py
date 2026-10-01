#!/usr/bin/env python3
"""
Image editor for annotating screenshots before adding to docs.

Usage:
    python scripts/edit_screenshots.py                    # edit images in docs/images/
    python scripts/edit_screenshots.py --dir screenshots  # edit images in specific folder

Keyboard shortcuts:
    B       — Blur tool  (drag rectangle → solid fill on release)
    M       — Mark tool  (drag rectangle → red border + numbered badge)
    Ctrl+Z  — Undo
    Ctrl+S  — Save & advance to next image

Saves to <dir>/edited/. Revisiting an image loads the edited version automatically.
"""

import argparse
import base64
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Timer
from urllib.parse import unquote, urlparse

IMG_DIR: Path = Path("docs/images")
PORT = 8765

HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Screenshot Editor</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    display: flex; flex-direction: column; height: 100vh;
    background: #1a1a1a; color: #eee;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    overflow: hidden; user-select: none;
}
#toolbar {
    display: flex; align-items: center; gap: 8px;
    padding: 0 12px; background: #252525;
    border-bottom: 1px solid #3a3a3a;
    height: 46px; flex-shrink: 0;
}
.tbtn {
    padding: 5px 14px; border: 2px solid transparent;
    border-radius: 6px; cursor: pointer; font-size: 13px;
    font-weight: 600; color: #ddd; background: #3a3a3a; white-space: nowrap;
}
.tbtn:hover { background: #484848; }
.tbtn.active { border-color: rgba(255,255,255,0.55); }
#btn-blur.active { background: #d97706; color: #fff; }
#btn-mark.active { background: #dc2626; color: #fff; }
#btn-reset { background: #6b7280; color: #fff; }
#btn-reset:hover { background: #4b5563; }
#btn-save { background: #0070f3; color: #fff; margin-left: auto; }
#btn-save:hover { background: #0060d3; }
#status { font-size: 12px; color: #888; flex-shrink: 0; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#done-banner {
    display: none; position: fixed; inset: 0; z-index: 9999;
    background: rgba(0,0,0,0.75); align-items: center; justify-content: center;
}
#done-banner.show { display: flex; }
#done-box {
    background: #1e1e1e; border: 1px solid #3a3a3a; border-radius: 14px;
    padding: 40px 56px; text-align: center; max-width: 420px;
}
#done-box h2 { font-size: 28px; margin-bottom: 10px; }
#done-box p  { color: #aaa; font-size: 14px; line-height: 1.6; margin-bottom: 24px; }
#done-close  { padding: 10px 28px; background: #0070f3; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }
#main { display: flex; flex: 1; overflow: hidden; }
#sidebar {
    width: 190px; flex-shrink: 0; overflow-y: auto;
    background: #1e1e1e; border-right: 1px solid #333; padding: 10px 8px;
}
#sidebar h3 { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px; padding: 0 4px; }
.img-item {
    padding: 5px 8px; border-radius: 5px; cursor: pointer;
    font-size: 11px; color: #aaa; word-break: break-all;
    line-height: 1.4; display: flex; align-items: flex-start; gap: 5px;
}
.img-item:hover { background: #2a2a2a; }
.img-item.active { background: #0070f3; color: #fff; }
.img-item .tick { color: #4ade80; flex-shrink: 0; font-size: 10px; margin-top: 1px; }
#canvas-wrap {
    flex: 1; overflow: auto;
    display: flex; align-items: flex-start; justify-content: flex-start;
    padding: 16px; background: #111;
}
#canvas { display: block; cursor: crosshair; box-shadow: 0 2px 20px rgba(0,0,0,0.6); }
#empty-msg { color: #555; font-size: 14px; margin: auto; }
</style>
</head>
<body>
<div id="toolbar">
    <button class="tbtn active" id="btn-blur"  title="Blur (B) — drag to fill">⬛ Blur</button>
    <button class="tbtn"        id="btn-mark"  title="Mark (M) — drag rectangle">⬜ Mark</button>
    <button class="tbtn"        id="btn-undo"  title="Undo (Ctrl+Z)">↩ Undo</button>
    <button class="tbtn"        id="btn-clear" title="Clear all markups">✕ Clear</button>
    <button class="tbtn"        id="btn-reset" title="Reset to original image">↺ Reset</button>
    <span id="status">Loading…</span>
    <button class="tbtn" id="btn-save" title="Save (Ctrl+S)">💾 Save &amp; Next</button>
</div>
<div id="done-banner">
    <div id="done-box">
        <h2>🎉 All done!</h2>
        <p id="done-msg"></p>
        <button id="done-close">Close</button>
    </div>
</div>
<div id="main">
    <div id="sidebar">
        <h3>Images</h3>
        <div id="img-list"></div>
    </div>
    <div id="canvas-wrap">
        <div id="empty-msg">No images found in folder.</div>
        <canvas id="canvas" style="display:none"></canvas>
    </div>
</div>

<script>
const canvas   = document.getElementById('canvas');
const ctx      = canvas.getContext('2d');
const statusEl = document.getElementById('status');

let activeTool   = 'blur';
let isDrawing    = false;
let startX = 0,  startY = 0;
let undoStack    = [];
let baseImage    = null;
let currentFile  = null;
let savedFiles   = new Set();
let imgList      = [];
let currentIndex = 0;
let snap         = null;
let markCount    = 0;   // resets per image

// ── Tool buttons ──────────────────────────────────────────────────────────
function setTool(t) {
    activeTool = t;
    document.getElementById('btn-blur').classList.toggle('active', t === 'blur');
    document.getElementById('btn-mark').classList.toggle('active', t === 'mark');
}
setTool('blur');

document.getElementById('btn-blur').addEventListener('click',  () => setTool('blur'));
document.getElementById('btn-mark').addEventListener('click',  () => setTool('mark'));
document.getElementById('btn-undo').addEventListener('click',  undo);
document.getElementById('btn-clear').addEventListener('click', clearAll);
document.getElementById('btn-reset').addEventListener('click', resetToOriginal);
document.getElementById('btn-save').addEventListener('click',  saveAndNext);
document.getElementById('done-close').addEventListener('click', () =>
    document.getElementById('done-banner').classList.remove('show'));

document.addEventListener('keydown', e => {
    if (document.activeElement.tagName === 'INPUT') return;
    const k = e.key.toLowerCase();
    if (k === 'b') setTool('blur');
    if (k === 'm') setTool('mark');
    if ((e.ctrlKey || e.metaKey) && k === 'z') { e.preventDefault(); undo(); }
    if ((e.ctrlKey || e.metaKey) && k === 's') { e.preventDefault(); saveAndNext(); }
});

// ── Undo ──────────────────────────────────────────────────────────────────
function pushUndo() {
    undoStack.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
    if (undoStack.length > 25) undoStack.shift();
}
function undo() {
    if (!undoStack.length) return;
    // If undoing the last mark, decrement the counter
    if (activeTool === 'mark' && markCount > 0) markCount--;
    ctx.putImageData(undoStack.pop(), 0, 0);
}
function clearAll() {
    if (!baseImage) return;
    undoStack = [];
    markCount = 0;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(baseImage, 0, 0);
}

// Load the original (unedited) file, ignoring any saved edited version
function resetToOriginal() {
    if (!currentFile) return;
    undoStack = []; snap = null; markCount = 0;
    savedFiles.delete(currentFile);
    updateList();
    const img = new Image();
    img.onload = () => {
        baseImage = img;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
        statusEl.textContent = `Reset to original — ${currentFile}`;
    };
    img.src = `/image/${encodeURIComponent(currentFile)}?original=1&t=${Date.now()}`;
}

// ── Coordinate mapping ────────────────────────────────────────────────────
function coords(e) {
    const r = canvas.getBoundingClientRect();
    return {
        x: (e.clientX - r.left) * (canvas.width  / r.width),
        y: (e.clientY - r.top)  * (canvas.height / r.height),
    };
}

// ── Solid-fill blur (average colour of region) ────────────────────────────
function applyBlurRect(x, y, w, h) {
    x = Math.max(0, Math.floor(x));
    y = Math.max(0, Math.floor(y));
    w = Math.min(canvas.width  - x, Math.ceil(w));
    h = Math.min(canvas.height - y, Math.ceil(h));
    if (w <= 0 || h <= 0) return;

    const data = ctx.getImageData(x, y, w, h).data;
    let r = 0, g = 0, b = 0;
    const n = w * h;
    for (let i = 0; i < data.length; i += 4) {
        r += data[i]; g += data[i + 1]; b += data[i + 2];
    }
    ctx.fillStyle = `rgb(${Math.round(r/n)},${Math.round(g/n)},${Math.round(b/n)})`;
    ctx.fillRect(x, y, w, h);
}

// ── Numbered badge at top-right of rectangle ──────────────────────────────
function drawBadge(rx, ry, rw, number) {
    const label  = String(number);
    const radius = label.length > 1 ? 16 : 14;
    const cx = Math.min(rx + rw + radius, canvas.width  - radius - 1);
    const cy = Math.max(ry - radius,      radius + 1);

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = '#ef4444';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2.5;
    ctx.stroke();
    ctx.fillStyle    = '#fff';
    ctx.font         = `bold ${radius + 5}px -apple-system, sans-serif`;
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, cx, cy);
    ctx.restore();
}

// ── Canvas mouse events ───────────────────────────────────────────────────
canvas.addEventListener('mousedown', e => {
    if (!currentFile) return;
    const { x, y } = coords(e);
    pushUndo();
    snap    = ctx.getImageData(0, 0, canvas.width, canvas.height);
    startX  = x; startY = y;
    isDrawing = true;
});

canvas.addEventListener('mousemove', e => {
    if (!isDrawing || !snap) return;
    const { x, y } = coords(e);

    ctx.putImageData(snap, 0, 0);   // restore before redrawing preview

    const rx = Math.min(x, startX), ry = Math.min(y, startY);
    const rw = Math.abs(x - startX), rh = Math.abs(y - startY);

    if (activeTool === 'blur') {
        // Dashed white outline preview
        ctx.save();
        ctx.strokeStyle = 'rgba(255,255,255,0.85)';
        ctx.lineWidth   = 1.5;
        ctx.setLineDash([6, 4]);
        ctx.strokeRect(rx + 0.5, ry + 0.5, rw, rh);
        ctx.restore();
    } else {
        // Red rectangle preview + badge preview
        ctx.save();
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth   = 5;
        ctx.lineJoin    = 'round';
        ctx.strokeRect(rx + 2.5, ry + 2.5, rw - 5, rh - 5);
        ctx.restore();
        drawBadge(rx, ry, rw, markCount + 1);
    }
});

canvas.addEventListener('mouseup', e => {
    if (!isDrawing || !snap) return;
    const { x, y } = coords(e);

    const rx = Math.min(x, startX), ry = Math.min(y, startY);
    const rw = Math.abs(x - startX), rh = Math.abs(y - startY);

    if (rw < 5 || rh < 5) {
        // Too small — cancel
        ctx.putImageData(snap, 0, 0);
        undoStack.pop();
    } else if (activeTool === 'blur') {
        ctx.putImageData(snap, 0, 0);
        applyBlurRect(rx, ry, rw, rh);
    } else {
        // Mark: rectangle was drawn in last mousemove; just add badge permanently
        markCount++;
        // Redraw clean rect + badge on top of snap to avoid double-stroke artifacts
        ctx.putImageData(snap, 0, 0);
        ctx.save();
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth   = 5;
        ctx.lineJoin    = 'round';
        ctx.strokeRect(rx + 2.5, ry + 2.5, rw - 5, rh - 5);
        ctx.restore();
        drawBadge(rx, ry, rw, markCount);
    }

    isDrawing = false;
    snap      = null;
});

canvas.addEventListener('mouseleave', () => {
    if (isDrawing && snap) {
        ctx.putImageData(snap, 0, 0);
        undoStack.pop();
    }
    isDrawing = false;
    snap      = null;
});

// ── Load image ────────────────────────────────────────────────────────────
// The server returns the edited version if one exists, so revisits are correct.
function loadImage(filename, index) {
    currentFile  = filename;
    currentIndex = index;
    undoStack    = [];
    snap         = null;
    markCount    = 0;

    document.querySelectorAll('.img-item').forEach((el, i) =>
        el.classList.toggle('active', i === index));
    statusEl.textContent = `${filename}  (${index + 1} / ${imgList.length})`;

    const img = new Image();
    img.onload = () => {
        baseImage     = img;
        canvas.width  = img.naturalWidth;
        canvas.height = img.naturalHeight;

        const wrap = document.getElementById('canvas-wrap');
        const maxW = wrap.clientWidth  - 32;
        const maxH = wrap.clientHeight - 32;
        const sc   = Math.min(maxW / img.naturalWidth, maxH / img.naturalHeight, 1);
        canvas.style.width  = `${img.naturalWidth  * sc}px`;
        canvas.style.height = `${img.naturalHeight * sc}px`;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);

        document.getElementById('empty-msg').style.display = 'none';
        canvas.style.display = 'block';
    };
    img.src = `/image/${encodeURIComponent(filename)}?t=${Date.now()}`;
}

// ── Save & advance ────────────────────────────────────────────────────────
async function saveAndNext() {
    if (!currentFile) return;
    statusEl.textContent = 'Saving…';

    const res = await fetch('/save', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ filename: currentFile, data: canvas.toDataURL('image/png') }),
    });
    const result = await res.json();
    if (!result.ok) { statusEl.textContent = 'Save failed.'; return; }

    savedFiles.add(currentFile);
    markCount = 0;
    updateList();
    statusEl.textContent = `Saved ✓  → ${result.path}`;

    // Show completion banner when all images are done
    if (savedFiles.size >= imgList.length) {
        const banner = document.getElementById('done-banner');
        document.getElementById('done-msg').textContent =
            `All ${imgList.length} image${imgList.length > 1 ? 's' : ''} saved to the edited/ folder.`;
        banner.classList.add('show');
        return;
    }

    setTimeout(() => {
        const next = imgList.findIndex((f, i) => i > currentIndex && !savedFiles.has(f));
        if (next !== -1) loadImage(imgList[next], next);
    }, 600);
}

// ── Sidebar ───────────────────────────────────────────────────────────────
function updateList() {
    const container = document.getElementById('img-list');
    container.innerHTML = '';
    imgList.forEach((name, i) => {
        const el = document.createElement('div');
        el.className = 'img-item' + (i === currentIndex ? ' active' : '');
        el.innerHTML = savedFiles.has(name)
            ? `<span class="tick">✓</span><span>${name}</span>`
            : `<span>${name}</span>`;
        el.addEventListener('click', () => loadImage(name, i));
        container.appendChild(el);
    });
}

// ── Init ──────────────────────────────────────────────────────────────────
fetch('/images')
    .then(r => r.json())
    .then(items => {
        imgList = items.map(i => i.name);
        // Pre-mark any images that already have an edited version on disk
        items.forEach(i => { if (i.edited) savedFiles.add(i.name); });
        if (!imgList.length) { statusEl.textContent = 'No images found.'; return; }
        updateList();
        loadImage(imgList[0], 0);
    });
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self._respond(200, "text/html", HTML.encode())

        elif path == "/images":
            edited_dir = IMG_DIR / "edited"
            files = []
            for f in sorted(IMG_DIR.iterdir()):
                if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    files.append({
                        "name":   f.name,
                        "edited": (edited_dir / f.name).exists(),
                    })
            self._respond_json(files)

        elif path.startswith("/image/"):
            filename = unquote(path[7:])
            original_only = "original=1" in urlparse(self.path).query
            edited   = IMG_DIR / "edited" / filename
            original = IMG_DIR / filename
            # Serve edited version unless caller explicitly wants the original
            filepath = original if original_only else (edited if edited.exists() else original)
            if filepath.exists() and filepath.suffix.lower() in (".png", ".jpg", ".jpeg"):
                ct = "image/png" if filepath.suffix.lower() == ".png" else "image/jpeg"
                self._respond(200, ct, filepath.read_bytes())
            else:
                self.send_error(404)

        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/save":
            length    = int(self.headers["Content-Length"])
            body      = json.loads(self.rfile.read(length))
            filename  = Path(body["filename"]).name
            img_bytes = base64.b64decode(body["data"].split(",", 1)[1])

            out_dir  = IMG_DIR / "edited"
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / filename
            out_path.write_bytes(img_bytes)

            print(f"  Saved → {out_path}")
            self._respond_json({"ok": True, "path": str(out_path)})
        else:
            self.send_error(404)

    def _respond(self, code, content_type, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _respond_json(self, data):
        self._respond(200, "application/json", json.dumps(data).encode())

    def log_message(self, *_):  # noqa: S1186
        pass


def main():
    global IMG_DIR
    parser = argparse.ArgumentParser(description="Screenshot annotation editor")
    parser.add_argument("--dir", default="docs/images",
                        help="Folder containing images to edit (default: docs/images/)")
    args = parser.parse_args()

    IMG_DIR = Path(args.dir)
    if not IMG_DIR.exists():
        print(f"Folder not found: {IMG_DIR}")
        return

    url = f"http://localhost:{PORT}"
    Timer(0.5, lambda: webbrowser.open(url)).start()

    print(f"\n  Editor → {url}")
    print(f"  Images from:  {IMG_DIR}/")
    print(f"  Saves to:     {IMG_DIR}/edited/")
    print(f"  Ctrl+C to quit.\n")

    server = HTTPServer(("localhost", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Done.")


if __name__ == "__main__":
    main()
