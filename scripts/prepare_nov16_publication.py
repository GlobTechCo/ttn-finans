#!/usr/bin/env python3
"""Build an importer-compatible ZIP from the reviewed Nov. 16 TTN source package."""
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from lxml import etree, html
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://globtechco.github.io/ttn-finans/"
ARCHIVE_NAME = "TTN_Finance_Publication_Package_2026-11-16.zip"

DEKS = {
    "wall-street-slides-treasury-yields-above-5-1-nvidia-earnings-november-16-2026":
        "U.S. equities weakened as Treasury yields stayed above 5.1%, leaving investors focused on Nvidia's results and the outlook for AI spending.",
    "bitcoin-64500-crypto-stocks-fall-nasdaq-november-16-2026":
        "Bitcoin hovered near $64,500 after a weekend slide, while listed crypto companies fell as investors cut exposure to risk assets.",
    "nvidia-first-earnings-without-jensen-huang-trump-possible-return-november-16-2026":
        "Nvidia is preparing to report results under interim CEO Colette Kress as Trump comments revive speculation about Jensen Huang's possible return.",
}

SOURCES = {
    "wall-street-slides-treasury-yields-above-5-1-nvidia-earnings-november-16-2026": [
        {"label": "Charles Schwab market update, November 16, 2026", "url": "https://www.schwab.com/learn/story/stock-market-update-open"},
        {"label": "U.S. Treasury daily par-yield curve", "url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve"},
        {"label": "Associated Press market report, November 16, 2026", "url": "https://apnews.com/article/35786b8f539ec95f16ae0500f71cfcc7"},
        {"label": "Nvidia investor relations events", "url": "https://investor.nvidia.com/events-and-presentations/events-and-presentations/default.aspx"},
    ],
    "bitcoin-64500-crypto-stocks-fall-nasdaq-november-16-2026": [
        {"label": "The Block, Strategy's November 16 Bitcoin purchase report", "url": "https://www.theblock.co/news/business/2026-11-16-this-dip-could-use-a-little-orange-michael-saylor-strategy-bitcoin-tumbles-440886"},
        {"label": "Investing.com, Strategy November 16 filing report", "url": "https://www.investing.com/news/cryptocurrency-news/strategy-buys-485-bitcoin-sells-mstr-shares-for-2447m-in-atm-offering-432SI-5029704"},
        {"label": "Charles Schwab market update, November 16, 2026", "url": "https://www.schwab.com/learn/story/stock-market-update-open"},
    ],
    "nvidia-first-earnings-without-jensen-huang-trump-possible-return-november-16-2026": [
        {"label": "Reuters, November 16, 2026", "url": "https://www.reuters.com/world/china/trump-says-he-would-not-mind-huang-being-reinstated-nvidia-ceo-2026-11-16/"},
        {"label": "Nvidia investor relations", "url": "https://investor.nvidia.com/news/"},
        {"label": "Nvidia filings with the U.S. Securities and Exchange Commission", "url": "https://www.sec.gov/edgar/browse/?CIK=1045810&owner=exclude"},
    ],
}

def set_meta(doc, key: str, value: str, attr: str = "name") -> None:
    nodes = doc.xpath(f"//meta[@{attr}=$key]", key=key)
    if nodes:
        nodes[0].set("content", value)
        for extra in nodes[1:]:
            extra.getparent().remove(extra)
    else:
        head = doc.xpath("//head")[0]
        node = html.Element("meta")
        node.set(attr, key)
        node.set("content", value)
        head.append(node)

def set_link(doc, rel: str, href: str) -> None:
    nodes = doc.xpath("//link[@rel=$rel]", rel=rel)
    if nodes:
        nodes[0].set("href", href)
        for extra in nodes[1:]:
            extra.getparent().remove(extra)
    else:
        node = html.Element("link", rel=rel, href=href)
        doc.xpath("//head")[0].append(node)

def localize_internal_links(fragment: html.HtmlElement) -> list[str]:
    related = []
    for anchor in fragment.xpath(".//a[@href]"):
        href = anchor.get("href", "")
        parsed = urlparse(href)
        if parsed.netloc == "globtechco.github.io" and parsed.path.startswith("/ttn-finans/"):
            href = Path(parsed.path).name
            anchor.set("href", href)
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*[.]html", href):
            related.append(href[:-5])
    return list(dict.fromkeys(related))

