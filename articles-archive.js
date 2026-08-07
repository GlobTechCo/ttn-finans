/**
 * TTN - renders the full "TTN Analysis" archive list on analysis.html.
 * Lightweight sibling to articles-ui.js: same data source (articles.js),
 * simpler list layout instead of the homepage's card grid.
 */
(function () {
  const ARTICLE_PAGES = {
    "fed-policy-2026": "fed-policy-2026.html",
    "bitcoin-halving-cycles": "bitcoin-halving-cycles.html",
    "gold-hedge-explainer": "gold-hedge-explainer.html",
    "oil-shock-market-ripple": "oil-shock-market-ripple.html",
    "ai-capex-nasdaq-correction": "ai-capex-nasdaq-correction.html",
    "treasury-yields-spike-2026": "treasury-yields-spike-2026.html",
    "stablecoins-explained-depeg-risk": "stablecoins-explained-depeg-risk.html",
    "earnings-beat-miss-explained": "earnings-beat-miss-explained.html",
    "bitcoin-etf-institutional-adoption": "bitcoin-etf-institutional-adoption.html",
    "eur-usd-rate-differential-explained": "eur-usd-rate-differential-explained.html",
    "crypto-liquidation-leverage-explained": "crypto-liquidation-leverage-explained.html",
    "vix-fear-index-explained": "vix-fear-index-explained.html",
    "short-squeeze-mechanics-explained": "short-squeeze-mechanics-explained.html",
    "dollar-cost-averaging-vs-lump-sum": "dollar-cost-averaging-vs-lump-sum.html",
    "correlation-breakdown-diversification": "correlation-breakdown-diversification.html",
    "crypto-taxes-us-explained": "crypto-taxes-us-explained.html",
    "cpi-inflation-explained": "cpi-inflation-explained.html",
    "options-calls-puts-explained": "options-calls-puts-explained.html",
    "stock-buybacks-explained": "stock-buybacks-explained.html",
    "prediction-markets-explained": "prediction-markets-explained.html",
    "ipo-process-explained": "ipo-process-explained.html",
    "market-cap-explained": "market-cap-explained.html",
    "insider-selling-explained": "insider-selling-explained.html",
    "nonfarm-payrolls-jobs-report-explained": "nonfarm-payrolls-jobs-report-explained.html",
    "mergers-acquisitions-explained": "mergers-acquisitions-explained.html",
    "yield-curve-inversion-recession-signal": "yield-curve-inversion-recession-signal.html",
    "dxy-dollar-index-explained": "dxy-dollar-index-explained.html",
    "sector-rotation-explained": "sector-rotation-explained.html",
    "etf-creation-redemption-mechanism": "etf-creation-redemption-mechanism.html",
  };

  function fmtDate(iso) {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function render() {
    const el = document.getElementById("analysis-archive");
    if (!el || typeof TTN_ARTICLES === "undefined") return;
    const sorted = [...TTN_ARTICLES].sort((a, b) => new Date(b.date) - new Date(a.date));

    el.innerHTML = sorted
      .map((a) => {
        const img = a.image
          ? `<img src="${a.image}?auto=compress&cs=tinysrgb&w=300&h=225&fit=crop" alt="${TTNNews.escapeAttr(a.title)}" loading="lazy">`
          : `<div class="news-item-thumb-fallback thumb-general"></div>`;
        return `
        <div class="analysis-list-item">
          ${img}
          <div>
            <span class="ttn-original-badge">TTN Original</span>
            <h3><a href="${ARTICLE_PAGES[a.id] || "#"}">${a.title}</a></h3>
            <p>${a.dek}</p>
            <div class="news-meta"><span class="source">${a.author}</span><span>${fmtDate(a.date)}</span></div>
          </div>
        </div>`;
      })
      .join("");
  }

  document.addEventListener("DOMContentLoaded", render);
})();
