/* TTN Finance: restore position after returning from an article. */
(() => {
  'use strict';
  const KEY = 'ttn-reader-scroll-v2:';
  const route = location.pathname + location.search;
  const storageKey = KEY + route;
  let lastSaved = null;
  let restoring = false;
  let userInterrupted = false;
  let observer = null;
  let restoreTimer = null;

  function read() {
    try { return JSON.parse(sessionStorage.getItem(storageKey) || 'null'); }
    catch (_) { return null; }
  }
  function write(value) {
    try { sessionStorage.setItem(storageKey, JSON.stringify(value)); }
    catch (_) {}
  }
  function record(target) {
    const card = target && target.closest('article, .news-item, .editorial-archive-card');
    const link = card && card.querySelector('a[href]');
    const data = {
      y: Math.max(0, window.scrollY),
      target: target ? target.pathname : (link ? new URL(link.href, location.href).pathname : ''),
      cardTop: card ? card.getBoundingClientRect().top : null,
      cardClass: card ? card.className : '',
      time: Date.now(),
      pending: true
    };
    lastSaved = data;
    write(data);
  }

  // Save before navigation for every local article, including dynamic news cards.
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey ||
        event.shiftKey || event.altKey || link.target === '_blank' || link.hasAttribute('download')) return;
    const destination = new URL(link.href, location.href);
    if (destination.origin !== location.origin || !destination.pathname.endsWith('.html') ||
        destination.pathname === location.pathname) return;
    if (link.closest('header, footer, nav')) return;
    record(destination);
  }, true);
  window.addEventListener('pagehide', () => {
    if (lastSaved) write({ ...lastSaved, y: Math.max(0, lastSaved.y), time: Date.now(), pending: true });
  });

  function restore() {
    if (!restoring || userInterrupted || !lastSaved) return;
    let desired = lastSaved.y;
    if (lastSaved.target && lastSaved.cardTop !== null) {
      const anchors = document.querySelectorAll('article a[href], .news-item a[href]');
      for (const a of anchors) {
        if (new URL(a.href, location.href).pathname !== lastSaved.target) continue;
        const card = a.closest('article, .news-item');
        if (card) desired = window.scrollY + card.getBoundingClientRect().top - lastSaved.cardTop;
        break;
      }
    }
    const maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    window.scrollTo({ top: Math.min(maxScroll, Math.max(0, desired)), behavior: 'instant' });
  }

  function start() {
    if (restoring) return;
    const data = read();
    if (!data || !data.pending || Date.now() - data.time > 60 * 60 * 1000) return;
    // The stored state belongs to a departure into an article, not an ordinary new visit.
    lastSaved = data;
    restoring = true;
    userInterrupted = false;
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    restore();
    observer = new MutationObserver(() => {
      if (restoring) requestAnimationFrame(restore);
    });
    observer.observe(document.body, { childList: true, subtree: true });
    window.addEventListener('load', restore, { once: true });
    const started = performance.now();
    const loop = () => {
      if (!restoring || userInterrupted) return;
      restore();
      if (performance.now() - started < 4500) restoreTimer = setTimeout(loop, 150);
      else finish();
    };
    restoreTimer = setTimeout(loop, 90);
  }

  function finish() {
    if (!restoring) return;
    restoring = false;
    if (observer) observer.disconnect();
    clearTimeout(restoreTimer);
    if (lastSaved) write({ ...lastSaved, pending: false });
    if ('scrollRestoration' in history) history.scrollRestoration = 'auto';
  }
  ['wheel', 'touchstart', 'pointerdown', 'keydown'].forEach(type => {
    addEventListener(type, () => { if (restoring) { userInterrupted = true; finish(); } }, { passive: true });
  });
  window.addEventListener('pageshow', start);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
