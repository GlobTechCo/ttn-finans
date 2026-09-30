/**
 * TTN — chart panel (TradingView Advanced Chart Widget)
 * Opens under the ticker strip, or when a ticker tag in an article is clicked.
 */
const TTNChart = (() => {
  let currentSymbol = null;

  function ensurePanel() {
    let panel = document.getElementById("chart-panel");
    if (panel) return panel;

    panel = document.createElement("div");
    panel.id = "chart-panel";
    panel.className = "chart-panel";
    panel.innerHTML = `
      <div class="chart-panel-inner">
        <div class="chart-panel-head">
          <span id="chart-panel-title">—</span>
          <button id="chart-panel-close" aria-label="Close chart">×</button>
        </div>
        <div id="tv-chart-container"></div>
      </div>`;

    const strip = document.getElementById("ticker-strip");
    const anchor = strip || document.querySelector(".topnav") || document.body;
    anchor.insertAdjacentElement("afterend", panel);

    panel.querySelector("#chart-panel-close").addEventListener("click", close);
    return panel;
  }

  function open(tvSymbol, label) {
    const panel = ensurePanel();
    document.getElementById("chart-panel-title").textContent = `${label} · ${tvSymbol}`;

    if (currentSymbol === tvSymbol && panel.classList.contains("open")) {
      close();
      return;
    }
    currentSymbol = tvSymbol;

    // Update visible state first, so a problem loading the external
    // TradingView script (e.g. a page missing the script tag, or the
    // script failing to load) still leaves the panel visibly open
    // and scrolled to, instead of silently doing nothing.
    panel.classList.add("open");
    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });

    // Fully replace the container node (not just clear its innerHTML) —
    // TradingView's widget script doesn't always reinitialize cleanly in a
    // reused container, which is why switching tickers could get stuck
    // showing the previous chart.
    const oldContainer = document.getElementById("tv-chart-container");
    const freshContainer = document.createElement("div");
    freshContainer.id = "tv-chart-container";
    oldContainer.replaceWith(freshContainer);

    const render = () => {
      if (currentSymbol !== tvSymbol) return true;
      if (typeof TradingView === "undefined" || typeof TradingView.widget !== "function") return false;
      freshContainer.textContent = "";
      try {
        new TradingView.widget({
          autosize: true,
          symbol: tvSymbol,
          interval: "60",
          timezone: "Etc/UTC",
          theme: "dark",
          style: "1",
          locale: "en",
          toolbar_bg: "#12161b",
          enable_publishing: false,
          hide_top_toolbar: false,
          hide_legend: false,
          save_image: false,
          container_id: "tv-chart-container",
        });
        return true;
      } catch (e) {
        return false;
      }
    };

    if (!render()) {
      freshContainer.textContent = "Loading chart…";
      let attempts = 0;
      const retry = window.setInterval(() => {
        attempts += 1;
        if (render() || attempts >= 30 || currentSymbol !== tvSymbol) {
          window.clearInterval(retry);
          if (currentSymbol === tvSymbol && attempts >= 30 && typeof TradingView === "undefined") {
            freshContainer.textContent = "Chart is temporarily unavailable. Please try again.";
          }
        }
      }, 250);
    }
  }

  function close() {
    const panel = document.getElementById("chart-panel");
    if (panel) panel.classList.remove("open");
    currentSymbol = null;
    document.querySelectorAll(".ticker-cell.active").forEach((c) => c.classList.remove("active"));
  }

  return { open, close };
})();
