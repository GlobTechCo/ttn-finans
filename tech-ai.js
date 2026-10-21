/* Technology archive; catalog classification is authoritative. */
(() => {
  function render() {
    const element = document.getElementById('tech-ai-archive');
    if (!element || typeof TTN_ARTICLES === 'undefined') return;
    const articles = TTN_ARTICLES.filter(a => a.section === 'Tech & AI').sort((a,b) => new Date(b.date)-new Date(a.date));
    TTNArchive.mount({element, articles, label:'Tech & AI', renderArticle:(a,index) => TTNArchive.card(a,'Tech & AI','',{eager:index<2})});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',render); else render();
})();
