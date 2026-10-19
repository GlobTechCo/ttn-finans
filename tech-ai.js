/* Tech & AI archive; the same card and pagination component as Market Analysis. */
(function () {
  const TECH_AI_IDS = new Set([
    "apple-pro-and-tell-october-28-2026-event",
    "sp-global-ai-debt-visibility-hyperscalers-2026",
    "amazon-torchneuron-pytorch-trainium-2026",
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
  function render() {
    const element = document.getElementById("tech-ai-archive");
    if (!element || typeof TTN_ARTICLES === "undefined") return;
    const articles = TTN_ARTICLES.filter(a => a.section === "Tech & AI" || TECH_AI_IDS.has(a.id)).sort((a,b) => new Date(b.date)-new Date(a.date));
    TTNArchive.mount({element, articles, label:"Tech & AI", renderArticle:(a, index) => TTNArchive.card(a, "Tech & AI", "", {eager:index < 2})});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render); else render();
})();

