/* Search highlight navigator — clears on Escape/click, prev/next traversal */
(function () {
  var marks = [], current = -1, nav = null;

  function buildNav() {
    if (nav) nav.remove();
    marks = Array.from(document.querySelectorAll('mark'));
    if (marks.length === 0) return;

    nav = document.createElement('div');
    nav.id = 'search-nav';
    nav.innerHTML =
      '<button id="sn-prev" title="Previous match">&#8592;</button>' +
      '<span id="sn-count"></span>' +
      '<button id="sn-next" title="Next match">&#8594;</button>' +
      '<button id="sn-clear" title="Clear highlights">&#10005;</button>';
    document.body.appendChild(nav);

    document.getElementById('sn-prev').addEventListener('click', function () { jump(-1); });
    document.getElementById('sn-next').addEventListener('click', function () { jump(1); });
    document.getElementById('sn-clear').addEventListener('click', clearHighlights);

    jump(0);
  }

  function jump(delta) {
    if (marks.length === 0) return;
    if (current >= 0) marks[current].classList.remove('sn-active');
    current = (current + delta + marks.length) % marks.length;
    marks[current].classList.add('sn-active');
    marks[current].scrollIntoView({ behavior: 'smooth', block: 'center' });
    document.getElementById('sn-count').textContent = (current + 1) + ' / ' + marks.length;
  }

  function clearHighlights() {
    document.querySelectorAll('mark').forEach(function (m) {
      var t = document.createTextNode(m.textContent);
      m.parentNode.replaceChild(t, m);
      m.parentNode.normalize();
    });
    var url = new URL(window.location.href);
    url.searchParams.delete('h');
    history.replaceState(null, '', url.toString());
    if (nav) { nav.remove(); nav = null; }
    marks = []; current = -1;
  }

  /* Clear on Escape */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') clearHighlights();
  });

  /* Clear when clicking the main content (not search box) */
  document.addEventListener('click', function (e) {
    if (marks.length === 0) return;
    if (e.target.closest('[data-md-component="search"]') ||
        e.target.closest('#search-nav')) return;
    clearHighlights();
  });

  /* Watch for marks being injected after page load (MkDocs Material lazily adds them) */
  var observer = new MutationObserver(function () {
    var fresh = document.querySelectorAll('mark');
    if (fresh.length > 0 && fresh.length !== marks.length) buildNav();
  });
  observer.observe(document.body, { childList: true, subtree: true });

  /* Also try once on DOMContentLoaded in case marks are already there */
  document.addEventListener('DOMContentLoaded', buildNav);
})();
