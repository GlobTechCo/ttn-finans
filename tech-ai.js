/* Original TTN technology section; independent of external news aggregation. */
(()=>{const el=document.getElementById("tech-ai-archive");if(!el||typeof TTN_ARTICLES==="undefined")return;
const techIds=new Set(["ai-inference-unit-economics-2026","enterprise-ai-data-security-2026","ai-search-publisher-economics-2026","robotics-ai-factory-roi-2026","ai-data-center-electricity-demand-2026","ai-capex-nasdaq-correction","circular-ai-financing-explained","ai-monetization-gap-explained","ai-agents-enterprise-roi-2026","ai-chips-bottlenecks-2026","small-business-ai-adoption-2026"]);
const escape=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const articles=TTN_ARTICLES.filter(a=>techIds.has(a.id)).sort((a,b)=>new Date(b.date)-new Date(a.date));
const datetime=d=>{const n=new Date(d);return Number.isNaN(n.valueOf())?"":n.toISOString().slice(0,10)};
el.innerHTML=articles.length?articles.map(a=>{
 const date=datetime(a.date), url=encodeURIComponent(a.id)+".html";
 return '<article class="tech-ai-card"><a class="tech-ai-card-media" href="'+url+'"><img src="'+escape(a.image)+'" alt="'+escape("AI-generated editorial photo for "+a.title)+'" width="640" height="360" loading="lazy" decoding="async"></a><div class="tech-ai-card-content"><span class="ttn-original-badge">TTN Original · Tech &amp; AI</span><h3><a href="'+url+'">'+escape(a.title)+'</a></h3><p>'+escape(a.dek)+'</p><p class="tech-ai-card-meta"><time datetime="'+date+'">'+new Date(a.date).toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})+'</time></p></div></article>';
}).join(""):"<p>Original technology reporting is being prepared.</p>";
})();