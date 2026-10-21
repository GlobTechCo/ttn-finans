/* Featured original technology coverage. External news loads independently. */
(() => {
  function render() {
    const element = document.getElementById('tech-ai-home');
    if (!element || typeof TTN_ARTICLES === 'undefined') return;
    const articles = TTN_ARTICLES.filter(a => a.section === 'Tech & AI').sort((a,b) => new Date(b.date)-new Date(a.date));
    element.classList.add('editorial-archive-grid');
    element.innerHTML = articles.slice(0,4).map(a => TTNArchive.card(a,'Tech & AI','',{home:true})).join('');
    if (articles.length > 4) element.insertAdjacentHTML('afterend','<p class="tech-ai-view-all"><a href="tech-ai.html" class="view-all-analysis">View all '+articles.length+' Tech &amp; AI articles &rarr;</a></p>');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',render); else render();
})();
