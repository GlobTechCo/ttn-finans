/* Restore the reader's position when returning from an article, including mobile browsers. */
(() => {
  const key = 'ttn-return-position-v1';
  let pending = null;
  let restoring = false;
  let started = false;
  const url = location.pathname + location.search;
  const get = () => { try { return JSON.parse(sessionStorage.getItem(key) || 'null'); } catch (_) { return null; } };
  const put = value => { try { sessionStorage.setItem(key, JSON.stringify(value)); } catch (_) {} };
  const snapshot = article => {
    const card = article && article.closest('.editorial-archive-card');
    const anchor = card && card.querySelector('a[href$=".html"]');
    const target = anchor && anchor.getAttribute('href');
    return { url, y: scrollY, cardHref: target || null, offset: card ? card.getBoundingClientRect().top : 0, saved: Date.now(), pending: true };
  };
  document.addEventListener('click', event => {
    const a = event.target.closest('a[href]');
    if (!a || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const dest = new URL(a.href, location.href);
    if (dest.origin !== location.origin || !dest.pathname.endsWith('.html') || dest.pathname === location.pathname) return;
    if (!a.closest('.editorial-archive-card, .home-news-row, .home-top-row')) return;
    put(snapshot(a));
  }, true);
  const start = () => {
    const data = get();
    if (started || !data || !data.pending || data.url !== url || Date.now() - data.saved > 30 * 60 * 1000) return;
    started = true;
    pending = data;
    restoring = true;
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    const restore = () => {
      if (!restoring || !pending) return;
      let y = pending.y;
      if (pending.cardHref) {
        const links = [...document.querySelectorAll('.editorial-archive-card a[href]')];
        const a = links.find(el => el.getAttribute('href') === pending.cardHref);
        const card = a && a.closest('.editorial-archive-card');
        if (card) y = scrollY + card.getBoundingClientRect().top - pending.offset;
      }
      scrollTo({ top: Math.max(0, y), behavior: 'instant' });
    };
    restore();
    requestAnimationFrame(restore);
    [100, 300, 700, 1400].forEach(delay => setTimeout(restore, delay));
    setTimeout(() => {
      restore();
      restoring = false;
      put({ ...pending, pending: false });
      if ('scrollRestoration' in history) history.scrollRestoration = 'auto';
    }, 1750);
  };
  addEventListener('pageshow', start);
  addEventListener('DOMContentLoaded', start);
  ['touchstart','wheel','keydown'].forEach(type => addEventListener(type, () => { restoring = false; }, { passive: true }));
})();
