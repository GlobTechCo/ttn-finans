/* TTN-styled tape with TradingView market quotes and standard asset logos. */
(() => {
  "use strict";
  function init() {
    const host = document.getElementById("ticker-strip");
    if (!host) return;
    host.innerHTML = '<div class="ttn-ticker-label">MARKETS</div><div class="ttn-live-tape"><tv-ticker-tape symbols="BITSTAMP:BTCUSD,BITSTAMP:ETHUSD,FOREXCOM:SPXUSD,FOREXCOM:NSXUSD,CMCMARKETS:GOLD,FX:UKOIL,FX:EURUSD" symbol-titles="{&quot;FX:UKOIL&quot;:&quot;Brent Oil&quot;}" item-size="compact" hide-chart></tv-ticker-tape></div>';
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
