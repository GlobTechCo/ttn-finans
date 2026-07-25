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

  function categoryForArticle(article) {
    const tickers = article.tickers || [];
    if (tickers.some((t) => ["BTC", "ETH"].includes(t))) return "crypto";
    if (tickers.includes("GOLD")) return "gold";
    if (tickers.includes("EUR/USD")) return "forex";
    if (tickers.length) return "stocks";
    return "general";
  }

  function articleThumbHtml(article, heightPx) {
    const category = categoryForArticle(article);
    const photo = TTNNews.getCategoryPhoto(category, article.id);
    const style = `width:100%;height:${heightPx}px;border-radius:${heightPx > 150 ? "0" : "5px"};${heightPx <= 150 ? "margin-bottom:12px;" : ""}`;
    if (photo) {
      return `<img src="${photo}" alt="" loading="lazy" style="${style}object-fit:cover;">`;
    }
    return `<div class="news-item-thumb-fallback thumb-${category}" style="${style}">${TREND_ICON}</div>`;
  }

  // Maps each article id to its standalone page (needed so link previews on
  // X/social and Google indexing see a real, unique URL per article instead
  // of everything pointing at index.html).
  const ARTICLE_PAGES = {
    "fed-policy-2026": "fed-policy-2026.html",
    "bitcoin-halving-cycles": "bitcoin-halving-cycles.html",
    "gold-hedge-explainer": "gold-hedge-explainer.html",
  };

  async function render() {
    const el = document.getElementById("ttn-articles");
    if (!el) return;
    await TTNNews.resolveCategoryPhotos(TTN_ARTICLES.map(categoryForArticle));
    el.innerHTML = TTN_ARTICLES.map(
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

    attachTickerHandlers(el);
  }

  return { render };
})();

document.addEventListener("DOMContentLoaded", () => TTNArticlesUI.render());