def build_page(template: str, slug: str, item: dict, fragment_text: str,
               seo: dict, cover_path: str, responsive_480: str,
               responsive_960: str, width: int, height: int,
               sources: list[dict]) -> tuple[str, int, list[str]]:
    doc = html.fromstring(template)
    title = item["title"]
    date = item["date"]
    description = seo["description"]
    section = item["category"]
    section_page = {
        "Market Analysis": "analysis.html",
        "Tech & AI": "tech-ai.html",
        "Crypto": "crypto.html",
    }[section]

    fragment = html.fragment_fromstring(fragment_text, create_parent="div")
    related = localize_internal_links(fragment)
    check_h1 = fragment.xpath(".//h1")
    if len(check_h1) != 1 or " ".join(check_h1[0].itertext()).strip() != title:
        raise ValueError(f"Headline mismatch in fragment: {slug}")
    for node in check_h1:
        node.getparent().remove(node)

    main_nodes = doc.xpath("//main")
    if len(main_nodes) != 1:
        raise ValueError(f"Expected one main element in template: {slug}")
    main = main_nodes[0]
    main.clear()
    main.set("class", "static-page")
    main.set("id", "main-content")
    main.set("tabindex", "-1")

    breadcrumb = html.Element("p")
    link = etree.SubElement(breadcrumb, "a", href=section_page)
    link.text = "← " + section
    main.append(breadcrumb)

    badge = html.Element("span", {"class": "ttn-original-badge"})
    badge.text = section
    main.append(badge)

    h1 = html.Element("h1")
    h1.text = title
    main.append(h1)

    deck = html.Element("p", {"class": "article-dek"})
    deck.text = DEKS[slug]
    main.append(deck)

    meta = html.Element("p", {
        "class": "editorial-meta",
        "data-editorial-byline": "",
        "data-author": "TTN Research Desk",
    })
    author = html.SubElement(meta, "span", {"class": "editorial-author"})
    author.text = "TTN Research Desk"
    published = html.SubElement(meta, "span", {"class": "editorial-published"})
    time = html.SubElement(published, "time", datetime=date)
    time.text = datetime.strptime(date, "%Y-%m-%d").strftime("%b %d, %Y").replace(" 0", " ")
    main.append(meta)

    figure = html.Element("figure", {"class": "ttn-editorial-figure"})
    image = html.SubElement(figure, "img", {
        "class": "article-hero-image",
        "src": cover_path,
        "alt": seo.get("imageAlt") or title,
        "width": str(width),
        "height": str(height),
        "loading": "eager",
        "fetchpriority": "high",
        "srcset": f"{responsive_480} 480w, {responsive_960} 960w, {cover_path} {width}w",
        "sizes": "(max-width: 900px) calc(100vw - 36px), 820px",
    })
    main.append(figure)

    body = html.Element("section", {"class": "editorial-body"})
    for child in list(fragment):
        body.append(child)
    main.append(body)

    word_count = sum(
        len(" ".join(p.itertext()).split())
        for p in body.xpath("./p")
    )
    if word_count < 700:
        raise ValueError(f"Article body below 700 words ({word_count}): {slug}")
    if len(related) < 2:
        raise ValueError(f"Fewer than two contextual internal links: {slug}")

    title_node = doc.xpath("//title")
    if not title_node:
        raise ValueError(f"Missing title element: {slug}")
    title_node[0].text = title + " | TTN Finance"
    canonical = BASE + slug + ".html"
    set_link(doc, "canonical", canonical)
    for key, value, attr in [
        ("description", description, "name"),
        ("og:type", "article", "property"),
        ("og:title", title, "property"),
        ("og:description", description, "property"),
        ("og:url", canonical, "property"),
        ("og:site_name", "TTN Finance", "property"),
        ("twitter:card", "summary_large_image", "name"),
        ("twitter:title", title, "name"),
        ("twitter:description", description, "name"),
        ("robots", "index,follow,max-image-preview:large", "name"),
        ("article:published_time", date, "property"),
    ]:
        set_meta(doc, key, value, attr)

    jsonld_nodes = doc.xpath('//script[@type="application/ld+json"]')
    if not jsonld_nodes:
        raise ValueError(f"Missing Article JSON-LD template: {slug}")
    structured = json.loads(jsonld_nodes[0].text or "{}")
    structured.update({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": date,
        "dateModified": date,
        "inLanguage": "en-US",
        "articleSection": section,
        "wordCount": word_count,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "image": {
            "@type": "ImageObject",
            "url": BASE + cover_path,
            "width": width,
            "height": height,
            "caption": seo.get("imageAlt") or title,
        },
        "citation": [source["url"] for source in sources],
    })
    jsonld_nodes[0].text = json.dumps(structured, ensure_ascii=False, separators=(",", ":"))
    return html.tostring(doc, encoding="unicode", method="html", doctype="<!DOCTYPE html>"), word_count, related

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: prepare_nov16_publication.py SOURCE.zip OUTPUT.zip")
    source_zip = Path(sys.argv[1])
    output_zip = Path(sys.argv[2])
    if source_zip.name != ARCHIVE_NAME:
        raise SystemExit(f"Refusing unexpected source archive: {source_zip.name}")

    source_dir = ROOT / "scripts/publication-source/nov16"
    template = (ROOT / "bitcoin-four-month-low-crypto-liquidations-november-2026.html").read_text(encoding="utf-8")
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source_zip) as src:
        by_basename = {}
        for name in src.namelist():
            if name.endswith("/"):
                continue
            base = Path(name).name
            if base in by_basename:
                raise ValueError(f"Duplicate source filename in archive: {base}")
            by_basename[base] = name
        manifest_name = by_basename.get("publication-manifest.json")
        if not manifest_name:
            raise ValueError("Source ZIP has no publication-manifest.json")
        raw_manifest = json.loads(src.read(manifest_name))
        if not isinstance(raw_manifest, dict) or not isinstance(raw_manifest.get("articles"), list):
            raise ValueError("Expected Gemini manifest object with an articles array")
        items = raw_manifest["articles"]
        if len(items) != 3:
            raise ValueError(f"Expected exactly three articles, got {len(items)}")

        normalized = []
        pages = []
        assets = {}
        for item in items:
            slug = item["slug"]
            if slug not in DEKS or slug not in SOURCES:
                raise ValueError(f"Unexpected article in latest Nov. 16 package: {slug}")
            if item["date"] != "2026-11-16":
                raise ValueError(f"Unexpected publication date for {slug}: {item['date']}")
            md_path = source_dir / f"{slug}.md"
            fragment_path = source_dir / f"{slug}-fragment.html"
            if not md_path.is_file() or not fragment_path.is_file():
                raise ValueError(f"Reviewed source files missing for {slug}")
            markdown = md_path.read_text(encoding="utf-8")
            if len(markdown.split()) < 700:
                raise ValueError(f"Reviewed Markdown unexpectedly short: {slug}")
            fragment_text = fragment_path.read_text(encoding="utf-8")
            seo_name = by_basename.get(item["seo"])
            cover_name = by_basename.get(item["cover"])
            if not seo_name or not cover_name:
                raise ValueError(f"SEO or cover file missing in source ZIP: {slug}")
            seo = json.loads(src.read(seo_name))
            cover_bytes = src.read(cover_name)
            image = Image.open(io.BytesIO(cover_bytes))
            image.load()
            if image.format != "WEBP" or image.width < 1200 or abs(image.width / image.height - 16 / 9) > 0.02:
                raise ValueError(f"Cover is not a usable 16:9 WebP: {slug} ({image.size})")
            description = seo.get("description", "")
            if not 70 <= len(description) <= 160:
                raise ValueError(f"SEO description length invalid for {slug}: {len(description)}")
            sources = SOURCES[slug]
            for source in sources:
                if not source["url"].startswith("https://"):
                    raise ValueError(f"Invalid source URL for {slug}")

            cover_path = f"assets/editorial/{slug}-cover.webp"
            small_path = f"assets/responsive/{slug}-cover-480.webp"
            medium_path = f"assets/responsive/{slug}-cover-960.webp"
            page, word_count, related = build_page(
                template, slug, item, fragment_text, seo,
                cover_path, small_path, medium_path,
                image.width, image.height, sources,
            )
            normalized.append({
                "slug": slug,
                "title": item["title"],
                "dek": DEKS[slug],
                "section": item["category"],
                "format": "news",
                "date": item["date"],
                "sources": sources,
                "cover": cover_path,
                "related": related,
                "tickers": [],
            })
            pages.append((slug + ".html", page.encode("utf-8")))
            assets[cover_path] = cover_bytes
            for size, path in [(480, small_path), (960, medium_path)]:
                resized = image.copy()
                resized.thumbnail((size, size * 9 // 16), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                resized.save(buffer, format="WEBP", quality=84, method=6)
                assets[path] = buffer.getvalue()

        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as out:
            out.writestr("publication-manifest.json", json.dumps(normalized, ensure_ascii=False, indent=2) + "\n")
            for name, data in pages:
                out.writestr(name, data)
            for name, data in assets.items():
                out.writestr(name, data)
    print(f"Prepared importer-ready package: {output_zip}")
    print("Articles:", ", ".join(item["slug"] for item in normalized))

if __name__ == "__main__":
    main()
