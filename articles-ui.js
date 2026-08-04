/**
 * TTN — renders the "TTN Analysis" section (original, in-house articles).
 * Unlike the aggregated news feed, these open with their FULL text in the
 * modal, since TTN owns this content outright.
 */
const TTNArticlesUI = (() => {
  function fmtDate(dateStr) {
    return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  }

  function tickerChipsHtml(article) {
    if (!article.tickers?.length) return "";
    return `<div class="article-tickers">${article.tickers
      .map((label) => {
        const entry = TTN_CONFIG.TICKER_DICTIONARY.find((d) => d.label === label);
        if (!entry) return "";
        return `<span class="article-ticker-tag" data-tv="${entry.tvSymbol}" data-label="${label}"><b>${label}</b></span>`;
      })
      .join("")}</div>`;
  }

  function attachTickerHandlers(root) {
    root.querySelectorAll(".article-ticker-tag").forEach((tag) => {
      tag.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        TTNChart.open(tag.dataset.tv, tag.dataset.label);
      });
    });
  }

  const TREND_ICON = `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="3,17 9,11 13,15 21,5"/><polyline points="15,5 21,5 21,11"/></svg>`;

  function articleThumbHtml(article, heightPx) {
    const style = `width:100%;height:${heightPx}px;border-radius:${heightPx > 150 ? "0" : "5px"};${heightPx <= 150 ? "margin-bottom:12px;" : ""}`;
    if (article.image) {
      const thumbSrc = `${article.image}?auto=compress&cs=tinysrgb&w=400&h=${heightPx * 3}&fit=crop`;
      return `<img src="${thumbSrc}" alt="${TTNNews.escapeAttr(article.title)}" loading="lazy" style="${style}object-fit:cover;">`;
    }
    return `<div class="news-item-thumb-fallback thumb-general" style="${style}">${TREND_ICON}</div>`;
  }

  // Maps each article id to its standalone page (needed so link previews on
  // X/social and Google indexing see a real, unique URL per article instead
  // of everything pointing at index.html).
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
  };

  const HOMEPAGE_LIMIT = 4;

  async function render() {
    const el = document.getElementById("ttn-articles");
    if (!el) return;
    const sorted = [...TTN_ARTICLES].sort((a, b) => new Date(b.date) - new Date(a.date));
    const shown = sorted.slice(0, HOMEPAGE_LIMIT);
    el.innerHTML = shown.map(
      (a) => `
      <article class="analysis-card">
        ${articleThumbHtml(a, 110)}
        <span class="ttn-original-badge">TTN Original</span>
        <h3><a href="${ARTICLE_PAGES[a.id] || "#"}">${a.title}</a></h3>
        <p>${a.dek}</p>
        <div class="news-meta"><span class="source">${a.author}</span><span>${fmtDate(a.date)}</span></div>
        ${tickerChipsHtml(a)}
      </article>`
    ).join("");

    if (sorted.length > HOMEPAGE_LIMIT) {
      el.insertAdjacentHTML(
        "afterend",
        `<a href="analysis.html" class="view-all-analysis">View all ${sorted.length} articles &rarr;</a>`
      );
    }

    attachTickerHandlers(el);
  }

  return { render };
})();

document.addEventListener("DOMContentLoaded", () => TTNArticlesUI.render());
