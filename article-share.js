/* Canonical article sharing; no tracking or external dependencies. */
(() => {
  function mount() {
    if (document.querySelector('.ttn-copy-link')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'ttn-copy-link';
    button.setAttribute('aria-label', 'Copy article link');
    button.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l2-2"/></svg><span>Copy link</span>';
    const label = button.querySelector('span');
    const status = document.createElement('span');
    status.className = 'ttn-copy-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    document.body.append(button, status);
    let reset;
    button.addEventListener('click', async () => {
      const url = new URL(document.querySelector('link[rel="canonical"]')?.href || location.href);
      url.search = ''; url.hash = '';
      let copied = false;
      try { await navigator.clipboard.writeText(url.href); copied = true; } catch (_) {
        const field = document.createElement('textarea');
        field.value = url.href;
        field.setAttribute('readonly', '');
        field.style.cssText = 'position:fixed;left:-9999px;top:0';
        document.body.append(field);
        field.select();
        try { copied = document.execCommand('copy'); } catch (_) {}
        field.remove(); button.focus({preventScroll:true});
      }
      clearTimeout(reset);
      label.textContent = copied ? 'Link copied' : 'Copy link';
      status.textContent = copied ? 'Article link copied to clipboard.' : 'Copy this article link from the field that follows.';
      if (!copied) window.prompt('Copy article link:', url.href);
      reset = setTimeout(() => { label.textContent = 'Copy link'; status.textContent = ''; }, 2500);
    });
    function avoidConsent() {
      const consent = document.getElementById('cookie-consent');
      const visible = consent && consent.getBoundingClientRect().height > 0 && getComputedStyle(consent).visibility !== 'hidden';
      button.hidden = Boolean(visible);
    }
    avoidConsent();
    new MutationObserver(avoidConsent).observe(document.body, {childList:true, subtree:true});
    window.addEventListener('resize', avoidConsent);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
