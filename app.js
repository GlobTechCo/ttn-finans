/** Start news and quotes independently. No external provider gates another. */
(() => {
  function start() {
    if (typeof TTNMarketSummary !== "undefined") {
      TTNMarketSummary.render();
      document.addEventListener("ttn-prices-updated", TTNMarketSummary.render);
      document.addEventListener("ttn-news-updated", TTNMarketSummary.render);
    }
    if (typeof TTNTickers !== "undefined") TTNTickers.init().catch(console.warn);
    if (typeof TTNNews !== "undefined") TTNNews.init().catch(console.warn);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
