/* TTN market tape. Never display simulated prices as market quotes. */
(() => {
  "use strict";
  function init() {
    const host = document.getElementById("ticker-strip");
    if (!host || typeof TTN_CONFIG === "undefined" || typeof TTNTickers === "undefined") return;
    host.innerHTML = '<div class="ttn-ticker-label">MARKETS</div><div class="ttn-ticker-window" tabindex="0" aria-label="Market ticker. Focus to pause scrolling."><div class="ttn-ticker-track"></div></div><span class="ttn-ticker-attribution">Charts: TradingView</span>';
    const track = host.querySelector(".ttn-ticker-track");
    function group(copy) {
      const el = document.createElement("div");
      el.className = "ttn-ticker-group";
      if (copy) el.setAttribute("aria-hidden", "true");
      TTN_CONFIG.TICKERS.forEach((ticker) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "ttn-ticker-item unavailable";
        if (copy) button.tabIndex = -1;
        button.dataset.id = ticker.id;
        button.dataset.symbol = ticker.tvSymbol;
        button.dataset.label = ticker.label;
        button.setAttribute("aria-label", "Open " + ticker.label + " chart");
        button.innerHTML = '<span class="ttn-ticker-name"></span><strong class="ttn-ticker-value">View chart</strong><span class="ttn-ticker-change"></span>';
        button.querySelector(".ttn-ticker-name").textContent = ticker.label;
        el.appendChild(button);
      });
      return el;
    }
    track.append(group(false), group(true));
    host.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-symbol]");
      if (button && typeof TTNChart !== "undefined") TTNChart.open(button.dataset.symbol, button.dataset.label);
    });
    function update() {
      track.querySelectorAll("button").forEach((button) => {
        const ticker = TTN_CONFIG.TICKERS.find((t) => t.id === button.dataset.id);
        const quote = TTNTickers.getState(ticker.id);
        const valid = quote && quote.demo === false && Number.isFinite(quote.price);
        const value = button.querySelector(".ttn-ticker-value");
        const change = button.querySelector(".ttn-ticker-change");
        button.className = "ttn-ticker-item";
        if (!valid) {
          button.classList.add("unavailable");
          value.textContent = "View chart";
          change.textContent = "";
          button.title = "Quote unavailable. Open the market chart.";
          return;
        }
        value.textContent = (ticker.type === "forex" ? "" : "$") + TTNTickers.fmtPrice(quote.price, { decimals: ticker.type === "forex" ? 4 : 2 });
        // Frankfurter provides a daily reference rate, not an intraday quote.
        if (ticker.type === "forex") {
          change.textContent = "Daily rate";
          button.title = "Daily reference rate from Frankfurter. Open the market chart.";
        } else {
          const pct = quote.changePct;
          change.textContent = Number.isFinite(pct) ? (pct >= 0 ? "+" : "") + pct.toFixed(2) + "%" : "";
          if (Number.isFinite(pct)) button.classList.add(pct >= 0 ? "up" : "down");
          button.title = "CoinGecko quote · 24-hour change. Open the market chart.";
        }
      });
    }
    update();
    // Update text in place: preserve animation and keyboard focus.
    setInterval(update, 1000);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
