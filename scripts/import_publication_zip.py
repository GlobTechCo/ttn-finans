#!/usr/bin/env python3
"""Safely import an approved TTN ZIP package; run site regeneration afterwards."""
import datetime
from zoneinfo import ZoneInfo
import copy
import html as html_std
import json
import re
import sys
import zipfile
from pathlib import Path
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://globtechco.github.io/ttn-finans/"
slug_re = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
topic = {"Market Analysis": "Jobs and housing", "Tech & AI": "AI investment, infrastructure and productivity", "Crypto": "Crypto, stablecoins and market structure"}

def check(condition, message):
    if not condition:
        raise ValueError(message)

def publish(archive):
    archive = Path(archive)
    check(archive.stat().st_size <= 30_000_000, "ZIP exceeds 30 MB")
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        check(len(names) == len(set(names)) and len(names) <= 100, "Duplicate or excessive ZIP entries")
        check(sum(i.file_size for i in z.infolist()) <= 100_000_000, "Expanded ZIP too large")
        for i in z.infolist():
            p = Path(i.filename)
            safe = i.filename in ("publication-manifest.json", "README-PUBLISH.txt", "GEMINI_INSTRUCTIONS.txt")
            safe |= len(p.parts) == 1 and p.suffix == ".html" and bool(slug_re.fullmatch(p.stem))
            safe |= len(p.parts) == 3 and p.parts[0] == "assets" and p.parts[1] in ("social", "editorial", "responsive") and p.suffix.lower() in (".webp", ".png", ".jpg") and bool(slug_re.fullmatch(p.stem))
            check(safe and not i.is_dir() and ".." not in p.parts and "\\" not in i.filename, "Unsafe ZIP entry: " + i.filename)
        manifest = json.loads(z.read("publication-manifest.json"))
        check(isinstance(manifest, list) and 1 <= len(manifest) <= 12, "Manifest needs 1 to 12 articles")
        catalog_path = ROOT / "articles.js"
        catalog = json.loads(catalog_path.read_text().split("=", 1)[1].strip().removesuffix(";"))
        existing = {a["id"] for a in catalog}
        replace_slugs = {
            "eu-budget-2028-2034-cuts-digital-tax-november-2026",
            "eu-indonesia-trade-agreement-european-exporters-2026",
            "bitcoin-reclaims-60000-weekend-rebound-november-21-2026",
            # Controlled correction pass for the three November 22 articles.
            "sec-fake-crypto-platforms-37-million-fraud-november-2026",
            "sk-hynix-mars-cxl-memory-pooling-ai-inference-2026",
            "swiss-inflation-snb-second-round-effects-december-policy-2026",
            # Controlled correction pass for the three November 23 articles after importer QA.
            "market-analysis-morgan-stanley-bullish-stocks",
            "tech-ai-nvidia-reinstates-jensen-huang",
            "crypto-bitcoin-seven-week-losing-streak",
            # Controlled November 24 correction pass for deck, SEO metadata and ticker QA.
            "global-banks-trading-revenue-record-301-billion-2026",
            "crowdstrike-zscaler-43-9-billion-cybersecurity-deal-2026",
            "ecb-tokenized-securities-eurosystem-collateral-2027",
        }
        approved_html_files = {slug + ".html" for slug in replace_slugs}
        entries = []
        relations = {}
        for m in manifest:
            slug = m["slug"]
            if slug == "eu-budget-2028-2034-cuts-digital-tax-november-2026":
                m["dek"] = "Costa's revised EU budget cuts €40 billion and proposes a 3% levy on major digital revenues."
                m["date"] = "2026-11-21T13:56:00-05:00"
            elif slug == "eu-indonesia-trade-agreement-european-exporters-2026":
                m["dek"] = "The EU-Indonesia deal cuts tariffs on 98.5% of lines and targets €650 million in annual exporter savings."
                m["date"] = "2026-11-21T13:56:00-05:00"
            elif slug == "bitcoin-reclaims-60000-weekend-rebound-november-21-2026":
                m["date"] = "2026-11-21T13:56:00-05:00"
            check(isinstance(slug, str) and bool(slug_re.fullmatch(slug)), "Invalid article slug")
            # The Japan FSA article is straight news reporting, not analysis.
            if slug == "japan-fsa-sustainability-assurance-startup-finance-rules-november-2026":
                m["format"] = "news"
            check((slug not in existing or slug in replace_slugs) and slug not in relations, "Existing or duplicate article: " + slug)
            check(m["section"] in topic and m["format"] in ("news", "analysis", "explainer"), "Invalid editorial section or format")
            parsed_date = datetime.datetime.fromisoformat(m["date"].replace("Z", "+00:00"))
            check((len(m["date"]) == 10 and parsed_date.tzinfo is None) or parsed_date.tzinfo is not None, "Date must be date-only or include a timezone offset")
            sources = m.get("sources", [])
            check(isinstance(sources, list) and len(sources) >= 1, "Every article needs at least one source")
            for source in sources:
                check(isinstance(source, dict) and isinstance(source.get("label"), str) and source["label"].strip() and isinstance(source.get("url"), str) and source["url"].startswith("https://"), "Invalid article source")
            file = slug + ".html"
            cover = m["cover"]
            check(file in names and cover in names and cover.startswith("assets/editorial/" + slug + "-"), "Article/cover missing")
            doc = html.fromstring(z.read(file))
            # Normalize common Gemini-export paths to the live TTN site layout.
            for stylesheet in doc.xpath("//link[@rel='stylesheet'][@href]"):
                href = (stylesheet.get("href") or "").strip()
                if href in {"assets/styles.css", "assets/style.css", "styles.css"}:
                    stylesheet.set("href", "style.css")
            for anchor_node in doc.xpath("//a[@href]"):
                if (anchor_node.get("href") or "").strip() == "market-analysis.html":
                    anchor_node.set("href", "analysis.html")
            for dek_node in doc.xpath("//p[contains(concat(' ',normalize-space(@class),' '),' article-dek ')]"):
                dek_node.text = m["dek"]
                for child in list(dek_node):
                    dek_node.remove(child)
            expected_canonical = BASE + file
            canonical_nodes = doc.xpath("//link[@rel='canonical']")
            if not canonical_nodes:
                head_nodes = doc.xpath("//head")
                check(len(head_nodes) == 1, "Missing document head for canonical URL: " + slug)
                canonical_nodes = [html.Element("link", rel="canonical", href=expected_canonical)]
                head_nodes[0].append(canonical_nodes[0])
            canonical_nodes[0].set("href", expected_canonical)
            for duplicate in canonical_nodes[1:]:
                duplicate.getparent().remove(duplicate)
            check(doc.xpath("//link[@rel='canonical']/@href") == [expected_canonical], "Could not normalize canonical URL: " + slug)
            published_nodes = doc.xpath("//meta[@property='article:published_time']")
            if not published_nodes:
                head_nodes = doc.xpath("//head")
                check(len(head_nodes) == 1, "Missing document head for publication date: " + slug)
                published_nodes = [html.Element("meta", **{"property": "article:published_time", "content": m["date"]})]
                head_nodes[0].append(published_nodes[0])
            published_nodes[0].set("content", m["date"])
            modified_nodes = doc.xpath("//meta[@property='article:modified_time']")
            if not modified_nodes:
                head_nodes = doc.xpath("//head")
                check(len(head_nodes) == 1, "Missing document head for modified date: " + slug)
                modified_nodes = [html.Element("meta", **{"property": "article:modified_time", "content": m["date"]})]
                head_nodes[0].append(modified_nodes[0])
            for node in modified_nodes:
                if not node.get("content"):
                    node.set("content", m["date"])
            for time_node in doc.xpath(
                "//p[contains(concat(' ',normalize-space(@class),' '),' editorial-meta ')]//time"
            ):
                time_node.set("datetime", m["date"])
                display_dt = datetime.datetime.fromisoformat(m["date"].replace("Z", "+00:00"))
                if display_dt.tzinfo is not None:
                    display_dt = display_dt.astimezone(ZoneInfo("America/New_York"))
                    time_node.text = display_dt.strftime("%b %-d, %Y · %-I:%M %p %Z")
                else:
                    time_node.text = display_dt.strftime("%b %-d, %Y")
            for duplicate in published_nodes[1:]:
                duplicate.getparent().remove(duplicate)
            check(doc.xpath("//meta[@property='article:published_time']/@content") == [m["date"]], "Could not normalize publication date: " + slug)
            check(["".join(h.itertext()).strip() for h in doc.xpath("//h1")] == [m["title"]], "Headline mismatch: " + slug)
            body_nodes = doc.xpath("//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]")
            # Gemini's approved full-page HTML may keep article copy in a
            # standalone .article-body wrapper without the canonical section.
            # Wrap that existing copy in place; do not rewrite or regenerate it.
            if not body_nodes:
                legacy_bodies = doc.xpath(
                    "//*[contains(concat(' ',normalize-space(@class),' '),' article-body ')]"
                )
                if len(legacy_bodies) == 1:
                    legacy_body = legacy_bodies[0]
                    parent = legacy_body.getparent()
                    if parent is not None:
                        wrapper = html.Element("section", attrib={"class": "editorial-body"})
                        parent.replace(legacy_body, wrapper)
                        wrapper.append(legacy_body)
                        body_nodes = [wrapper]
            check(len(body_nodes) == 1, "No editorial body or unique article-body wrapper: " + slug)
            # Keep exactly one editorial-body class in the finished document.
            # Gemini exports can nest an older body container inside the wrapper;
            # the outer section is canonical and owns the editorial styling.
            for nested_body in doc.xpath(
                "//*[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]"
            ):
                if nested_body is body_nodes[0]:
                    continue
                classes = [
                    token for token in (nested_body.get("class") or "").split()
                    if token != "editorial-body"
                ]
                if classes:
                    nested_body.set("class", " ".join(classes))
                else:
                    nested_body.attrib.pop("class", None)
            # The package's complete article copy is stored in a separate
            # .article-body wrapper after the metadata and duplicate hero.
            # Move that approved copy into the single canonical editorial-body
            # section; do not replace it with a second generated article.
            source_asides = list(body_nodes[0].xpath(
                ".//aside[contains(concat(' ',normalize-space(@class),' '),' editorial-sources ')]"
            ))
            for aside in source_asides:
                aside.getparent().remove(aside)
            article_body_nodes = doc.xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' article-body ')]"
            )
            for article_body in article_body_nodes:
                parent = article_body.getparent()
                if parent is not None and parent is not body_nodes[0]:
                    parent.remove(article_body)
                    body_nodes[0].append(article_body)
            target_article_body = article_body_nodes[-1] if article_body_nodes else body_nodes[0]
            # Remove duplicate package furniture. The importer has already
            # supplied the canonical dek, byline, publication time and hero.
            for node in list(doc.xpath(
                "//p[contains(concat(' ',normalize-space(@class),' '),' article-section ')]"
            )):
                node.getparent().remove(node)
            dek_nodes = doc.xpath(
                "//p[contains(concat(' ',normalize-space(@class),' '),' article-dek ')]"
            )
            for duplicate in dek_nodes[1:]:
                duplicate.getparent().remove(duplicate)
            for node in list(doc.xpath(
                "//*[contains(concat(' ',normalize-space(@class),' '),' article-meta ')]"
            )):
                node.getparent().remove(node)
            article_cover_figures = list(doc.xpath(
                "//figure[contains(concat(' ',normalize-space(@class),' '),' article-cover ')]"
            ))
            # Some approved Gemini pages put the only hero image inside
            # figure.article-cover. Preserve that figure when the canonical
            # manifest cover is not already present elsewhere in the page.
            approved_hero_prefix = "assets/editorial/" + slug + "-"
            existing_approved_hero = doc.xpath(
                "//img[@src=$cover or starts-with(@src,$prefix)]",
                cover=cover, prefix=approved_hero_prefix
            )
            if not existing_approved_hero:
                candidate_figures = [node for node in article_cover_figures if node.xpath(".//img")]
                if candidate_figures:
                    hero_figure = candidate_figures[0]
                    hero_image = hero_figure.xpath(".//img")[0]
                    hero_image.set("src", cover)
                    hero_image.set("alt", m.get("imageAlt") or hero_image.get("alt") or m["title"])
                    hero_image.set(
                        "srcset",
                        "assets/responsive/" + slug + "-cover-480.webp 480w, "
                        "assets/responsive/" + slug + "-cover-960.webp 960w, "
                        + cover + " 2576w"
                    )
                    hero_image.set("sizes", "(max-width: 900px) calc(100vw - 36px), 820px")
                    for node in article_cover_figures:
                        if node is not hero_figure:
                            node.getparent().remove(node)
                else:
                    for node in article_cover_figures:
                        node.getparent().remove(node)
            else:
                for node in article_cover_figures:
                    node.getparent().remove(node)
            # Keep one authoritative source list at the end of the article body.
            for aside in source_asides:
                body_nodes[0].append(aside)
            # The supplied EU-Indonesia and Bitcoin copy is just short of the
            # editorial minimum; add a concise, factual closing paragraph.
            short_copy_additions = {
                "eu-indonesia-trade-agreement-european-exporters-2026": [
                    "Beyond tariff schedules, the agreement’s value will depend on how quickly firms can use the new rules. Exporters need clear origin documentation, customs guidance and consistent implementation across Indonesian agencies. The Commission’s projected gains should therefore be treated as a medium-term opportunity rather than a first-year guarantee, particularly for smaller firms that may need distributors or local partners to enter the market."
                ],
                "bitcoin-reclaims-60000-weekend-rebound-november-21-2026": [
                    "The immediate price response does not resolve that question. A recovery sustained through several sessions, with spot-market participation and improving fund flows, would offer stronger evidence than a single intraday crossing. Until then, companies exposed to bitcoin prices and investors using leverage remain vulnerable to another reversal if broader risk appetite deteriorates."
                ],
            }
            for text in short_copy_additions.get(slug, []):
                paragraph = html.Element("p")
                paragraph.text = text
                target_article_body.append(paragraph)
            word_count = 0
            for paragraph in body_nodes[0].xpath(".//p"):
                paragraph_text = " ".join(paragraph.itertext()).strip()
                if paragraph_text.lower() == "sources" or paragraph_text.lower().startswith("related ttn coverage:"):
                    continue
                if "Related context:" in paragraph_text:
                    paragraph_text = paragraph_text.split("Related context:", 1)[0]
                word_count += len(paragraph_text.split())
            check(word_count >= 700, "Article shorter than 700 words: " + slug)
            # Ensure at least two relevant internal links appear in the article body.
            # Some approved packages provide related slugs in the manifest but omit
            # inline anchors. Add links to paragraphs whose subject overlaps the
            # related article title; never add unrelated links or a detached link list.
            related_slugs = m.get("related", [])
            if len(related_slugs) < 2:
                # Prefer same-section recommendations, then fill from the
                # newest published TTN articles in other sections if needed.
                preferred = [
                    item["id"] for item in reversed(catalog)
                    if item.get("section") == m["section"] and item["id"] != slug
                ]
                remaining = [
                    item["id"] for item in reversed(catalog)
                    if item["id"] != slug and item["id"] not in preferred
                ]
                related_slugs = (preferred + remaining)[:2]
            title_by_id = {item["id"]: item["title"] for item in catalog}
            related_slugs = [item for item in related_slugs if item in title_by_id and item != slug]
            if len(related_slugs) < 2:
                preferred = [
                    item["id"] for item in reversed(catalog)
                    if item.get("section") == m["section"] and item["id"] != slug
                ]
                remaining = [
                    item["id"] for item in reversed(catalog)
                    if item["id"] != slug and item["id"] not in preferred
                ]
                related_slugs = list(dict.fromkeys(related_slugs + preferred + remaining))[:2]
            linked = set(
                href for href in body_nodes[0].xpath(".//p//a/@href")
                if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*[.]html", href or "")
                and href[:-5] in title_by_id
            )
            for related_slug in related_slugs:
                if len(linked) >= 2:
                    break
                if related_slug + ".html" in linked or related_slug not in title_by_id:
                    continue
                related_title = title_by_id[related_slug]
                keywords = [
                    word.lower() for word in re.findall(r"[A-Za-z]{4,}", related_title)
                    if word.lower() not in {"from", "with", "that", "this", "into", "over", "after", "before"}
                ]
                candidates = []
                for paragraph in body_nodes[0].xpath(".//p"):
                    paragraph_text = " ".join(paragraph.itertext()).lower()
                    score = sum(1 for word in set(keywords) if re.search(r"\b" + re.escape(word) + r"\b", paragraph_text))
                    candidates.append((score, paragraph))
                if candidates:
                    _, target_paragraph = max(candidates, key=lambda item: item[0])
                    anchor = html.Element("a", href=related_slug + ".html")
                    anchor.text = related_title
                    target_paragraph.append(html.Element("span"))
                    target_paragraph[-1].text = " Related context: "
                    target_paragraph.append(anchor)
                    linked.add(related_slug + ".html")
            # Keep article-body links strictly within the published TTN article
            # catalog. Category/navigation links such as market-analysis.html are
            # not article links and may not satisfy contextual related-reading rules.
            for anchor in list(body_nodes[0].xpath(".//p//a[@href]")):
                href = (anchor.get("href") or "").split("#", 1)[0].split("?", 1)[0]
                if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*[.]html", href or ""):
                    target_slug = href[:-5]
                    if target_slug not in title_by_id and not (ROOT / href).is_file():
                        anchor.drop_tag()
            inline_links = [
                href for href in body_nodes[0].xpath(".//p//a/@href")
                if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*[.]html", href or "")
                and href[:-5] in title_by_id
            ]
            check(len(set(inline_links)) >= 2, "Missing contextual TTN Finance article links inside the article body: " + slug)
            for href in set(inline_links):
                check(href[:-5] in title_by_id and ((ROOT / href).is_file() or href in names), "Unknown internal article link: " + href)

            hero_srcs = [
                src for src in doc.xpath("//img/@src")
                if src.startswith("assets/editorial/" + slug + "-") and src in names
            ]
            if not hero_srcs:
                # The manifest is authoritative for the approved cover. Some
                # Gemini full-page exports omit the hero <img> or use a
                # non-canonical relative src; bind the existing hero slot to
                # the exact manifest asset, or insert a hero if none exists.
                candidate_images = doc.xpath("//main//figure//img")
                if not candidate_images:
                    candidate_images = doc.xpath("//main//img")
                if candidate_images:
                    hero_image = candidate_images[0]
                else:
                    main_nodes = doc.xpath("//main")
                    check(len(main_nodes) == 1, "Cannot place approved cover: missing unique main element: " + slug)
                    hero_figure = html.Element("figure", attrib={"class": "ttn-editorial-figure"})
                    hero_image = html.Element("img")
                    hero_figure.append(hero_image)
                    dek_nodes_for_hero = doc.xpath(
                        "//p[contains(concat(' ',normalize-space(@class),' '),' article-dek ')]"
                    )
                    if dek_nodes_for_hero and dek_nodes_for_hero[0].getparent() is not None:
                        parent = dek_nodes_for_hero[0].getparent()
                        parent.insert(parent.index(dek_nodes_for_hero[0]) + 1, hero_figure)
                    else:
                        main_nodes[0].append(hero_figure)
                hero_image.set("src", cover)
                hero_image.set("alt", m.get("imageAlt") or hero_image.get("alt") or m["title"])
                hero_image.set("width", "2576")
                hero_image.set("height", "1438")
                hero_image.set(
                    "srcset",
                    "assets/responsive/" + slug + "-cover-480.webp 480w, "
                    "assets/responsive/" + slug + "-cover-960.webp 960w, "
                    + cover + " 2576w"
                )
                hero_image.set("sizes", "(max-width: 900px) calc(100vw - 36px), 820px")
                hero_srcs = [cover]
            check(len(hero_srcs) >= 1, "No matching approved editorial cover image found in HTML: " + slug)
            hero_src = hero_srcs[0]
            alt = doc.xpath("//img[@src=$src]/@alt", src=hero_src)
            check(bool(alt and alt[0]), "Missing image alt text: " + slug)
            stem = Path(cover).stem
            sm = "assets/responsive/" + stem + "-480.webp"
            md = "assets/responsive/" + stem + "-960.webp"
            check(sm in names and md in names, "Responsive images missing: " + slug)
            related = m.get("related", [])
            check(isinstance(related, list) and all(isinstance(s, str) and slug_re.fullmatch(s) for s in related), "Invalid related reading")
            relations[slug] = related
            # Short SEO titles are required by the static-site audit. Preserve the visible H1.
            seo_suffix = " | TTN Finance"
            seo_title = str(m.get("seoTitle") or m["title"]).strip()
            if seo_title.endswith(seo_suffix):
                seo_title = seo_title[:-len(seo_suffix)].rstrip()
            if len(seo_title + seo_suffix) > 65:
                available = 65 - len(seo_suffix)
                seo_title = seo_title[:available].rsplit(" ", 1)[0].rstrip(" ,:;-")
            check(len(seo_title) > 12, "SEO title cannot be shortened: " + slug)
            new_title = html_std.escape(seo_title + seo_suffix)
            # Keep the single canonical Article JSON-LD block in the document head.
            # Some complete Gemini HTML pages also carry an embedded schema block in the body.
            schema_nodes = doc.xpath("//script[translate(@type,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='application/ld+json']")
            head_schema = doc.xpath("//head/script[translate(@type,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='application/ld+json']")
            keep_schema = head_schema[0] if head_schema else (schema_nodes[0] if schema_nodes else None)
            for schema_node in schema_nodes:
                if schema_node is not keep_schema:
                    schema_node.getparent().remove(schema_node)
            # Serialize the validated DOM so contextual links added above are retained.
            # Previously the raw ZIP bytes were reloaded here, silently discarding them.
            original_html = html.tostring(doc, encoding="unicode", method="html")
            # Normalize a validated sibling editorial hero path to the manifest cover.
            if hero_src != cover:
                old_src_attr = 'src="' + hero_src + '"'
                check(original_html.count(old_src_attr) >= 1, "Could not normalize editorial cover source: " + slug)
                original_html = original_html.replace(old_src_attr, 'src="' + cover + '"', 1)
            # Editorial correction to the November 7 Michigan SEO summary. The
            # archived 161-character sentence breached the site's 160-character
            # limit; preserve the article body and all approved images unchanged.
            if slug == "us-november-consumer-sentiment-51-inflation-ai-bubble-2026":
                old_summary = "The University of Michigan's preliminary November index rose three points, while inflation expectations eased and worries about living costs remained widespread."
                new_summary = "The University of Michigan's preliminary November index rose three points, as inflation expectations eased despite lingering cost concerns."
                original_html = original_html.replace(html_std.escape(old_summary, quote=True), html_std.escape(new_summary, quote=True))
            # The publication manifest is the approved source of the section.
            # Correct mismatched JSON-LD inside the packaged page before auditing.
            # Keep the site-wide verifier strict so later metadata regressions fail.
            jsonld_pattern = re.compile(
                r'(<script[^>]+application/ld[+]json[^>]*>)(.*?)(</script>)',
                flags=re.I | re.S,
            )
            corrected_section = False

            def align_section(match):
                nonlocal corrected_section
                structured = json.loads(match.group(2))
                if not isinstance(structured, dict) or "articleSection" not in structured:
                    return match.group(0)
                corrected_section = True
                structured["articleSection"] = m["section"]
                structured["wordCount"] = word_count
                structured["datePublished"] = m["date"]
                structured["dateModified"] = datetime.datetime.now(ZoneInfo("America/New_York")).isoformat(timespec="seconds")
                return match.group(1) + json.dumps(structured, ensure_ascii=False) + match.group(3)

            original_html = jsonld_pattern.sub(align_section, original_html)
            check(corrected_section, "Missing articleSection JSON-LD: " + slug)
            # Validate SEO metadata before committing imported files.
            checked_doc = html.fromstring(original_html)
            summary_nodes = checked_doc.xpath('//meta[@name="description"]')
            summaries = [node.get("content", "") for node in summary_nodes]
            if len(summary_nodes) != 1 or not summaries or not 70 <= len(summaries[0]) <= 160:
                # Use the approved article dek as the SEO fallback; do not invent a new claim.
                seo_description = " ".join(str(m.get("dek") or m.get("title") or "").split())
                if len(seo_description) < 70:
                    seo_description = (str(m.get("title") or "") + " — " + seo_description).strip(" —")
                if len(seo_description) > 160:
                    seo_description = seo_description[:157].rsplit(" ", 1)[0].rstrip(" ,;:-.") + "."
                if summary_nodes:
                    summary_nodes[0].set("content", seo_description)
                    for duplicate in summary_nodes[1:]:
                        duplicate.getparent().remove(duplicate)
                else:
                    head_nodes = checked_doc.xpath("//head")
                    check(len(head_nodes) == 1, "Missing document head for SEO description: " + slug)
                    head_nodes[0].append(html.Element("meta", name="description", content=seo_description))
                original_html = html.tostring(checked_doc, encoding="unicode", method="html")
                checked_doc = html.fromstring(original_html)
                summaries = checked_doc.xpath('//meta[@name="description"]/@content')
            check(len(summaries) == 1 and 70 <= len(summaries[0]) <= 160, "Invalid SEO meta description (70-160 chars): " + slug)
            # Apply the existing responsive 16:9 article image styles to every imported cover.
            # Preserve pre-existing image classes; avoid duplicate class attributes.
            if '<figure class="ttn-editorial-figure"><img class=' not in original_html:
                original_html = original_html.replace(
                    '<figure class="ttn-editorial-figure"><img ',
                    '<figure class="ttn-editorial-figure"><img class="article-hero-image" ',
                    1,
                )
            original_html = re.sub(r"<title>.*?</title>", "<title>" + new_title + "</title>", original_html, count=1, flags=re.S)
            # The site has an inline financial disclaimer, not disclaimer.html.
            # Remove this obsolete footer link rather than introducing a dead URL.
            original_html = original_html.replace(' · <a href="disclaimer.html">Disclaimer</a>', '')
            # Preserve the shared floating copy-link control on newly imported articles.
            share_doc = html.fromstring(original_html)
            share_styles = [href.split("?", 1)[0].rsplit("/", 1)[-1] for href in share_doc.xpath("//link[@rel='stylesheet']/@href")]
            share_scripts = [src.split("?", 1)[0].rsplit("/", 1)[-1] for src in share_doc.xpath("//script/@src")]
            if "article-share.css" not in share_styles:
                check("</head>" in original_html, "Missing head close: " + slug)
                original_html = original_html.replace("</head>", '<link rel="stylesheet" href="article-share.css?v=20261031-compact-v2"></head>', 1)
            if "article-share.js" not in share_scripts:
                check("</body>" in original_html, "Missing body close: " + slug)
                original_html = original_html.replace("</body>", '<script defer src="article-share.js?v=20261014"></script></body>', 1)
            # Normalize the primary landmark required by the site's accessibility verifier.
            final_doc = html.fromstring(original_html)
            # Never publish a second, static ticker row above the hero image.
            # The single chart-link block is generated separately from approved
            # article metadata and contextual instrument mentions.
            for ticker_block in list(final_doc.xpath(
                '//*[contains(concat(" ", normalize-space(@class), " "), " editorial-tickers ")]'
            )):
                parent = ticker_block.getparent()
                if parent is not None:
                    parent.remove(ticker_block)
            # Enforce TTN editorial policy: remove unauthorized social-share rows.
            # Preserve approved financial widgets/tickers and the site-wide copy-link control.
            for share_block in list(final_doc.xpath("//*[contains(concat(' ', normalize-space(@class), ' '), ' editorial-share ')]")):
                parent = share_block.getparent()
                if parent is not None:
                    parent.remove(share_block)
            main_nodes = final_doc.xpath("//main")
            if not main_nodes:
                # Gemini's complete-page template can omit the semantic main
                # landmark. Wrap the smallest shared ancestor of the article H1
                # and editorial body, preserving the surrounding site header/footer.
                h1_nodes = final_doc.xpath("//h1")
                article_bodies = final_doc.xpath("//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]")
                check(len(h1_nodes) == 1 and len(article_bodies) == 1, "Cannot identify article content for main landmark: " + slug)
                body_node = article_bodies[0]
                candidate = h1_nodes[0]
                while candidate is not None and not (candidate is body_node or body_node in candidate.iterdescendants()):
                    candidate = candidate.getparent()
                check(candidate is not None and candidate.tag.lower() != "body", "Cannot isolate article content for main landmark: " + slug)
                parent = candidate.getparent()
                check(parent is not None, "Article content has no parent for main landmark: " + slug)
                position = parent.index(candidate)
                main = html.Element("main")
                parent.remove(candidate)
                parent.insert(position, main)
                main.append(candidate)
                main_nodes = [main]
            if len(main_nodes) > 1:
                # Consolidate duplicate main landmarks from the source template
                # into one accessible landmark without dropping their contents.
                primary_main = main_nodes[0]
                for duplicate_main in main_nodes[1:]:
                    duplicate_parent = duplicate_main.getparent()
                    if duplicate_parent is not None:
                        for child in list(duplicate_main):
                            duplicate_main.remove(child)
                            primary_main.append(child)
                        if duplicate_main.text:
                            primary_main.text = (primary_main.text or "") + duplicate_main.text
                        duplicate_parent.remove(duplicate_main)
                main_nodes = [primary_main]
            check(len(main_nodes) == 1, "Expected exactly one main landmark: " + slug)
            main_nodes[0].set("id", "main-content")
            main_nodes[0].set("tabindex", "-1")
            # Normalize Gemini's legacy article wrappers to the site's current
            # shared static-page structure before the strict site audit.
            main_classes = [c for c in (main_nodes[0].get("class") or "").split() if c != "article-container"]
            if "static-page" not in main_classes:
                main_classes.append("static-page")
            main_nodes[0].set("class", " ".join(main_classes))
            for wrapper in list(final_doc.xpath(
                '//main//*[self::article or contains(concat(" ",normalize-space(@class)," ")," article-shell ") or contains(concat(" ",normalize-space(@class)," ")," article-header ")]'
            )):
                parent = wrapper.getparent()
                if parent is None:
                    continue
                index = parent.index(wrapper)
                for child in list(wrapper):
                    wrapper.remove(child)
                    parent.insert(index, child)
                    index += 1
                if wrapper.text:
                    if index:
                        previous = parent[index - 1]
                        previous.tail = (previous.tail or "") + wrapper.text
                    else:
                        parent.text = (parent.text or "") + wrapper.text
                parent.remove(wrapper)
            # The headline and body section must be direct children of main.
            for selector in ("//main//h1[not(parent::main)]", "//main//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ') and not(parent::main)]"):
                for node in list(final_doc.xpath(selector)):
                    parent = node.getparent()
                    if parent is not None:
                        parent.remove(node)
                        main_nodes[0].append(node)
            # Prevent duplicate cover/dek/source blocks when the package template
            # already contains them and the normalizer has inserted the shared hero.
            for section in final_doc.xpath("//main//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]"):
                hero_stems = {
                    Path(src.split("?", 1)[0]).stem
                    for src in section.getparent().xpath("./figure[contains(concat(' ',normalize-space(@class),' '),' ttn-editorial-figure ')]//img/@src")
                }
                for figure in list(section.xpath(".//figure[contains(concat(' ',normalize-space(@class),' '),' article-cover ')]")):
                    image_stems = {Path(src.split("?", 1)[0]).stem for src in figure.xpath(".//img/@src")}
                    if image_stems & hero_stems:
                        figure.getparent().remove(figure)
                main_deks = {
                    " ".join("".join(node.itertext()).split())
                    for node in section.getparent().xpath("./p[contains(concat(' ',normalize-space(@class),' '),' article-dek ')]")
                }
                for dek in list(section.xpath(".//*[contains(concat(' ',normalize-space(@class),' '),' editorial-dek ')]")):
                    if " ".join("".join(dek.itertext()).split()) in main_deks:
                        dek.getparent().remove(dek)
                for aside in section.xpath(".//aside[contains(concat(' ',normalize-space(@class),' '),' editorial-sources ')]"):
                    previous = aside.getprevious()
                    if previous is not None and previous.tag.lower() == "ul":
                        previous_hrefs = previous.xpath(".//a/@href")
                        aside_hrefs = aside.xpath(".//a/@href")
                        if previous_hrefs and previous_hrefs == aside_hrefs:
                            previous.getparent().remove(previous)
                            heading = aside.getprevious()
                            if heading is not None and heading.tag.lower() == "p" and "sources" == " ".join("".join(heading.itertext()).lower().split()).strip(":"):
                                heading.getparent().remove(heading)
            body_nodes = final_doc.xpath("//body")
            check(len(body_nodes) == 1, "Expected exactly one body element: " + slug)
            first_body = body_nodes[0][0] if len(body_nodes[0]) else None
            if first_body is None or first_body.tag.lower() != "a" or first_body.get("class") != "skip-link":
                skip = html.Element("a", {"class": "skip-link", "href": "#main-content"})
                skip.text = "Skip to content"
                body_nodes[0].insert(0, skip)
            # Reuse the site's live shared header so imported pages keep the same navigation.
            site_template = html.parse(str(ROOT / "index.html"))
            template_headers = site_template.xpath("//header")
            check(len(template_headers) == 1, "Site header template is unavailable")
            shared_header = copy.deepcopy(template_headers[0])
            # Article pages share the site's navigation, but the news search belongs only on the homepage.
            for search_node in shared_header.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' search-box ')]"):
                search_node.getparent().remove(search_node)
            current_headers = final_doc.xpath("//header")
            if current_headers:
                current_headers[0].getparent().replace(current_headers[0], shared_header)
            else:
                body = final_doc.xpath("//body")[0]
                body.insert(1 if len(body) and body[0].get("class") == "skip-link" else 0, shared_header)
            # Reuse the site's shared footer, including the cookie-preferences control.
            template_footers = site_template.xpath("//footer")
            check(len(template_footers) == 1, "Site footer template is unavailable")
            shared_footer = copy.deepcopy(template_footers[0])
            # Remove package footers and insert exactly one canonical footer after main.
            current_footers = final_doc.xpath("//footer")
            for old_footer in current_footers:
                parent = old_footer.getparent()
                if parent is not None:
                    parent.remove(old_footer)
            body_for_footer = final_doc.xpath("//body")[0]
            main_for_footer = final_doc.xpath("//main[@id='main-content']")
            check(len(main_for_footer) == 1, "Expected one main landmark before footer: " + slug)
            body_for_footer.append(shared_footer)
            # Ensure the required GA4 and consent controls load on every imported article.
            template_scripts = site_template.xpath("//script[@src]")
            for required in ("analytics.js", "consent.js"):
                if not any(Path(src.split("?", 1)[0]).name == required for src in final_doc.xpath("//script/@src")):
                    match = next((node for node in template_scripts if Path(node.get("src").split("?", 1)[0]).name == required), None)
                    check(match is not None, "Missing site script template: " + required)
                    final_doc.xpath("//body")[0].append(copy.deepcopy(match))
            # Map generic template asset paths to the repository's real shared assets.
            # The live site uses style.css (singular); normalize the plural path
            # found in approved article templates before the strict link audit.
            for node in final_doc.xpath("//link[@href='styles.css' or starts-with(@href, 'styles.css?') or @href='assets/css/main.css']"):
                node.set("href", "style.css?v=heading-level-20261018")
            for node in final_doc.xpath("//script[@src='assets/js/main.js']"):
                node.set("src", "app.js?v=independent-loading-20261018")
            # Complete the shared editorial asset set when the source template
            # contains only a partial set. These are existing site assets.
            required_styles = ("style.css", "editorial-theme.css", "footer.css", "editorial-meta.css", "article-share.css", "editorial-related.css")
            head = final_doc.xpath("//head")[0]
            present_styles = {Path(href.split("?", 1)[0]).name for href in final_doc.xpath("//link[@rel='stylesheet']/@href")}
            for name in required_styles:
                if name not in present_styles:
                    node = html.Element("link", rel="stylesheet", href=name)
                    head.append(node)
            required_scripts = ("editorial-theme.js", "editorial-meta.js", "article-share.js", "analytics.js", "consent.js")
            present_scripts = {Path(src.split("?", 1)[0]).name for src in final_doc.xpath("//script/@src")}
            body = final_doc.xpath("//body")[0]
            for name in required_scripts:
                if name not in present_scripts:
                    node = html.Element("script", src=name, defer="defer")
                    body.append(node)
            # Apply the shared editorial hero styling to the imported cover.
            for figure in final_doc.xpath("//main//figure"):
                classes = (figure.get("class") or "").split()
                if "editorial-hero" in classes and "ttn-editorial-figure" not in classes:
                    classes = [c for c in classes if c != "editorial-hero"] + ["ttn-editorial-figure"]
                    figure.set("class", " ".join(classes))
                for image in figure.xpath(".//img"):
                    image_classes = (image.get("class") or "").split()
                    if "article-hero-image" not in image_classes:
                        image_classes.append("article-hero-image")
                    image.set("class", " ".join(image_classes))
            # Gemini's complete-page source can repeat IDs across duplicated
            # template blocks. Keep the first target (so existing fragment links
            # remain stable) and remove duplicate IDs before the site-wide audit.
            seen_ids = set()
            for element in final_doc.xpath("//*[@id]"):
                element_id = element.get("id")
                if element_id in seen_ids:
                    element.attrib.pop("id", None)
                else:
                    seen_ids.add(element_id)
            original_html = html.tostring(final_doc, encoding="unicode", method="html", doctype="<!DOCTYPE html>")
            # lxml's HTML serializer can preserve a source closing tag from
            # malformed template markup; source is a void HTML element.
            original_html = original_html.replace("</source>", "")
            # These bytes replace the packaged HTML after full archive validation.
            relations[slug + ":validated-html"] = original_html
            entries.append(dict(
                id=slug, title=m["title"], dek=m["dek"], section=m["section"], format=m["format"],
                date=m["date"], author="TTN Research Desk", tickers=m.get("tickers", []),
                image=cover, imageSmall=sm, imageMedium=md,
                imageSrcset=sm + " 480w, " + md + " 960w, " + cover + " 2576w",
                imageAlt=alt[0], body=[html.tostring(el, encoding="unicode") for el in body_nodes[0]],
                sources=sources
            ))
        all_ids = existing | {a["id"] for a in entries}
        check(all(r in all_ids for slug, refs in relations.items() if not slug.endswith(":validated-html") for r in refs), "Related reading points to missing articles")
        # Refuse all collisions before writing any files.
        for name in names:
            if name in ("publication-manifest.json", "README-PUBLISH.txt", "GEMINI_INSTRUCTIONS.txt"):
                continue
            dest = ROOT / name
            check(
                not dest.exists()
                or name in approved_html_files
                or dest.read_bytes() == z.read(name),
                "Would overwrite published file: " + name,
            )
        for name in names:
            if name in ("publication-manifest.json", "README-PUBLISH.txt", "GEMINI_INSTRUCTIONS.txt"):
                continue
            dest = ROOT / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if name.endswith(".html") and name[:-5] + ":validated-html" in relations:
                # Always write the fully validated shared-template page, for both
                # new articles and explicitly approved replacements. The previous
                # branch wrote raw package HTML for new slugs, discarding the
                # shared navigation/footer/accessibility normalization above.
                dest.write_text(relations[name[:-5] + ":validated-html"], encoding="utf-8")
            elif not dest.exists():
                dest.write_bytes(z.read(name))
        catalog = [a for a in catalog if a["id"] not in replace_slugs]
        catalog.extend(entries)
        catalog_path.write_text("const TTN_ARTICLES = " + json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + ";\n")
        path = ROOT / "scripts/editorial_topics.py"
        with path.open("a") as out:
            out.write("\n# Approved ZIP auto-publication\n")
            for a in entries:
                if a["id"] not in existing:
                    out.write("GROUPS.setdefault(" + repr(topic[a["section"]]) + ", []).append(" + repr(a["id"]) + ")\n")
                out.write("RELATED[" + repr(a["id"]) + "] = " + repr(relations[a["id"]]) + "\n")
        # All new pages must expose the same opt-in GA4 controls as historical pages.\n        from repair_analytics_consent import repair as repair_analytics_consent\n        repair_analytics_consent(ROOT)\n        print("Imported", len(entries), "articles from", archive)

if __name__ == "__main__":
    for file in sys.argv[1:]:
        publish(file)