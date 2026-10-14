(function () {
  var STORE = 'sap-mcp-progress';

  var PAGE_TOTALS = {
    'bah-01-purchase-order':   11,
    'bah-02-business-partner':  6,
    'bah-03-inbound-delivery':  6,
    'bah-04-material-stock':    6,
    'bah-05-ai-agent':          5,
  };
  var GRAND_TOTAL = 34;

  var PAGES = [
    { id: 'bah-01-purchase-order',   label: '1. Purchase Order MCP',    href: '../bah-01-purchase-order/' },
    { id: 'bah-02-business-partner', label: '2. Business Partner MCP',  href: '../bah-02-business-partner/' },
    { id: 'bah-03-inbound-delivery', label: '3. Inbound Delivery MCP',  href: '../bah-03-inbound-delivery/' },
    { id: 'bah-04-material-stock',   label: '4. Material Stock MCP',    href: '../bah-04-material-stock/' },
    { id: 'bah-05-ai-agent',         label: '5. AI Agent Client',       href: '../bah-05-ai-agent/' },
  ];

  function load() {
    try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (e) { return {}; }
  }
  function persist(d) {
    try { localStorage.setItem(STORE, JSON.stringify(d)); } catch (e) {}
  }
  function pageId() {
    return window.location.pathname.replace(/\/$/, '').split('/').pop() || 'index';
  }
  function objValues(o) {
    return Object.keys(o).map(function (k) { return o[k]; });
  }
  function countDone() {
    var d = load();
    var done = 0;
    Object.keys(PAGE_TOTALS).forEach(function (pid) {
      var pd = d[pid];
      if (pd && pd.done) done += objValues(pd.done).filter(Boolean).length;
    });
    return done;
  }

  /* ── header progress widget (left of dark/light toggle) ── */
  function initHeaderWidget() {
    var widget = document.getElementById('tp-hw');
    if (!widget) {
      widget = document.createElement('div');
      widget.id = 'tp-hw';
      widget.innerHTML =
        '<span class="tp-hw-label">Tutorial Progress</span>' +
        '<div class="tp-hw-track"><div class="tp-hw-fill" id="tp-hw-fill"></div></div>' +
        '<span class="tp-hw-pct" id="tp-hw-pct"></span>';

      var palette = document.querySelector('[data-md-component="palette"]');
      if (palette && palette.parentNode) {
        palette.parentNode.insertBefore(widget, palette);
      } else {
        var nav = document.querySelector('.md-header__inner');
        if (nav) nav.appendChild(widget);
      }
    }
    updateHeaderWidget();
  }

  function updateHeaderWidget() {
    var fill = document.getElementById('tp-hw-fill');
    var pctEl = document.getElementById('tp-hw-pct');
    if (!fill || !pctEl) return;
    var done = countDone();
    var pct = Math.round(done / GRAND_TOTAL * 100);
    fill.style.width = pct + '%';
    fill.style.background = pct === 100 ? '#4caf50' : 'rgba(255,255,255,0.9)';
    pctEl.textContent = pct + '%';
  }

  /* ── checkbox state restore + green highlight ── */
  function initCheckboxes() {
    var cbs = Array.from(document.querySelectorAll('.task-list-item input[type="checkbox"]'));
    if (!cbs.length) return;

    var id = pageId();
    var d = load();
    if (!d[id]) d[id] = { total: 0, done: {} };
    d[id].total = cbs.length;
    if (!d[id].done) d[id].done = {};

    cbs.forEach(function (cb, i) {
      cb.checked = !!d[id].done[i];
      styleItem(cb);
    });
    persist(d);

    cbs.forEach(function (cb, i) {
      cb.addEventListener('change', function () {
        var d2 = load();
        if (!d2[id]) d2[id] = { total: cbs.length, done: {} };
        if (!d2[id].done) d2[id].done = {};
        d2[id].done[i] = cb.checked;
        persist(d2);
        styleItem(cb);
        updateHeaderWidget();
      });
    });
  }

  function styleItem(cb) {
    var li = cb.closest('li');
    if (!li) return;
    if (cb.checked) li.classList.add('tp-done');
    else li.classList.remove('tp-done');
  }

  /* ── overview (page 05) ── */
  function initOverview() {
    var el = document.getElementById('tp-overview');
    if (!el) return;
    var d = load();
    var grandDone = 0;

    var rows = PAGES.map(function (p) {
      var pd = d[p.id] || {};
      var total = PAGE_TOTALS[p.id];
      var done = pd.done ? objValues(pd.done).filter(Boolean).length : 0;
      grandDone += done;
      var pct = Math.round(done / total * 100);
      var color = pct === 100 ? '#2e7d32' : 'var(--md-primary-fg-color)';
      return '<div class="tp-ov-row">' +
        '<a class="tp-ov-label" href="' + p.href + '">' + p.label + '</a>' +
        '<div class="tp-track tp-ov-track">' +
          '<div class="tp-fill" style="width:' + pct + '%;background:' + color + '"></div>' +
        '</div>' +
        '<span class="tp-ov-count">' + done + ' / ' + total + '</span>' +
        '</div>';
    }).join('');

    var gPct = Math.round(grandDone / GRAND_TOTAL * 100);
    var gColor = gPct === 100 ? '#2e7d32' : 'var(--md-primary-fg-color)';

    el.innerHTML =
      '<div class="tp-ov-overall">' +
        '<div class="tp-ov-header">' +
          '<strong>Overall progress</strong>' +
          '<span class="tp-ov-count">' + grandDone + ' / ' + GRAND_TOTAL + ' (' + gPct + '%)</span>' +
        '</div>' +
        '<div class="tp-track tp-ov-overall-track">' +
          '<div class="tp-fill" style="width:' + gPct + '%;background:' + gColor + '"></div>' +
        '</div>' +
      '</div>' + rows;
  }

  function run() {
    initHeaderWidget();
    initCheckboxes();
    initOverview();
  }

  if (typeof document$ !== 'undefined') {
    document$.subscribe(run);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
