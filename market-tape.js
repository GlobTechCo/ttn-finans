/* TTN-styled tape with TradingView market quotes and standard asset logos. */
(() => {
  "use strict";
  function init() {
    const host = document.getElementById("ticker-strip");
    if (!host) return;
    if (host.dataset.layout === 'cards') {
      const cards = host.querySelectorAll('tv-mini-chart');
      const syncCards = () => cards.forEach(card => card.setAttribute('theme', document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'));
      syncCards();
      new MutationObserver(syncCards).observe(document.documentElement, {attributes: true, attributeFilter: ['data-theme']});
      return;
    }
    const crypto = host.dataset.market === 'crypto';
    host.innerHTML = '<div class="ttn-ticker-label">MARKETS</div><div class="ttn-live-tape"><tv-ticker-tape symbols="BITSTAMP:BTCUSD,BITSTAMP:ETHUSD,COINBASE:SOLUSD,BITSTAMP:XRPUSD,FOREXCOM:SPXUSD,FOREXCOM:NSXUSD,CMCMARKETS:GOLD,FX:UKOIL,FX:EURUSD" symbol-titles="{&quot;FX:UKOIL&quot;:&quot;Brent Oil&quot;}" item-size="compact" hide-chart></tv-ticker-tape></div>';
    if (crypto) host.innerHTML = '<div class="ttn-live-tape"><tv-ticker-tape symbols="BITSTAMP:BTCUSD,BITSTAMP:ETHUSD,COINBASE:SOLUSD,BITSTAMP:XRPUSD" item-size="compact" hide-chart></tv-ticker-tape></div>';
    const widget = host.querySelector("tv-ticker-tape");
    function syncTheme() {
      widget.setAttribute("theme", document.documentElement.dataset.theme === "dark" ? "dark" : "light");
    }
    syncTheme();
    new MutationObserver(syncTheme).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
