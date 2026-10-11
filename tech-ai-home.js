/* Featured original technology analyses. No changes to TTNNews/news feed. */
(()=>{function init(){const el=document.getElementById("tech-ai-home");if(!el||typeof TTN_ARTICLES==="undefined")return;
const term=/\b(ai|artificial intelligence|semiconductor|chip|gpu|nvidia|hyperscaler|data center|quantum|robot|cloud computing|big tech|tech stock)\b/i;
const safe=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const selected=TTN_ARTICLES.filter(a=>term.test(a.title+" "+a.dek)).sort((a,b)=>new Date(b.date)-new Date(a.date)).slice(0,4);
el.innerHTML=selected.map(a=>'<article class="tech-ai-card"><span class="ttn-original-badge">TTN Original</span><h3><a href="'+encodeURIComponent(a.id)+'.html">'+safe(a.title)+'</a></h3><p>'+safe(a.dek)+'</p></article>').join("")||'<p class="tech-ai-intro">Technology reporting is coming to TTN.</p>';}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init()})();