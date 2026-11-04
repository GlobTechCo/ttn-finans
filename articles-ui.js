/**
 * TTN — renders the "TTN Analysis" section (original, in-house articles).
 * Unlike the aggregated news feed, these open with their FULL text in the
 * modal, since TTN owns this content outright.
 */
const TTNArticlesUI = (() => {
  // Maps each article id to its standalone page (needed so link previews on
  // X/social and Google indexing see a real, unique URL per article instead
  // of everything pointing at index.html).

  // Tech & AI has its own exclusive homepage/archive section.
  const HOMEPAGE_LIMIT = 4;

  async function render() {
    const el = document.getElementById("ttn-articles");
    if (!el) return;
    const sorted = TTN_ARTICLES.filter(a => a.section === "Market Analysis").sort((a, b) => new Date(b.date) - new Date(a.date));
    const shown = sorted.slice(0, HOMEPAGE_LIMIT);
    el.classList.add('editorial-archive-grid');
    el.innerHTML = shown.map(a => TTNArchive.card(a, 'Market Analysis', '', {home:true})).join('');

    if (sorted.length > HOMEPAGE_LIMIT) {
      el.insertAdjacentHTML(
        "afterend",
        `<a href="analysis.html" class="view-all-analysis">View all ${sorted.length} market analysis articles &rarr;</a>`
      );
    }

  }

  return { render };
})();

document.addEventListener("DOMContentLoaded", () => TTNArticlesUI.render());
