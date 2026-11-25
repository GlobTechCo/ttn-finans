# TTN Finance — Semantic Keyword Core
**Version:** 1.1 (baseline map with dated-news support URLs)  
**Prepared:** 25 November 2026  
**Primary language:** English (US spelling and search phrasing; international coverage)  
**Primary SEO audience:** English-speaking readers, with the United States as the initial keyword-validation market and UK, Europe, Australia and Asia coverage retained editorially.  
**Repository:** `GlobTechCo/ttn-finans`

## Purpose and status

This is the first structured semantic map for TTN Finance. It assigns one dominant search intent and one primary query theme to each existing landing page or evergreen explainer, then lists supporting query variants and internal-link relationships.

**Important data limitation:** no Google Search Console query/page export, Google Ads Keyword Planner data, or connected keyword-research dataset was available while this baseline was prepared. Therefore:
- Search volumes, keyword difficulty, CPC, ranking positions and traffic estimates are deliberately **not invented**.
- P1/P2 are editorial and strategic priorities, not claims about measured search volume.
- Query phrases are candidate targets to validate, not evidence that TTN currently ranks for them.
- Connect the Search Console / keyword research integration and refresh this map using real query, impression, click, CTR and position data before making volume-led decisions.

## Existing site architecture mapped

| Existing page | Role in the semantic structure |
|---|---|
| `/` | Brand and broad financial-news discovery |
| `analysis.html` | Market Analysis archive and broad markets discovery |
| `tech-ai.html` | Tech & AI archive |
| `crypto.html` | Crypto archive |
| `brokers.html` | Brokers and exchanges comparison information |
| `calculators.html` | Financial calculator directory |
| Individual evergreen explainers and tools | Own specific definitions, practical tasks and long-tail intents |

The site already has thematic editorial grouping in `scripts/editorial_topics.py`. That is useful for content organization and related-reading suggestions, but it is not by itself a keyword-research database or a measured semantic core.

## Priority definitions

- **P1:** strategically central to the publication or supported by a useful existing hub/tool/evergreen page. Validate demand and performance first.
- **P2:** valuable secondary cluster with a narrower audience, a shared landing page, or a content-depth limitation.
- These are planning priorities only. Do not interpret them as search-volume tiers.

## Cluster rules

1. **One primary intent per URL.** A page can rank for many close variants, but two TTN pages should not be deliberately optimized for the same dominant intent.
2. **Hubs target broad category terms.** Individual articles target a specific company, event, market move, product, regulation or question.
3. **Evergreen explainers own definitions.** News stories link to explainers for background; explainers link back to relevant current coverage only when it adds value.
4. **Tools own task intent.** Calculator pages should answer the calculation directly and explain formulas, assumptions, fees/taxes exclusions and limitations.
5. **No keyword stuffing.** Use the primary phrase naturally in the title, H1, introduction and relevant subheadings where it fits. Secondary phrases belong where the subject genuinely covers them.
6. **No meta-keywords tag.** Google does not use the meta-keywords tag for web ranking. Do not add it.
7. **Do not change established URLs casually.** Preserve current slugs. If a URL must change, require a tested permanent redirect and canonical update.
8. **No unsupported superlatives.** Avoid “best broker”, “top exchange” or “highest-return investment” unless the article has a transparent, current methodology and jurisdiction-specific evidence.
9. **Financial YMYL standards.** Attribute data, distinguish fact from estimate, disclose assumptions, date fee/rate/regulatory information, and avoid personalized financial or tax advice.
10. **Do not target Russia or Russian entities.**

## Cannibalization and architecture watchlist

