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
  };

  function categoryForArticle(article) {
    const tickers = article.tickers || [];
    if (article.id?.includes("oil")) return "oil";
    if (article.id?.includes("ai-capex")) return "chips";
    if (article.id?.includes("treasury-yields")) return "bonds";
    if (tickers.some((t) => ["BTC", "ETH"].includes(t))) return "crypto";
    if (tickers.includes("GOLD")) return "gold";
    if (tickers.includes("EUR/USD")) return "forex";
    if (tickers.length) return "stocks";
    return "general";
  }

  function fmtDate(iso) {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  async function render() {
    const el = document.getElementById("analysis-archive");
    if (!el || typeof TTN_ARTICLES === "undefined") return;
    const sorted = [...TTN_ARTICLES].sort((a, b) => new Date(b.date) - new Date(a.date));
    await TTNNews.resolveCategoryPhotos(sorted.map(categoryForArticle));

    el.innerHTML = sorted
      .map((a) => {
        const photo = TTNNews.getCategoryPhoto(categoryForArticle(a), a.id);
        const img = photo
          ? `<img src="${photo}" alt="${TTNNews.escapeAttr(a.title)}" loading="lazy">`
          : `<div class="news-item-thumb-fallback thumb-${categoryForArticle(a)}"></div>`;
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
