/* Original TTN technology section; independent of external news aggregation. */
(()=>{const el=document.getElementById("tech-ai-archive");if(!el||typeof TTN_ARTICLES==="undefined")return;
const terms=/\b(ai|artificial intelligence|semiconductor|chip|gpu|nvidia|hyperscaler|data center|data centers|quantum|robot|cloud computing|big tech|tech stock)\b/i;
const escape=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const articles=TTN_ARTICLES.filter(a=>terms.test(a.title+" "+a.dek)).sort((a,b)=>new Date(b.date)-new Date(a.date));
const datetime=d=>{const n=new Date(d);return Number.isNaN(n.valueOf())?"":n.toISOString().slice(0,10)};
el.innerHTML=articles.length?articles.map(a=>{
 const date=datetime(a.date), url=encodeURIComponent(a.id)+".html";
 return '<article class="tech-ai-card"><span class="ttn-original-badge">TTN Original</span><h3><a href="'+url+'">'+escape(a.title)+'</a></h3><p>'+escape(a.dek)+'</p><p style="margin-top:12px"><time datetime="'+date+'">'+new Date(a.date).toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})+'</time></p></article>';
}).join(""):"<p>Original technology reporting is being prepared.</p>";
})();