- **Brokers vs. crypto exchanges:** both currently converge on `brokers.html`. Keep one neutral comparison hub for now, but clearly separate stock/forex brokerage intent from crypto-exchange intent in headings and sections. A separate exchange landing page should only be introduced if the site has enough original, maintained comparison content and distinct query demand.
- **Bitcoin market news vs. Bitcoin ETF flows:** `crypto.html` is the broad hub; `bitcoin-etf-institutional-adoption.html` is the evergreen institutional-adoption explainer; dated ETF flow stories own their specific reporting period. Do not reuse the same evergreen slug for a new monthly flow report.
- **AI infrastructure vs. AI chips vs. AI economics:** keep power/capacity/capex, semiconductor supply constraints, and inference/monetization economics as separate clusters. Company stories target their company and event.
- **Inflation vs. CPI vs. PPI:** `cpi-inflation-explained.html` is the broad consumer-inflation anchor; PPI and individual data releases need their own clearly differentiated intent.
- **Market Analysis archive vs. individual investment explainers:** `analysis.html` is a collection page, not a substitute for dedicated explainers such as bond duration, ETF mechanics, free cash flow or dollar-cost averaging.
- **Calculators hub vs. individual calculators:** the directory targets broad calculator discovery; each tool targets one task. Avoid duplicating a full calculator on the directory page.

## On-page implementation standard for every new article

Before drafting, select:
- one primary query and one search intent;
- 3–8 closely related secondary queries/entities;
- one existing parent hub and up to three genuinely relevant internal links;
- one differentiation statement explaining why this article does not duplicate an existing TTN URL.

Then verify:
- SEO title accurately expresses the article’s main subject and is distinct from existing titles;
- one clear H1, with the deck supporting rather than repeating it;
- meta description summarizes the actual article, not a keyword list;
- slug is unique, readable and stable;
- H2/H3 structure answers the reader’s likely follow-up questions;
- internal links use descriptive anchors and resolve to existing pages;
- canonical, Open Graph, Twitter Card and appropriate Schema.org data match the final URL;
- publication and modification dates are accurate;
- no hidden meta-keywords tag is added.

## Search Console measurement loop

Once connected, export at least the last 3 months and 16 months where available, grouped by **query** and **page**, including clicks, impressions, CTR and average position. Segment by country and device.

For each cluster:
1. Find queries with meaningful impressions but weak CTR: review title and snippet relevance, not just wording.
2. Find queries ranking around positions 5–20: assess whether the assigned page answers the query better than competing TTN pages.
3. Find queries where multiple TTN URLs receive impressions: inspect intent overlap and choose one canonical target page; consolidate only when content genuinely duplicates.
4. Find high-impression queries with no appropriate TTN page: record a content gap, then commission an article or guide only when it fits editorial standards.
5. Compare mobile and desktop results; do not infer demand from one device segment.
6. Recheck after material edits; annotate changes so ranking movements can be interpreted.

## Files

- `seo/semantic-keyword-core.csv` — working cluster-to-URL map, suitable for spreadsheet review.
- This document — strategy, governance, cannibalization watchlist and measurement procedure.

## Next evidence required

The baseline map is ready for use in editorial planning. To turn it into a measured, evidence-backed keyword core, the next input is a connected Google Search Console dataset plus keyword research for the US, UK, Australia and selected European markets. Do not fabricate volume or difficulty in the meantime.


## Dated news support URLs — November 25, 2026

Three current articles have been added as supporting URLs to existing clusters, without replacing their evergreen anchor pages:

- Market Analysis: the Asian equities and US tariff-risk report supports the global-markets and trade/tariffs clusters.
- Tech & AI: Dell's AI-server backlog report supports the AI-infrastructure and Tech & AI news clusters.
- Crypto: the November spot Bitcoin ETF flow report supports the Bitcoin ETF flows and crypto-regulation clusters.

These are event-specific pages, not new evergreen landing pages. Their inclusion is a semantic mapping decision, not evidence of measured search demand. Search volumes, rankings, impressions and clicks remain unmeasured until a Search Console export is available.

## Whole-site semantic audit — November 25, 2026

The 26-cluster CSV was checked against the repository: every primary target and listed supporting URL exists. The published sitemap contains 500 unique URLs with no duplicates; the two additional HTML files outside the sitemap are the 404 page and the Google verification file, while the homepage is represented by the root URL. The broad archive hubs are reused as primary targets in several clusters: analysis.html serves global markets, investing basics and earnings discovery; crypto.html serves Bitcoin and Ethereum discovery; brokers.html currently covers both traditional brokers and crypto exchanges. These overlaps are intentional hub-level mappings but remain cannibalization watchpoints. Use dedicated evergreen pages or dated news URLs for narrower intents, and do not create new landing pages until query data and sufficient original content justify them.
