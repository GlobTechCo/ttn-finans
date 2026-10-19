---
name: ttn-editorial
description: Research, write, publish and correct TTN Finance articles, editorial covers, homepage sections and social cards. Use for TTN Original, Market Analysis, Tech & AI, generated finance or technology imagery, and requests to apply TTN editorial or image-quality corrections.
---

# TTN Finance editorial workflow

Work exclusively on `GlobTechCo/ttn-finans`, published at `https://globtechco.github.io/ttn-finans/`. This skill belongs only to TTN Finance. Never modify another project or its skills while carrying out a TTN task. Interpret requests to update all skills within this project scope. Write original English articles for a U.S. audience; report work in Ukrainian. Preserve News Aggregator content and behavior.

## Verify the story

Establish the precise news development, first publication time, modification time and event date. Interpret user time windows in Europe/Kyiv. Do not qualify an older story merely through a recent update or syndication. Check for an existing article before selecting the topic.

Use Western news organizations and primary records. Verify important claims against original announcements, filings, datasets or documentation. Distinguish a forecast, allegation, warning and actual decision. Do not invent interviews, measurements, quotes, losses or firsthand experience. Write as an experienced journalist: concrete finding first, original structure, clear explanation and useful context. Avoid promotional language, formulaic AI phrasing, rhetorical questions, long dashes and word-count padding. Preserve copyright limits and required attribution.

## Generate natural editorial imagery

Treat image selection and quality review as editorial decisions, not decorative tasks. Before prompting, name the article's subject and central angle and choose a scene that explains them. A generic data center does not adequately identify a credit agency's warning when the agency itself is the news subject.

Honor explicit generation requests. For TTN the owner prefers unique generated editorial covers, not stock/Pexels images. Use verified references for actual companies, recognizable buildings, logos and products; do not invent a branded facade or put a printed company name on paper. If the user explicitly approves an original photograph, verify its commercial editorial rights and credits before publishing. Never represent generated imagery as a documentary photograph or evidence of an actual event. Retain generation provenance internally and use truthful alt text/schema; do not add a visible AI-generation caption under the image.

Apply these requirements to every generated scene:

- Use ordinary natural daylight, realistic white balance, normal exposure, natural color and believable textures. Neutral does not mean gray, brown or desaturated.
- Exclude cinematic or moody grading, dramatic clouds, underexposure, film grain, teal/orange effects, strong vignettes, excessive blur, artificial glow and harsh reflections.
- Exclude advertising staging and stock-photo behavior: posed agent-and-buyer groups, handshakes, matching smiles, generic meetings and showroom-perfect surroundings.
- Include people when relevant. Show natural posture and a believable task, with correct anatomy and safe placement. Do not solve staging by removing all people from every image.
- Vary subjects, locations, framing and human activity across articles. Avoid repeated faces, office scenes, round devices, gas nozzles or decorative visual motifs.
- Depict ordinary credible environments. For housing-market news, use realistic residential construction or an ordinary new-build street rather than a picturesque luxury development or staged sales visit.
- Preserve supported visual details and scale. Keep vehicles parked plausibly, equipment intact and numerical keypads legible when present.

## Reject weak results before publishing

Inspect the actual generated output, not just the prompt. Check the story connection, factual identity, architecture, perspective, signage, lighting, color, textures, reflections and people. Reject cinematic, promotional, staged, irrelevant or anatomically flawed results and regenerate with a targeted correction. Never publish a weak image and only acknowledge the defect after the user challenges it.

Inspect both card and full-article framing. Aim for a useful 1920×1080 WebP master with responsive variants, while preserving the subject and image quality. Do not upscale a visibly weak result as a substitute for regeneration. Keep one distinct cover per article.

## Integrate articles and corrections

Choose Tech & AI or Market Analysis (the owner's TTN Original) once and apply it consistently to the catalog, standalone page, breadcrumbs, homepage, archive and metadata. Use the catalog's section as authoritative. Preserve legacy classification where needed, but do not rely solely on duplicated ID lists. Verify that each new article appears in its intended section and is absent from the other one after JavaScript renders.

Add visible, relevant internal links and an incoming link from an established related article when useful. Keep publication dates truthful and stable. Maintain concise titles/descriptions, canonical URLs, alt text, Article schema, sitemap and Open Graph/Twitter cards. Preserve TTN’s own analytics configuration; do not invent account identifiers.

For an image replacement, use versioned filenames and update the article hero, card catalog, homepage/static fallback, archive, schema, alt text and social image URL together. Keep immutable old social assets available for existing links; new sharing metadata must point to the new asset. Do not change article text or unrelated pages merely because a generator touches them.

Verify decoded image files, local references, schema and section exclusivity. Compare uploaded blob hashes. Publish against the current expected repository head; do not overwrite concurrent work. If Git push is unavailable, use authenticated GitHub blob/tree/commit/ref tools, including base64 blobs for images. Do not stop at local-only files or claim publication before the site deploys.

After deployment, inspect the live article, actual image, homepage section and relevant archive; verify social metadata. Check mobile/desktop framing when the change affects layout. Summarize the concrete result and any remaining limitation in Ukrainian.
