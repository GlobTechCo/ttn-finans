/**
 * TTN - renders the full "TTN Analysis" archive list on analysis.html.
 * Lightweight sibling to articles-ui.js: same data source (articles.js),
 * simpler list layout instead of the homepage's card grid.
 */
(function () {

  function fmtDate(iso) {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  // Keep Tech & AI exclusively in its own archive; do not remove source articles.
  const TECH_AI_IDS = new Set([,"iphone-duo-preorder-delays-january-2027","germany-nvidia-industrial-ai-agreement-2026","meta-muse-spark-open-coding-model-2026","google-news-ai-pilot-publisher-licensing-2026","tsmc-q3-2026-ai-chip-demand","ftc-openai-anthropic-safety-subpoenas-2026","cohere-aisle-cybersecurity-deal-2026","asml-q3-2026-ai-demand","apple-homeview-siri-ai-2026","scaleway-amd-sweden-ai-supercomputer","anthropic-ai-self-replication-iot-2026","broadcom-ai-networking-ocp-2026","ai-inference-unit-economics-2026","enterprise-ai-data-security-2026","ai-search-publisher-economics-2026","robotics-ai-factory-roi-2026","ai-data-center-electricity-demand-2026","ai-capex-nasdaq-correction","circular-ai-financing-explained","ai-monetization-gap-explained","ai-agents-enterprise-roi-2026","ai-chips-bottlenecks-2026","small-business-ai-adoption-2026"]);

  function render() {
    const el = document.getElementById("analysis-archive");
    if (!el || typeof TTN_ARTICLES === "undefined") return;
    const sorted = TTN_ARTICLES.filter(a => !TECH_AI_IDS.has(a.id)).sort((a, b) => new Date(b.date) - new Date(a.date));

    el.innerHTML = sorted
      .map((a) => {
        const img = a.image
          ? `<img src="${a.image.startsWith("http") ? a.image + "?auto=compress&cs=tinysrgb&w=300&h=225&fit=crop" : a.image}" alt="${TTNNews.escapeAttr(a.title)}" loading="lazy">`
          : `<div class="news-item-thumb-fallback thumb-general"></div>`;
        return `
        <div class="analysis-list-item">
          ${img}
          <div>
            <span class="ttn-original-badge">TTN Original</span>
            <h3><a href="${a.id}.html">${a.title}</a></h3>
            <p>${a.dek}</p>
            <div class="news-meta"><span class="source">${a.author}</span><span>${fmtDate(a.date)}</span></div>
          </div>
        </div>`;
      })
      .join("");
  }

  document.addEventListener("DOMContentLoaded", render);
})();
