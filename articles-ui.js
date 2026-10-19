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
  const TECH_AI_IDS = new Set([
    "ai-agents-website-breaches-norforge-october-2026",
    "anthropic-public-benefit-fund-five-percent-shares-2026",
    "meta-commercial-terms-crawling-publishers-clarification-2026",
    "tiktok-musk-documentary-account-suspension-2026",

    "china-solar-manufacturing-technology-export-controls-2026",
    "replit-openai-preferred-partner-claude-choice-2026",
    "ai-agents-websites-block-access-2026",
    "tesla-slovakia-assisted-driving-approval-2026",
    "tesla-fsd-class-certification-appeal-october-2026",
    "china-ai-technology-export-controls-draft-2026",
    "ai-agents-india-cert-in-security-warning-2026",
    "iphone-duo-preorder-delays-january-2027",
    "germany-nvidia-industrial-ai-agreement-2026",
    "meta-muse-spark-open-coding-model-2026",
    "google-news-ai-pilot-publisher-licensing-2026",
    "tsmc-q3-2026-ai-chip-demand",
    "ftc-openai-anthropic-safety-subpoenas-2026",
    "cohere-aisle-cybersecurity-deal-2026",
    "asml-q3-2026-ai-demand",
    "apple-homeview-siri-ai-2026",
    "scaleway-amd-sweden-ai-supercomputer",
    "anthropic-ai-self-replication-iot-2026",
    "broadcom-ai-networking-ocp-2026",
    "ai-inference-unit-economics-2026",
    "enterprise-ai-data-security-2026",
    "ai-search-publisher-economics-2026",
    "robotics-ai-factory-roi-2026",
    "ai-data-center-electricity-demand-2026",
    "ai-capex-nasdaq-correction",
    "circular-ai-financing-explained",
    "ai-monetization-gap-explained",
    "ai-agents-enterprise-roi-2026",
    "ai-chips-bottlenecks-2026",
    "small-business-ai-adoption-2026",
]);
  const HOMEPAGE_LIMIT = 4;

  async function render() {
    const el = document.getElementById("ttn-articles");
    if (!el) return;
    const sorted = TTN_ARTICLES.filter(a => !TECH_AI_IDS.has(a.id)).sort((a, b) => new Date(b.date) - new Date(a.date));
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
