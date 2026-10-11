/* Curated from original TTN articles only. The external news aggregator remains unchanged. */
(()=>{const el=document.getElementById("tech-ai-archive");if(!el||typeof TTN_ARTICLES==="undefined")return;
const tags=/\b(ai|artificial intelligence|semiconductor|chip|gpu|nvidia|hyperscaler|data center|quantum|robot|cloud computing|big tech|tech stock)\b/i;
const found=TTN_ARTICLES.filter(a=>tags.test(a.title+" "+a.dek)).sort((a,b)=>new Date(b.date)-new Date(a.date));
function safe(v){return String(v||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
el.innerHTML=found.length?found.map(a=>'<article class="tech-ai-card"><span class="ttn-original-badge">TTN Original</span><h3><a href="'+encodeURIComponent(a.id)+'.html">'+safe(a.title)+'</a></h3><p>'+safe(a.dek)+'</p><p style="margin-top:12px">'+new Date(a.date).toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})+'</p></article>').join(""):"<p>Original Tech & AI reporting is being prepared.</p>";
})();