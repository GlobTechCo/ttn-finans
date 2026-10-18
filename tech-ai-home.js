/* Featured original technology analyses. No changes to TTNNews/news feed. */
(()=>{function init(){const el=document.getElementById("tech-ai-home");if(!el||typeof TTN_ARTICLES==="undefined")return;
const techIds=new Set([
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
const all=TTN_ARTICLES.filter(a=>techIds.has(a.id)).sort((a,b)=>new Date(b.date)-new Date(a.date));
const selected=all.slice(0,4);
el.classList.add('editorial-archive-grid');
el.innerHTML=selected.map(a=>TTNArchive.card(a, 'Tech & AI')).join("")||'<p class="tech-ai-intro">Technology reporting is coming to TTN.</p>';
if(all.length)el.insertAdjacentHTML("afterend",'<p class="tech-ai-view-all"><a href="tech-ai.html" class="view-all-analysis">View all '+all.length+' Tech &amp; AI articles &rarr;</a></p>');
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init()})();
