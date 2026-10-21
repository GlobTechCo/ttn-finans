/**
 * TTN — renders the "TTN Analysis" section (original, in-house articles).
 * Unlike the aggregated news feed, these open with their FULL text in the
 * modal, since TTN owns this content outright.
 */
const TTNArticlesUI = (() => {
  function tickerChipsHtml(article) {
    if (!article.tickers?.length) return "";
    return `<div class="article-tickers">${article.tickers
      .map((label) => {
        const entry = TTN_CONFIG.TICKER_DICTIONARY.find((d) => d.label === label);
        if (!entry) return "";
        return `<span class="article-ticker-tag" role="button" tabindex="0" data-tv="${entry.tvSymbol}" data-label="${label}"><b>${label}</b></span>`;
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

  // Maps each article id to its standalone page (needed so link previews on
  // X/social and Google indexing see a real, unique URL per article instead
  // of everything pointing at index.html).

  // Tech & AI has its own exclusive homepage/archive section.
  const HOMEPAGE_LIMIT = 4;

  async function render() {
    const el = document.getElementById("ttn-articles");
    if (!el) return;
    const sorted = TTN_ARTICLES.filter(a => a.section === "Market Analysis").sort((a, b) => new Date(b.date) - new Date(a.date));
    const shown = sorted.slice(0, HOMEPAGE_LIMIT);
    el.classList.add('editorial-archive-grid');
    el.innerHTML = shown.map(a => TTNArchive.card(a, 'Market Analysis', tickerChipsHtml(a), {home:true})).join('');

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
