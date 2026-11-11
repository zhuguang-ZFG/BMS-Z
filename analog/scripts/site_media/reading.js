/* The original README split left pre-heading anchors on the previous page.
 * Source links now point to their owners. Keep already shared URLs working. */
(function () {
  'use strict';

  function followLegacyAnchor() {
    var id;
    try { id = decodeURIComponent(window.location.hash.slice(1)); }
    catch (_) { return; }
    if (!id) return;
    var anchor = document.getElementById(id);
    if (!anchor || !anchor.classList.contains('legacy-anchor')) return;
    var link = anchor.querySelector('a[href]');
    if (!link) return;
    var target = new URL(link.href, window.location.href);
    if (target.origin !== window.location.origin) return;
    target.search = window.location.search;
    if (target.href !== window.location.href) window.location.replace(target.href);
  }

  window.addEventListener('hashchange', followLegacyAnchor);
  if (typeof document$ !== 'undefined') document$.subscribe(followLegacyAnchor);
  else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', followLegacyAnchor);
  } else followLegacyAnchor();
})();
