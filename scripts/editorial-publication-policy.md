# TTN publication gate

Apply alongside `.agents/skills/ttn-editorial/SKILL.md`, the project-wide rules. This file owns the detailed commissioning, freshness, approval and date gates. The latest explicit user instruction overrides an older rule only within its scope.

## Standing commissioning instructions, October 19

- Source breadth, reaffirmed October 21: search widely across financial, economic, technology and crypto reporting, including Watcher.Guru (https://watcher.guru/) and specialist outlets. Do not restrict discovery to a small fixed publisher list. Verify important claims against primary releases, filings, official data or additional independent reporting; distinguish reporting from price predictions and sponsored/promotional material. This changes editorial research, not the News Aggregator provider configuration.
- For a three-article package, aim for one relevant current story each in Market Analysis, Tech & AI and Crypto. Investigate all three broadly. Freshness, significance and verification still take precedence over filling a quota; explain any section gap before substituting another topic.
- Preserve active TradingView ticker controls below an article when it mentions supported instruments. Build them from reviewed catalog tickers and explicit instrument names in the editorial text; do not confuse a publisher or exchange company with a stock index. Include the chart controller, verify the actual instrument/provider, and check mouse/keyboard activation. The shared refresh and site checks enforce coverage for new and existing articles.
- Keep working notes, prompts and technical logs internal. Do not send the owner MD files or technical-artifact links unless explicitly requested; report completed results and relevant article links concisely.

- A request to find and analyze news topics includes source verification, original article writing, distinct generated covers, relevant internal links, search/social metadata, publication and live verification. Do not require the user to repeat these steps. Audience-interest analysis is an internal selection aid and must not appear as scores or popularity claims in articles.
- Finance remains the core remit: the economy, monetary policy, banking, corporate finance and markets. Include equities, foreign exchange and crypto alongside Tech & AI when significant current events justify coverage. Do not impose a quota for any beat or substitute a stale item to fill a package.
- Publish separately reviewed articles sequentially when practical. Set each initial publication timestamp at its actual release, preserve that instant thereafter and use dateModified for substantive updates. Never manufacture intervals, backdate a story or vary timestamps merely to make simultaneous publication look organic.

Updated following the user's editorial correction on October 17, 2026.

- Inspect Market Analysis, Tech & AI and Crypto, but publish only when a significant, separately verified new event qualifies within the requested hour. A pair is a target, never a quota.
- If neither section has a qualifying event, publish nothing. If one section has no qualifying event, skip that section. Never fill it with a reserve topic, old report, background explainer or speculative corporate claim simply to meet a count.
- Record the earliest verified event/primary release and first reporting time, with timezone. An update, syndication time or later outlet confirmation does not reset an unchanged event's age.
- Review the October 17 withdrawal audit (`editorial-audit-20261017.json`, recoverable from Git history when absent from the working tree) before selecting a potentially repeated or withdrawn topic. Do not republish withdrawn IDs or their old drafts from editorial queue files. A genuinely material subsequent event requires a new review and a distinct article.
- Check the last several articles in the section for company and topic concentration. Separate events about one company do not automatically make a balanced news feed.
- Match the cover directly to the main reported event. Avoid tenuous illustrative connections such as a biological laboratory for a broad GDP scenario. Use verified references for specific products, people and named architecture. Respect `editorial-visual-policy.md`.
- User-requested image corrections must be previewed and specifically approved before any replacement is published. Removal of a weak article is permitted when authorized; it does not authorize an unseen replacement image.
- Keep source facts, assumptions and analysis distinct. A company model is not an independently validated forecast. Lack of access is not evidence of falsity, but insufficient verification is a reason to withhold a new publication.
- Never claim successful publication or withdrawal until the deployed catalog and direct URLs have been checked.

- Preserve published URLs that readers may have shared. A missed hourly freshness gate alone is not grounds to delete an existing accurate article. Correct verified errors at the existing URL; reserve withdrawal for a documented substantive reason. The user explicitly restored the New York Fed survey and Slovakia Tesla articles on October 17; do not remove them again on freshness grounds.

- Public dates and publication times target US readers: use America/New_York (Eastern Time, automatically EST/EDT), a 12-hour clock and the shared editorial-meta.js formatter in cards and article bylines. Scheduling in Kyiv time does not determine the reader-facing timezone. Preserve original timestamp instants and do not invent a time for legacy dates without an explicit timezone. All three sections use the shared TTNArchive.card component and editorial-meta.css for author, date and description styling.

## Reader-focused journalism review, October 22

Use Reuters standards (https://reutersagency.com/about/standards-values/) and AP sourcing principles (https://www.ap.org/about/news-values-and-principles/telling-the-story/) as references for verification, attribution, balance and clear distinctions between fact, allegation and analysis. Follow Google’s people-first guidance and contextual link practices (https://developers.google.com/search/docs/crawling-indexing/links-crawlable): useful original reporting and reader understanding take priority over clickbait, keyword stuffing or a fixed link count. Review the lead, stakes for the reader, specific comparisons, source transparency, informative subheads and story-specific imagery before publication. Distribute useful internal links through the text rather than reserving them for a closing paragraph or Related reading box. Audience growth is an objective, not a promised outcome.
