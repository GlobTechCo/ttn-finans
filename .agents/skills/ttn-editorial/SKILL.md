---
name: ttn-editorial
description: Maintain TTN Finance across editorial research, journalism, publishing, images, SEO, internal links, site design, accessibility, quotes, calculators, analytics and deployment. Use for all work on GlobTechCo/ttn-finans and requests to update TTN project rules.
---

# TTN Finance project rules

## Scope and authority

Work exclusively on `GlobTechCo/ttn-finans`, served at `https://globtechco.github.io/ttn-finans/`. Treat a request to update all rules as a project-wide TTN update. Never modify another project's files, skills, analytics or publishing settings as part of TTN work. Keep all TTN instructions in this repository.

Read `scripts/editorial-publication-policy.md` for commissioning, freshness, approvals and dates; read `scripts/editorial-visual-policy.md` for image decisions and corrections. Resolve conflicts using the latest explicit user instruction, preserving unrelated standing requirements. Read `README.md` for current implementation and commands. Treat historical task notes and queues as evidence, not fresh commissions or current facts. Do not turn an unresolved defect into a permanent design rule.

Write public articles in English for a U.S. audience. Communicate progress and results in Ukrainian; provide a Ukrainian duplicate of public copy when requested. Preserve News Aggregator content and behavior unless the user specifically authorizes changes to it.

## Research and editorial judgment

Cover significant developments in the economy, monetary policy, banking, corporate finance, equities, foreign exchange, crypto, technology and AI. Select news by substance, recency, verification and reader relevance. Compare all editorial sections and recent coverage to avoid duplicate stories and excessive company/topic concentration. Use a material new development, not a recycled explanation, as a new article's reason to exist.

Verify current claims using Western news sources and primary announcements, filings, official datasets or documentation. Read the underlying material; a search snippet is insufficient for important claims. Check critical claims across sources where possible. Record the original event/release and first reporting times with timezones. Syndication and cosmetic updates do not make an old event new. Apply the user's requested window exactly in Europe/Kyiv, including a last-three-hours request. Withhold an unverified story rather than invent facts or fill a quota.

Distinguish actual decisions, allegations, forecasts, scenarios and analysis. Check units, currencies, percentage changes versus percentage points, periods and attribution. Use official specifications for product measurements; do not relabel another publication's testing as official data. Never invent interviews, quotes, losses, firsthand observation or proprietary reporting. Keep useful source attribution and rights-required credits without promotional outlet plugs or decorative numeric footnotes. Do not conceal the source of a claim.

## Writing and commissioning

Require at least 700 words of article-body paragraphs for every new article and substantive rewrite, in every section and format. This is the owner's hard minimum, effective October 30, 2026. Do not count the headline, deck, headings, sources, captions, navigation or related reading. Run the paragraph-count audit before publication and fix a short draft with substantive verified reporting or useful analysis, never filler. Do not silently revert to the former 600-word news threshold. Unchanged historical articles are outside a new commission unless their revision is requested.

Write as an experienced journalist: lead with the concrete development, explain its significance and mechanisms, add relevant context and identify uncertainty. Use original structure and clear, precise English. Lead with what changed and why it matters to readers; use concrete comparisons, meaningful subheads and an independent angle rather than rewriting a press release. Do not pad a thin story with generic caveats to reach a length target. Avoid AI-like formulas, promotional claims, rhetorical questions, long dashes, repetitive conclusions and length padding. Make unfamiliar companies and technical terms understandable in the headline/deck and first relevant passage. Keep analysis distinguishable from verified fact; do not imply personalized investment advice or certainty about market outcomes.

Follow the publication policy's standing commissioning scope: a commissioned news package includes research, original articles, suitable covers, links, metadata, publication and verification. Do not silently expand a standalone question, audit or rules update into a new publication. Treat requested article counts and section pairs as targets subordinate to freshness and significance. Report a shortfall honestly.

For recurring work, inspect actual automation configuration before claiming it is active or changed. The requested cadence is one item per original section at the top of each hour, daily 11:00 through 02:00 Europe/Kyiv, subject to the news gate. Do not claim background monitoring or successful scheduled deliveries without an operational automation. Do not backfill missed slots with stale stories.

## Classification and internal links

Use Market Analysis for general financial reporting and explainers, Tech & AI for technology/AI coverage, and Crypto for digital-asset markets, stablecoins, tokenization and crypto regulation. Set Crypto format to news or explainer and keep it aligned with the article schema. General prediction-market coverage stays in Market Analysis unless its main angle is specifically crypto. Decide the section from the story's main angle. Keep the catalog, standalone page, breadcrumb, schema, homepage and archives consistent. Treat explicit catalog sections as authoritative while preserving compatible legacy IDs. Verify rendered section exclusivity, not only HTML fallback or a section label.

Use visible contextual internal links to relevant existing articles and specific related reading. Add a useful incoming link from an established related article where appropriate. Avoid irrelevant link stuffing. Review contextual links throughout the body rather than applying a template with one link near the end. Add descriptive links at the point where a relevant explainer or previous report helps the reader; there is no universal link quota. Keep Related reading supplementary. Preserve accurate published URLs and dates; correct at the existing URL unless withdrawal has a substantive documented reason. Freshness alone does not justify deleting an accurate published article.

