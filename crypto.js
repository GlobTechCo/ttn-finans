/* Crypto uses the shared cards; news and explainers remain distinct. */
(() => {
  function render() {
    if (typeof TTN_ARTICLES === 'undefined') return;
    const articles = TTN_ARTICLES.filter(a => a.section === 'Crypto').sort((a,b) => new Date(b.date)-new Date(a.date));
    const home = document.getElementById('crypto-home');
    if (home) {
      home.classList.add('editorial-archive-grid');
      home.innerHTML = articles.filter(a => a.format === 'news').slice(0,4).map(a => TTNArchive.card(a,'Crypto','',{home:true})).join('');
      if (articles.length > 4) home.insertAdjacentHTML('afterend','<a href="crypto.html" class="view-all-analysis">View all '+articles.length+' Crypto articles &rarr;</a>');
    }
    const element = document.getElementById('crypto-archive');
    if (element) TTNArchive.mount({element, articles:articles.filter(a=>a.format==='news'), label:'Crypto news', renderArticle:(a,index)=>TTNArchive.card(a,'Crypto','',{eager:index<2})});
    const explainers = document.getElementById('crypto-explainers');
    if (explainers) explainers.innerHTML = articles.filter(a=>a.format==='explainer').slice(0,4).map(a=>TTNArchive.card(a,'Crypto explainer')).join('');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',render); else render();
})();
