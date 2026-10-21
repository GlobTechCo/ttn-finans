/* Canonical catalog sections keep the three editorial archives exclusive. */
(() => {
  function render() {
    const element = document.getElementById('analysis-archive');
    if (!element || typeof TTN_ARTICLES === 'undefined') return;
    const articles = TTN_ARTICLES.filter(a => a.section === 'Market Analysis').sort((a,b) => new Date(b.date)-new Date(a.date));
    TTNArchive.mount({element, articles, label:'Market Analysis', renderArticle:(a,index) => TTNArchive.card(a,'Market Analysis','',{eager:index<2})});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',render); else render();
})();
