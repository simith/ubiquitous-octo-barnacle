(function () {
  function markExternalLinks() {
    var host = window.location.host;
    var links = document.querySelectorAll('.md-content a[href]');
    links.forEach(function (a) {
      var href = a.getAttribute('href') || '';
      var isExternal = /^https?:\/\//i.test(href) && a.host !== host;
      if (isExternal) {
        a.setAttribute('target', '_blank');
        a.setAttribute('rel', 'noopener noreferrer');
      }
    });
  }

  if (typeof document$ !== 'undefined') {
    document$.subscribe(markExternalLinks);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', markExternalLinks);
  } else {
    markExternalLinks();
  }
})();
