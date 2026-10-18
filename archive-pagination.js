/* Shared navigation for the two original editorial archives. */
window.TTNArchive = {
  card(article, section, extras = "", options = {}) {
    const escape = value => String(value || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
    const url = encodeURIComponent(article.id) + ".html";
    const image = article.image
      ? `<img src="${escape(article.imageSmall || article.image)}"${article.imageSrcset ? ` srcset="${escape(article.imageSrcset)}" sizes="${options.home ? '(max-width: 560px) calc(100vw - 40px), (max-width: 1050px) calc((100vw - 60px) / 2), 290px' : '(max-width: 700px) calc(100vw - 36px), 400px'}"` : ""} alt="${escape(article.imageAlt || article.title)}" width="640" height="360" loading="${options.eager ? 'eager' : 'lazy'}" decoding="async">`
      : '<span class="archive-image-fallback" aria-hidden="true"></span>';
    return `<article class="editorial-archive-card"><a class="editorial-archive-media" href="${url}" aria-label="${escape(article.title)}">${image}</a><div class="editorial-archive-content"><span class="ttn-original-badge">${escape(section)}</span><h3><a href="${url}">${escape(article.title)}</a></h3><p class="editorial-dek">${escape(article.dek)}</p><div class="editorial-meta">${TTNEditorialMeta.html(article)}</div>${extras}</div></article>`;
  },

  mount({ element, articles, renderArticle, label, pageSize = 12 }) {
    element.classList.add("editorial-archive-grid");
    const summary = document.createElement("p");
    summary.className = "archive-summary";
    summary.setAttribute("role", "status");
    summary.setAttribute("aria-live", "polite");
    const navigation = document.createElement("nav");
    navigation.className = "archive-pagination";
    navigation.setAttribute("aria-label", label + " pages");
    element.before(summary);
    element.after(navigation);
    element.setAttribute("tabindex", "-1");
    const totalPages = Math.max(1, Math.ceil(articles.length / pageSize));
    function pageUrl(page) {
      const url = new URL(window.location.href);
      if (page === 1) url.searchParams.delete("page");
      else url.searchParams.set("page", page);
      url.hash = "";
      return url.pathname + url.search;
    }
    function render(moveFocus = false) {
      const requested = new URLSearchParams(window.location.search).get("page");
      const page = Math.min(totalPages, Math.max(1, /^\d+$/.test(requested || "") ? Number(requested) : 1));
      if (requested !== null && requested !== String(page)) {
        window.history.replaceState(null, "", pageUrl(page));
      }
      const start = (page - 1) * pageSize;
      const end = Math.min(start + pageSize, articles.length);
      summary.textContent = articles.length
        ? `${articles.length} articles · Showing ${start + 1}–${end} · Page ${page} of ${totalPages}`
        : "0 articles";
      element.innerHTML = articles.slice(start, end).map((article, index) => renderArticle(article, index)).join("") || "<p>No articles are available yet.</p>";
      const link = (n, text, extra = "") => `<a href="${pageUrl(n).replace(/&/g, "&amp;").replace(/\"/g, "&quot;")}" ${extra}>${text}</a>`;
      const pages = new Set([1, totalPages, page - 1, page, page + 1]);
      const numbers = [...pages].filter(n => n >= 1 && n <= totalPages).sort((a, b) => a - b);
      let previous = 0;
      const numbered = numbers.map(n => {
        const gap = previous && n > previous + 1 ? '<span class="pagination-gap" aria-hidden="true">…</span>' : "";
        previous = n;
        return gap + link(n, n, n === page ? 'aria-current="page" aria-label="Page ' + n + ', current page"' : 'aria-label="Page ' + n + '"');
      }).join("");
      navigation.hidden = totalPages === 1;
      navigation.innerHTML = (page > 1 ? link(page - 1, "Previous", 'rel="prev"') : '<span aria-disabled="true">Previous</span>')
        + numbered + (page < totalPages ? link(page + 1, "Next", 'rel="next"') : '<span aria-disabled="true">Next</span>');
      if (moveFocus) {
        element.focus({ preventScroll: true });
        summary.scrollIntoView({ block: "start" });
      }
    }
    navigation.addEventListener("click", event => {
      const anchor = event.target.closest("a");
      if (!anchor || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      window.history.pushState(null, "", anchor.getAttribute("href"));
      render(true);
    });
    window.addEventListener("popstate", () => render(true));
    render();
  }
};
