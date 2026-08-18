/**
 * TTN - renders the full "TTN Analysis" archive list on analysis.html.
 * Lightweight sibling to articles-ui.js: same data source (articles.js),
 * simpler list layout instead of the homepage's card grid.
 */
(function () {

  function fmtDate(iso) {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function render() {
    const el = document.getElementById("analysis-archive");
    if (!el || typeof TTN_ARTICLES === "undefined") return;
    const sorted = [...TTN_ARTICLES].sort((a, b) => new Date(b.date) - new Date(a.date));

    el.innerHTML = sorted
      .map((a) => {
        const img = a.image
          ? `<img src="${a.image}?auto=compress&cs=tinysrgb&w=300&h=225&fit=crop" alt="${TTNNews.escapeAttr(a.title)}" loading="lazy">`
          : `<div class="news-item-thumb-fallback thumb-general"></div>`;
        return `
        <div class="analysis-list-item">
          ${img}
          <div>
            <span class="ttn-original-badge">TTN Original</span>
            <h3><a href="${a.id}.html">${a.title}</a></h3>
            <p>${a.dek}</p>
            <div class="news-meta"><span class="source">${a.author}</span><span>${fmtDate(a.date)}</span></div>
          </div>
        </div>`;
      })
      .join("");
  }

  document.addEventListener("DOMContentLoaded", render);
})();
