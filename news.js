/**
 * TTN — news module
 * Aggregates real RSS feeds (via rss2json.com) plus Finnhub, shows
 * headline + short excerpt FROM THE SOURCE + a link to the original.
 * No automatic "rewriting" — aggregation with attribution only.
 */
const TTNNews = (() => {
  let allItems = [];
  let itemsIndex = {}; // link -> item, used to open the in-site modal
  const tickerPriceCache = {}; // label -> changePct (number) | null

  async function resolveTickerPrices(items) {
    const needed = new Map(); // label -> dictionary entry
    items.forEach((item) => {
      detectTickers(`${item.title} ${item.desc}`).forEach((entry) => {
        if (!(entry.label in tickerPriceCache) && !needed.has(entry.label)) {
          needed.set(entry.label, entry);
        }
      });
    });
    if (!needed.size) return;

    const coingeckoIds = [];
    const finnhubEntries = [];

    needed.forEach((entry, label) => {
      if (entry.trackedId) {
        const pct = TTNTickers.getChangePct(entry.trackedId);
        tickerPriceCache[label] = pct;
      } else if (entry.coingeckoId) {
        coingeckoIds.push(entry);
      } else if (TTN_CONFIG.FINNHUB_KEY) {
        finnhubEntries.push(entry);
      } else {
        tickerPriceCache[label] = null; // no data source available — chip shows without %
      }
    });

    if (coingeckoIds.length) {
      try {
        const ids = coingeckoIds.map((e) => e.coingeckoId).join(",");
        const res = await fetch(
          `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true`
        );
        const data = await res.json();
        coingeckoIds.forEach((e) => {
          tickerPriceCache[e.label] = data[e.coingeckoId]?.usd_24h_change ?? null;
        });
      } catch (e) {
        coingeckoIds.forEach((e) => (tickerPriceCache[e.label] = null));
      }
    }

    if (finnhubEntries.length) {
      const symbol = (tv) => tv.split(":")[1]?.replace(".", "-") || tv;
      await Promise.all(
        finnhubEntries.slice(0, 8).map(async (e) => {
          try {
            const res = await fetch(
              `https://finnhub.io/api/v1/quote?symbol=${encodeURIComponent(symbol(e.tvSymbol))}&token=${TTN_CONFIG.FINNHUB_KEY}`
            );
            const data = await res.json();
            tickerPriceCache[e.label] = typeof data.dp === "number" ? data.dp : null;
          } catch (err) {
            tickerPriceCache[e.label] = null;
          }
        })
      );
    }
  }

  function ensureModal() {
    let modal = document.getElementById("news-modal");
    if (modal) return modal;
    modal = document.createElement("div");
    modal.id = "news-modal";
    modal.className = "news-modal";
    modal.innerHTML = `
      <div class="news-modal-overlay" id="news-modal-overlay"></div>
      <div class="news-modal-panel">
        <button class="news-modal-close" id="news-modal-close" aria-label="Close">×</button>
        <div id="news-modal-body"></div>
      </div>`;
    document.body.appendChild(modal);
    // All three ways of dismissing the modal (X button, tapping the overlay,
    // Escape key) go through history.back() rather than closing directly.
    // That keeps a single source of truth: the modal is only ever actually
    // hidden by the popstate handler below, so the phone's physical/browser
    // back button behaves exactly the same as tapping X — it reveals the
    // homepage underneath instead of navigating to whatever page happened
    // to be earlier in browser history.
    modal.querySelector("#news-modal-overlay").addEventListener("click", requestClose);
    modal.querySelector("#news-modal-close").addEventListener("click", requestClose);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("open")) requestClose();
    });
    window.addEventListener("popstate", (e) => {
      hideModal();
    });
    return modal;
  }

  function requestClose() {
    // Pops the history entry pushed when the modal opened; the popstate
    // listener above then actually hides the modal. As a safety net, if
    // popstate doesn't fire quickly (some in-app/embedded browsers have
    // limited history support), we force-close directly so the X button
    // never gets stuck as the only way out.
    const modal = document.getElementById("news-modal");
    history.back();
    setTimeout(() => {
      if (modal && modal.classList.contains("open")) hideModal();
    }, 350);
  }

  function hideModal() {
    const modal = document.getElementById("news-modal");
    if (modal) modal.classList.remove("open");
    document.body.classList.remove("modal-open");
  }

  function showModal() {
    const modal = document.getElementById("news-modal");
    if (!modal.classList.contains("open")) {
      history.pushState({ ttnModal: true }, "", location.href);
    }
    modal.classList.add("open");
    document.body.classList.add("modal-open");
  }

  function openModal(link) {
    const item = itemsIndex[link];
    if (!item) return;
    const modal = ensureModal();
    const hasDesc = item.desc && item.desc.trim().length > 0;
    document.getElementById("news-modal-body").innerHTML = `
      ${thumbHtml(item, "lg")}
      <div class="news-modal-meta"><span class="source">${item.source}</span> · ${timeAgo(item.pubDate)}</div>
      <h2>${item.title}</h2>
      ${hasDesc ? `<p>${item.desc}${item.desc.length >= 220 ? "…" : ""}</p>` : `<p style="color:var(--text-dim);">${item.source} didn't include a preview for this story.</p>`}
      ${tickerTagsHtml(item)}
      <p class="news-modal-note">We show the original headline and a short excerpt with full attribution. The complete article stays on the publisher's own site, in line with copyright and licensing terms.</p>
      <a href="${item.link}" target="_blank" rel="noopener" class="news-modal-source-link">Read full article on ${item.source} →</a>
    `;
    attachTagHandlers(modal);
    attachThumbFallbacks(modal);
    showModal();
  }

  function stripHtml(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html || "";
    return (tmp.textContent || tmp.innerText || "").trim();
  }

  // Safely escape text for use inside an HTML attribute (e.g. alt="...").
  // Needed because headline titles can contain quotes or & that would
  // otherwise break out of the attribute.
  function escapeAttr(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function extractFirstImage(html) {
    if (!html) return null;
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    const img = tmp.querySelector("img");
    return img?.getAttribute("src") || null;
  }

  function detectTickers(text) {
    const lower = text.toLowerCase();
    const found = [];
    TTN_CONFIG.TICKER_DICTIONARY.forEach((entry) => {
      const hit = entry.match.some((kw) => lower.includes(kw));
      if (hit && !found.some((f) => f.label === entry.label)) {
        found.push(entry);
      }
    });
    return found.slice(0, 5);
  }

  function timeAgo(dateStr) {
    const diffMs = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hr ago`;
    return `${Math.floor(hrs / 24)} d ago`;
  }

  async function fetchFeed(feed) {
    const proxy = "https://api.rss2json.com/v1/api.json";
    const keyParam = TTN_CONFIG.RSS2JSON_KEY ? `&api_key=${TTN_CONFIG.RSS2JSON_KEY}` : "";
    const url = `${proxy}?rss_url=${encodeURIComponent(feed.url)}${keyParam}`;
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (data.status !== "ok") return [];
      return data.items.map((item) => ({
        title: item.title,
        desc: stripHtml(item.description).slice(0, 220),
        link: item.link,
        image: item.thumbnail || item.enclosure?.link || extractFirstImage(item.description) || null,
        pubDate: item.pubDate,
        source: feed.name,
      }));
    } catch (e) {
      return [];
    }
  }

  async function fetchFinnhub() {
    if (!TTN_CONFIG.FINNHUB_KEY) return [];
    try {
      const res = await fetch(
        `https://finnhub.io/api/v1/news?category=general&token=${TTN_CONFIG.FINNHUB_KEY}`
      );
      const data = await res.json();
      if (!Array.isArray(data)) return [];
      return data.slice(0, 25).map((item) => ({
        title: item.headline,
        desc: stripHtml(item.summary || "").slice(0, 220),
        link: item.url,
        image: item.image || null,
        pubDate: new Date(item.datetime * 1000).toISOString(),
        source: item.source ? `Finnhub · ${item.source}` : "Finnhub",
      }));
    } catch (e) {
      return [];
    }
  }

  async function fetchCurrents() {
    if (!TTN_CONFIG.CURRENTS_KEY) return [];
    try {
      const res = await fetch(
        `https://api.currentsapi.services/v1/search?category=economy_business_finance&language=en&page_size=25`,
        { headers: { Authorization: TTN_CONFIG.CURRENTS_KEY } }
      );
      const data = await res.json();
      if (!Array.isArray(data.news)) return [];
      return data.news.map((item) => ({
        title: item.title,
        desc: stripHtml(item.description || "").slice(0, 220),
        link: item.url,
        image: item.image && item.image !== "None" ? item.image : null,
        pubDate: item.published,
        source: "Currents",
      }));
    } catch (e) {
      return [];
    }
  }

  async function fetchApitube() {
    if (!TTN_CONFIG.APITUBE_KEY) return [];
    try {
      const res = await fetch(
        `https://api.apitube.io/v1/news/everything?title=stocks,markets,crypto,economy&language.code=en&per_page=25`,
        { headers: { "X-API-Key": TTN_CONFIG.APITUBE_KEY } }
      );
      const data = await res.json();
      const results = data.results || data.articles || [];
      if (!Array.isArray(results)) return [];
      return results.map((item) => ({
        title: item.title,
        desc: stripHtml(item.description || item.summary || "").slice(0, 220),
        link: item.href || item.url || item.link,
        // APITube's exact image field wasn't fully confirmed against a live
        // response when this was written — checking a few likely names so
        // this degrades gracefully to the icon fallback rather than break.
        image: item.image?.url || item.image || item.media?.thumbnail || null,
        pubDate: item.published_at || item.publishedAt || item.date,
        source: item.source?.name ? `APITube · ${item.source.name}` : "APITube",
      }));
    } catch (e) {
      return [];
    }
  }

  function tickerTagsHtml(item) {
    const tickers = detectTickers(`${item.title} ${item.desc}`);
    if (!tickers.length) return "";
    return `<div class="article-tickers">${tickers
      .map((t) => {
        const pct = tickerPriceCache[t.label];
        const pctHtml =
          typeof pct === "number"
            ? `<span class="${pct >= 0 ? "up" : "down"}">${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%</span>`
            : "";
        return `<span class="article-ticker-tag" data-tv="${t.tvSymbol}" data-label="${t.label}"><b>${t.label}</b>${pctHtml}</span>`;
      })
      .join("")}</div>`;
  }

  const TREND_ICON = `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="3,17 9,11 13,15 21,5"/><polyline points="15,5 21,5 21,11"/></svg>`;

  function categoryFor(item) {
    const tickers = detectTickers(`${item.title} ${item.desc}`);
    if (!tickers.length) return "general";
    const sym = tickers[0].tvSymbol;
    if (sym.startsWith("BINANCE:")) return "crypto";
    if (sym.startsWith("FX:")) return "forex";
    if (sym === "TVC:GOLD" || sym === "TVC:USOIL") return "gold";
    return "stocks";
  }

  const categoryPhotoCache = {}; // category -> array of photo URLs

  async function resolveCategoryPhotos(categories) {
    if (!TTN_CONFIG.PEXELS_KEY) return;
    const needed = [...new Set(categories)].filter((c) => !(c in categoryPhotoCache));
    if (!needed.length) return;
    await Promise.all(
      needed.map(async (category) => {
        const query = TTN_CONFIG.CATEGORY_PHOTO_QUERIES[category] || TTN_CONFIG.CATEGORY_PHOTO_QUERIES.general;
        try {
          const res = await fetch(
            `https://api.pexels.com/v1/search?query=${encodeURIComponent(query)}&per_page=24&orientation=landscape`,
            { headers: { Authorization: TTN_CONFIG.PEXELS_KEY } }
          );
          const data = await res.json();
          const urls = (data.photos || []).map((p) => p.src?.medium).filter(Boolean);
          categoryPhotoCache[category] = urls.length ? urls : null;
        } catch (e) {
          categoryPhotoCache[category] = null;
        }
      })
    );
  }

  // Simple stable hash so the same item always picks the same photo from
  // the pool (no flicker on re-render) while different items spread out
  // across the available photos instead of all sharing photo #1.
  function stableIndex(key, poolSize) {
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      hash = (hash * 31 + key.charCodeAt(i)) >>> 0;
    }
    return hash % poolSize;
  }

  function pickCategoryPhoto(category, key) {
    const pool = categoryPhotoCache[category];
    if (!pool || !pool.length) return null;
    return pool[stableIndex(key, pool.length)];
  }

  function thumbHtml(item, size) {
    const cls = size === "lg" ? "featured-img" : "news-item-thumb";
    const category = categoryFor(item);
    if (item.image) {
      // No inline onerror attribute here on purpose — the SVG's own quote
      // characters would break out of a quoted HTML attribute. Instead we
      // mark the img with data attributes and wire up error handling in
      // JS after it's inserted (see attachThumbFallbacks).
      return `<img class="${cls}" src="${item.image}" alt="${escapeAttr(item.title)}" loading="lazy" data-thumb-fallback="1" data-thumb-size="${size}" data-thumb-category="${category}">`;
    }
    // Source gave us no photo — use a relevant Pexels stock photo if we
    // have one cached for this category, so cards rarely show a plain icon.
    const categoryPhoto = pickCategoryPhoto(category, item.link || item.title || "");
    if (categoryPhoto) {
      return `<img class="${cls}" src="${categoryPhoto}" alt="${escapeAttr(item.title)}" loading="lazy" data-thumb-fallback="1" data-thumb-size="${size}" data-thumb-category="${category}">`;
    }
    const fallbackCls = size === "lg" ? "featured-img" : "news-item-thumb-fallback";
    return `<div class="${fallbackCls} thumb-${category}">${TREND_ICON}</div>`;
  }

  function attachThumbFallbacks(root) {
    root.querySelectorAll("img[data-thumb-fallback]").forEach((img) => {
      img.addEventListener(
        "error",
        () => {
          const fallbackCls = img.dataset.thumbSize === "lg" ? "featured-img" : "news-item-thumb-fallback";
          const div = document.createElement("div");
          div.className = `${fallbackCls} thumb-${img.dataset.thumbCategory}`;
          div.innerHTML = TREND_ICON;
          img.replaceWith(div);
        },
        { once: true }
      );
    });
  }

  function attachTagHandlers(root) {
    root.querySelectorAll(".article-ticker-tag").forEach((tag) => {
      tag.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        TTNChart.open(tag.dataset.tv, tag.dataset.label);
        document.getElementById("chart-panel")?.scrollIntoView({ behavior: "smooth" });
      });
    });
  }

  function attachOpenHandlers(root) {
    root.querySelectorAll(".open-article").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        openModal(link.dataset.link);
      });
    });
  }

  function indexItems(items) {
    items.forEach((item) => {
      itemsIndex[item.link] = item;
    });
  }

  function renderFeatured(item) {
    const el = document.getElementById("featured-article");
    if (!item) {
      el.innerHTML = `<div class="featured-body"><p>No news available right now. Please check your internet connection.</p></div>`;
      return;
    }
    indexItems([item]);
    el.innerHTML = `
      ${thumbHtml(item, "lg")}
      <div class="featured-body">
        <div class="featured-meta"><span class="source">${item.source}</span> · ${timeAgo(item.pubDate)}</div>
        <h1><a href="#" class="open-article" data-link="${item.link}">${item.title}</a></h1>
        ${tickerTagsHtml(item)}
        <p style="margin-top:12px;"><a href="#" class="open-article" data-link="${item.link}" style="color:var(--accent);font-size:13px;">Read this story →</a></p>
      </div>`;
    attachTagHandlers(el);
    attachOpenHandlers(el);
    attachThumbFallbacks(el);
  }

  function renderFeed(items) {
    const el = document.getElementById("news-feed");
    if (!items.length) {
      el.innerHTML = `<p style="color:var(--text-dim);">News is temporarily unavailable.</p>`;
      return;
    }
    indexItems(items);
    el.innerHTML = items
      .map(
        (item) => `
      <article class="news-item">
        ${thumbHtml(item, "sm")}
        <div class="news-item-body">
          <div class="news-meta"><span class="source">${item.source}</span><span>${timeAgo(item.pubDate)}</span></div>
          <h3><a href="#" class="open-article" data-link="${item.link}">${item.title}</a></h3>
          ${tickerTagsHtml(item)}
        </div>
      </article>`
      )
      .join("");
    attachTagHandlers(el);
    attachOpenHandlers(el);
    attachThumbFallbacks(el);
  }

  let lastTrending = [];

  function renderTrending() {
    const counts = {};
    allItems.forEach((item) => {
      detectTickers(`${item.title} ${item.desc}`).forEach((t) => {
        counts[t.label] = (counts[t.label] || 0) + 1;
      });
    });
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8);
    lastTrending = sorted;
    const el = document.getElementById("trending-list");
    if (!sorted.length) {
      el.innerHTML = `<li style="color:var(--text-faint);font-size:13px;">No data yet</li>`;
      return;
    }
    el.innerHTML = sorted
      .map(([label, count]) => {
        const entry = TTN_CONFIG.TICKER_DICTIONARY.find((d) => d.label === label);
        return `<li><a href="#" class="trending-tag" data-tv="${entry.tvSymbol}" data-label="${label}">${label} <span style="color:var(--text-faint);">· ${count} mention${count === 1 ? "" : "s"}</span></a></li>`;
      })
      .join("");
    el.querySelectorAll(".trending-tag").forEach((tag) => {
      tag.addEventListener("click", (e) => {
        e.preventDefault();
        TTNChart.open(tag.dataset.tv, tag.dataset.label);
      });
    });
  }

  function getTrending() {
    return lastTrending;
  }

  function getAllItems() {
    return allItems;
  }

  async function applySearch(query) {
    const q = query.trim().toLowerCase();
    if (!q) {
      renderFeatured(allItems[0]);
      renderFeed(allItems.slice(1));
      return;
    }
    const filtered = allItems.filter((item) => {
      const tickers = detectTickers(`${item.title} ${item.desc}`).map((t) => t.label.toLowerCase());
      return (
        item.title.toLowerCase().includes(q) ||
        item.desc.toLowerCase().includes(q) ||
        tickers.some((t) => t.includes(q))
      );
    });
    await resolveTickerPrices(filtered.slice(0, 13));
    await resolveCategoryPhotos(filtered.slice(0, 13).map((i) => categoryFor(i)));
    renderFeatured(filtered[0]);
    renderFeed(filtered.slice(1));
  }

  function normalizeTitle(title) {
    return title
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s]/gu, "") // strip punctuation
      .replace(/\s+/g, " ")
      .trim();
  }

  // Law firms constantly push "investors should inquire about a class
  // action" press releases through the same wires as real financial news
  // whenever a stock drops. These aren't journalism, they're attorney
  // solicitation, and they clutter the feed. Filtered out by keyword match
  // rather than by source, since they get syndicated under normal outlet
  // bylines (Business Insider, PR Newswire, etc.) rather than a distinct
  // source name we could just exclude.
  const LEGAL_SOLICITATION_PATTERNS = [
    /class action/i,
    /investor rights/i,
    /securities fraud/i,
    /shareholder rights/i,
    /encourages .{0,40}investors to/i,
    /investors who (lost|suffered)/i,
    /(rosen|pomerantz|bragar eagel|kessler topaz|glancy prongay|levi ?& ?korsinsky|schall law|faruqi|kahn swick|johnson fistel|bronstein.{0,15}gewirtz|robbins geller|hagens berman) (law firm|llp|encourages|reminds|announces|files|is investigating)/i,
    /is investigating (claims|whether)/i,
    /law firm.{0,30}(investigation|investors)/i,
  ];
  function isLegalSolicitation(item) {
    const text = `${item.title} ${item.desc || ""}`;
    return LEGAL_SOLICITATION_PATTERNS.some((re) => re.test(text));
  }

  function dedupeItems(items) {
    const seenLinks = new Set();
    const seenTitles = new Set();
    const result = [];
    for (const item of items) {
      if (!item.link || !item.title) continue;
      const normTitle = normalizeTitle(item.title);
      if (seenLinks.has(item.link) || seenTitles.has(normTitle)) continue;
      seenLinks.add(item.link);
      seenTitles.add(normTitle);
      result.push(item);
    }
    return result;
  }

  // Groups items by source (each group already newest-first from the
  // earlier sort), then interleaves round-robin — one from each source in
  // turn — so a source that happens to publish a burst of items doesn't
  // flood the top of the feed and crowd out everyone else. Recency still
  // matters (each source's own queue is newest-first), it's just no longer
  // the *only* thing that decides order.
  function balanceBySource(items) {
    const bySource = new Map();
    items.forEach((item) => {
      const key = item.source;
      if (!bySource.has(key)) bySource.set(key, []);
      bySource.get(key).push(item);
    });
    const queues = [...bySource.values()];
    const result = [];
    let remaining = items.length;
    while (remaining > 0) {
      for (const queue of queues) {
        if (queue.length) {
          result.push(queue.shift());
          remaining--;
        }
      }
    }
    return result;
  }

  async function init() {
    const [feedResults, finnhubResults, currentsResults, apitubeResults] = await Promise.all([
      Promise.all(TTN_CONFIG.NEWS_FEEDS.map(fetchFeed)),
      fetchFinnhub(),
      fetchCurrents(),
      fetchApitube(),
    ]);
    const combined = [...feedResults.flat(), ...finnhubResults, ...currentsResults, ...apitubeResults]
      .filter((i) => i.title)
      .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate));
    allItems = balanceBySource(dedupeItems(combined.filter((i) => !isLegalSolicitation(i))));

    if (!allItems.length) {
      allItems = fallbackItems();
    }

    await resolveTickerPrices(allItems.slice(0, 13));
    await resolveCategoryPhotos(allItems.slice(0, 13).map((i) => categoryFor(i)));
    renderFeatured(allItems[0]);
    renderFeed(allItems.slice(1, 13));
    renderTrending();

    const searchInput = document.getElementById("search-input");
    searchInput?.addEventListener("input", (e) => applySearch(e.target.value));
  }

  function fallbackItems() {
    // Only shown if every news source is unreachable (e.g. no internet)
    const now = new Date().toISOString();
    return [
      {
        title: "News temporarily unavailable",
        desc: "Could not load financial news. Please check your internet connection or the RSS source settings in config.js.",
        link: "#",
        image: null,
        pubDate: now,
        source: "TTN",
      },
    ];
  }

  function openCustomModal(html) {
    const modal = ensureModal();
    document.getElementById("news-modal-body").innerHTML = html;
    attachTagHandlers(modal);
    attachThumbFallbacks(modal);
    showModal();
  }

  return {
    init,
    applySearch,
    openCustomModal,
    getTrending,
    getAllItems,
    resolveCategoryPhotos,
    getCategoryPhoto: (category, key) => pickCategoryPhoto(category, key || category),
    escapeAttr,
  };
})();
