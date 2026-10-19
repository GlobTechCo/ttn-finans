# TTN Finance

TTN Finance is a static English-language publication covering financial markets,
technology and the global economy. It combines original reporting and explainers,
a separate external news feed, TradingView quotes and financial calculators.

## Project structure

- `index.html`: homepage with static editorial cards and an external news feed.
- `analysis.html`, `tech-ai.html`: paginated original-content archives with a
  complete, static directory of article links grouped by topic.
- Individual `.html` article pages: complete text, sources, social metadata and
  contextual Related reading links. Reading an article does not require JavaScript.
- `articles.js`: canonical editorial catalog, including full article text.
- `article-cards.js`: generated compact catalog for homepage and archive cards.
  It excludes full bodies and source lists to reduce visitor downloads.
- `home-editorial.js`, `archive-editorial.js`: generated bundles of the editorial
  display components, in dependency order. Edit the individual source components
  and regenerate; news, quotes and their initialization remain separate.
- `style.css`, `editorial-theme.css`, `footer.css`, `homepage-layout.css`,
  `archive-pagination.css`, `editorial-related.css`: shared presentation.
- `editorial-theme.js`, `editorial-meta.js`, `archive-pagination.js`: theme,
  publication labels and archive navigation.
- `news.js`, `config.js`, `tickers.js`, `app.js`: external news, provider settings,
  supplementary quote lookups and independent initialization.
- `market-tape.js`, `chart.js`: TradingView quote tape and interactive charts.
- `calculators.html`, calculator pages and `calculators.js`: financial tools.
- `analytics.js`, `consent.js`: analytics consent and preferences.
- `404.html`: custom not-found page; excluded from indexing and sitemap.
- `assets/`: editorial originals, responsive sizes and social preview images.
- `sitemap.xml`, `robots.txt`: discovery and indexing configuration.
- `scripts/`: maintenance code and operational image manifests, excluded from
  the published site by `_config.yml`.

## Run locally

No build tool or application server is required:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/`. External news and quote widgets still require a
network connection. Static article content and topic directories work without
JavaScript. The 404 page uses an absolute base URL for the production project
path, so its links and assets also work for deeply nested missing addresses.

## Editorial maintenance

After adding or updating a catalog entry and its standalone HTML page:

```sh
python3 scripts/refresh_static_editorial.py
python3 scripts/refresh_seo_metadata.py
python3 scripts/verify_site.py
node scripts/test-independent-loading.cjs
node scripts/test-navigation.cjs
```

Install optional verification/image dependencies with
`python3 -m pip install -r requirements-maintenance.txt`.

`refresh_static_editorial.py` regenerates the compact card catalog, editorial
JavaScript bundles with content-based URL versions, current
homepage/archive fallbacks and full topic directories. It preserves existing
Related reading selections and adds a block to pages that lack one. Review new
articles in `scripts/editorial_topics.py` to assign a topic and specific related
reading. Uncategorized new entries still appear in the static archive.

`refresh_seo_metadata.py` applies reviewed search titles/descriptions from
`scripts/seo_metadata.py`; it does not replace visible article headlines.

For image changes, `scripts/refresh_social_cards.py` refreshes social-image URLs
and the operational social-card manifest. Retain earlier social-image assets so
previously shared links continue working. Supply responsive images and keep
catalog paths, `srcset` and standalone image metadata aligned.

Update sitemap `lastmod` when a page changes meaningfully. Preserve actual
publication dates; do not alter them to make old material appear newly published.
A substantial content revision should receive a truthful `dateModified`.
Historical editorial queues and review reports can be recovered from Git history;
they are not needed to run the site.

For a read-only date provenance check, run
`python3 scripts/audit_publication_dates.py` (or add `--details`). This compares
the current catalog with the first HTML version and the Git addition date.
An earlier publication label can reflect an import; a discrepancy is a review
flag, not proof of backdating or authorization to invent a new publication date.

## Data and failure behavior

The visible quote tape is a TradingView widget using Bitstamp BTC/USD and ETH/USD,
FOREX.com S&P 500 and Nasdaq-100 instruments, CMC Markets Gold and FXCM EUR/USD.
The FOREX.com instruments are broker quotes, not the official cash-index feeds.
Closed markets can show the latest available price. The widget does not expose a
quote API to the site's JavaScript. The former Market Snapshot is removed.

The external news feed uses the providers configured in `config.js`. Supplementary
quote lookups use separate providers; they can differ from the tape. Failed or
unconfigured quote lookups produce missing values, not invented demonstration
prices. News and quote requests start independently, with bounded request timeouts.
Do not put private credentials in this publicly served configuration.

## Deployment

The repository is `GlobTechCo/ttn-finans`. GitHub Pages publishes the `main` branch
at `https://globtechco.github.io/ttn-finans/` using the root directory and Jekyll.
`_config.yml` excludes maintenance scripts and documentation. Do not add
`.nojekyll` without providing an equivalent publication exclusion mechanism.

Before publishing, run validation and inspect desktop/mobile layouts, both themes,
archive pagination and the JavaScript-disabled homepage. After deployment, verify
representative live pages and the custom not-found response.

## Advertising

AdSense is not connected. A valid publisher ID and account-specific instructions
are needed before adding its script or an `ads.txt` seller record. There is no
placeholder publisher ID or fabricated authorization record. Editorial quality,
site policies and accurate reporting remain separate requirements from advertising
integration.

## Shared navigation and accessibility

Use the common header on new pages, including About and Contact. Keep the menu
button linked to `nav-links` with `aria-controls` and an initial
`aria-expanded="false"`. `editorial-theme.js` owns its disclosure behavior;
do not add per-page menu handlers. It closes on Escape, selection, outside
interaction and focus leaving the header, and restores button focus on Escape.

Place `Skip to main content` first in the body, linking to the single
`main` landmark with `id="main-content"` and `tabindex="-1"`. The navigation
remains visible on small screens when JavaScript is unavailable. The 404 page
uses absolute resource links so its skip fragment works at arbitrary missing URLs.

## Advertising locations (disabled)

`scripts/ad_placements.py` keeps advertising disabled globally and for every
placement. Publisher and slot IDs are empty. Article pages have a location after
the body; articles of at least 600 words also have one near the midpoint, with
at least 150 words on each side. The homepage has two locations between complete
sections, and each original-content archive has one below its article cards.
Policy pages, contact, tools and the 404 page have no advertising locations.

Locations use native `<template>` elements. They create no visible blocks,
reserved height, focus targets, AdSense tags or network requests. No advertising
JavaScript or stylesheet is loaded. The existing news aggregator is untouched.

Run `python3 scripts/ad_placements.py` to refresh placements. The regular
`refresh_static_editorial.py` command also maintains them. Do not convert these
templates into live ads until an actual publisher ID, slot IDs, consent integration,
clear advertisement labels and responsive sizing have been configured and tested.
Changing the disabled flag alone deliberately refuses activation.