## Images

Never use a cinematic style for TTN imagery. Reject cinematic-looking outputs before publication even when the generation prompt prohibited that style. Apply the complete visual policy before selecting, generating, accepting or replacing a cover. Prefer distinct generated editorial covers for TTN; honor an explicit generation request. Use authentic references for named buildings, brands and products. Verify licensing and credit requirements for any explicitly approved original photograph. Never present a synthetic scene or person as documentary evidence.

Inspect the actual result at card and full-article sizes. Require a direct connection to the story, plausible details and natural editorial appearance. Reject cinematic grading, staged advertising behavior, anatomical errors, invented architecture and repetitive subjects. Follow the specific preview-and-approval gate for corrected images before replacing them on the site. Do not interpret a request to generate a revised preview as approval to publish an unseen result.

Prefer a sharp 1920×1080 WebP master with responsive variants; preserve supported quality and framing rather than enlarging a weak result. Use versioned replacement filenames. Update hero, card catalog, static fallbacks, archives, alt text, schema and OG/Twitter images together. Retain old immutable social assets for previously shared links. Keep truthful alt/schema and internal provenance without adding an unwanted visible AI-generation caption.

## SEO, analytics and monetization

Maintain unique useful titles/descriptions, one clear page heading, canonical URLs, crawlable article text and links, valid Article schema, truthful publication/modification dates, sitemap/robots and complete OG/Twitter cards. Use reviewed search metadata without silently rewriting visible headlines. Do not promise rankings, indexing or AdSense approval. Keep article content and navigation usable without JavaScript.

Preserve original publication instants. Use dateModified for substantial changes and meaningful sitemap lastmod values. Show dates through the shared editorial-meta formatter in America/New_York, with its automatic EST/EDT handling and a 12-hour clock. Kyiv scheduling does not change the public display timezone. Do not invent timezone/time details for legacy date-only records.

Read TTN's current analytics/consent configuration before editing it. Use only the actual user-authorized measurement ID; do not import other projects' tags or invent identifiers. Keep private credentials out of served files. Preserve disabled advertising until real publisher/slot IDs, account instructions, consent integration, labels and responsive sizing are available and authorized. Do not fabricate ads.txt authorization or activate placeholders. Retain policy/about/contact pages and editorial quality appropriate to a commercial publication.

## Design, navigation and tools

Maintain a restrained professional media layout in both light and dark themes. Use consistent hover/focus behavior, readable contrast, clear typography, balanced spacing and responsive cards. Inspect the header/logo, homepage columns, article layout and compact two-column mobile footer when affected. Use the shared theme/menu components; avoid duplicated handlers or emoji theme controls. Preserve keyboard navigation, focus behavior, skip links, landmarks, accessible labels and a usable no-JavaScript fallback.

Keep market quotes and news loading independently with bounded failures. Prefer the existing TradingView integration for tape/charts; verify actual symbol support and distinguish cash indexes, futures and broker CFDs in labels. Use reader-facing instrument names such as Brent Oil with accurate provider context. Never invent live prices or hide unavailable values behind demonstration data. Check hover behavior, both themes and quotes inside articles. Do not restore removed snapshot/search/tape-label blocks casually or change News Aggregator to resolve a quote issue.

Keep financial calculators functional, accessible and numerically coherent. Verify formulas, units, assumptions, boundary cases and result explanations when changing calculations. Avoid decorative stock/AI imagery that obscures the tool. Keep deferred Save/Translate/Listen features paused unless recommissioned; preserve existing sharing/copy-link behavior when editing the surrounding UI.

## Repository, checks and publication

Inspect the current diff and repository head before editing. Modify source components, then rebuild derived cards/bundles using existing scripts. Consult `scripts/editorial_topics.py` for topic/related assignments. Review generated diffs and remove unrelated churn. Do not apply a broad generator as an excuse to rewrite unrelated articles. Preserve GitHub Pages/Jekyll exclusion rules; keep maintenance instructions and scripts out of the public site.

Run checks appropriate to the actual change: skill validation for rules; `python3 scripts/verify_site.py` for site consistency; independent-loading/navigation checks for relevant JavaScript changes; calculator tests for changed formulas; advertising checks for placement changes. Run image/social refresh scripts only as needed. For layout changes, inspect desktop/mobile and both themes. For publishing, verify references, image decoding/quality, metadata, timestamps, internal links and section exclusivity.

Publish against the latest expected remote head without overwriting concurrent work. If ordinary push is unavailable, use authenticated GitHub blob/tree/commit/ref tools; compare uploaded blobs and use an expected-head lease. Do not change repository visibility as a workaround. Distinguish local changes, a saved remote commit, successful deployment and live verification in status reports.

After a content/image/UI deployment, inspect the actual live article, image, homepage, relevant archive and social metadata; verify the affected interactive behavior. A remote commit alone is not proof of live publication. For rules-only changes, confirm the saved repository files without claiming a new article or UI deployment. Report the result, validation and any real blocker concisely in Ukrainian; complete authorized work without repeated confirmations, while honoring explicit image approval requirements.
