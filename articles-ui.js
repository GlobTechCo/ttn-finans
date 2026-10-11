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
      const thumbSrc = article.image; // Use local originals directly; do not append Pexels-specific query parameters.
      return `<img src="${thumbSrc}" alt="${TTNNews.escapeAttr(article.title)}" loading="lazy" style="${style}object-fit:cover;">`;
    }
    return `<div class="news-item-thumb-fallback thumb-general" style="${style}">${TREND_ICON}</div>`;
  }

  // Maps each article id to its standalone page (needed so link previews on
  // X/social and Google indexing see a real, unique URL per article instead
  // of everything pointing at index.html).

  // Tech & AI has its own exclusive homepage/archive section.
  const TECH_AI_IDS = new Set(["ai-inference-unit-economics-2026","enterprise-ai-data-security-2026","ai-search-publisher-economics-2026","robotics-ai-factory-roi-2026","ai-data-center-electricity-demand-2026","ai-capex-nasdaq-correction","circular-ai-financing-explained","ai-monetization-gap-explained","ai-agents-enterprise-roi-2026","ai-chips-bottlenecks-2026","small-business-ai-adoption-2026"]);
  const HOMEPAGE_LIMIT = 4;

  async function render() {
    const el = document.getElementById("ttn-articles");
    if (!el) return;
    const sorted = TTN_ARTICLES.filter(a => !TECH_AI_IDS.has(a.id)).sort((a, b) => new Date(b.date) - new Date(a.date));
    const shown = sorted.slice(0, HOMEPAGE_LIMIT);
    el.innerHTML = shown.map(
      (a) => `
      <article class="analysis-card">
        ${articleThumbHtml(a, 110)}
        <span class="ttn-original-badge">TTN Original</span>
        <h3><a href="${a.id}.html">${a.title}</a></h3>
        <p>${a.dek}</p>
        <div class="news-meta"><span class="source">${a.author}</span><span>${fmtDate(a.date)}</span></div>
        ${tickerChipsHtml(a)}
      </article>`
    ).join("");

    if (sorted.length > HOMEPAGE_LIMIT) {
      el.insertAdjacentHTML(
        "afterend",
        `<a href="analysis.html" class="view-all-analysis">View all ${sorted.length} market analysis articles &rarr;</a>`
      );
    }

    attachTickerHandlers(el);
  }

  return { render };
})();

document.addEventListener("DOMContentLoaded", () => TTNArticlesUI.render());
