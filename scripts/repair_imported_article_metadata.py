#!/usr/bin/env python3
"""Repair source citations and inherited template image metadata on the three
articles imported from the 2026-11-15 approved package.
"""
from pathlib import Path
from html import escape, unescape
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://globtechco.github.io/ttn-finans/"
CATALOG = ROOT / "articles.js"

SOURCES = {
    "bitcoin-four-month-low-crypto-liquidations-november-2026": [
        {"label": "Business Standard (Bloomberg), Bitcoin tumbles to four-month low as leveraged bets face mass liquidations",
         "url": "https://www.business-standard.com/markets/cryptocurrency/bitcoin-tumbles-to-four-month-low-as-leveraged-bets-face-mass-liquidations-126111500058_1.html"}
    ],
    "eba-explores-alternatives-eu-deposit-insurance-cross-border-banking-november-2026": [
        {"label": "Financial Times, EU banking watchdog veers away from single deposit insurance scheme",
         "url": "https://www.ft.com/content/016ce22d-1e09-4f1d-a7e6-9acf183e757f"},
        {"label": "European Commission, European deposit insurance scheme",
         "url": "https://finance.ec.europa.eu/banking/banking-union/european-deposit-insurance-scheme_en"},
        {"label": "EUR-Lex, Directive 2014/49/EU on deposit guarantee schemes",
         "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0049"}
    ],
    "samsung-ai-data-center-infrastructure-expansion-november-2026": [
        {"label": "Financial Times, Samsung conquered AI chips. Now it wants to build data centres",
         "url": "https://www.ft.com/content/ee5b23b3-89b3-41f7-9158-56c1586759c2"},
        {"label": "Samsung Global Newsroom, Samsung to invest USD 1 billion in Helix",
         "url": "https://news.samsung.com/global/samsung-to-invest-usd-1-billion-in-ai-infrastructure-company-helix"},
        {"label": "Helix Digital Infrastructure, Samsung commits USD 1 billion to Helix",
         "url": "https://www.helixdi.com/news-insights/samsung-commits-1-billion-to-helix-digital-infrastructure-to-support-global-ai-infrastructure-buildout/"}
    ]
}

IMAGE_ALTS = {
    "bitcoin-four-month-low-crypto-liquidations-november-2026":
        "Bitcoin market sell-off and leveraged crypto liquidations",
    "eba-explores-alternatives-eu-deposit-insurance-cross-border-banking-november-2026":
        "European banking system and deposit protection",
    "samsung-ai-data-center-infrastructure-expansion-november-2026":
        "Samsung AI data center infrastructure and server facilities",
}


def replace_meta_tags(text, alt):
    def update(match):
        tag = match.group(0)
        if re.search(r'property=["\']og:image:alt["\']', tag, re.I) or re.search(r'name=["\']twitter:image:alt["\']', tag, re.I):
            if re.search(r'\bcontent=["\']', tag, re.I):
                return re.sub(r'\bcontent=(["\']).*?\1', lambda m: 'content="' + escape(alt, quote=True) + '"', tag, count=1, flags=re.I)
        return tag
    return re.sub(r'<meta\b[^>]*>', update, text, flags=re.I)


def repair_page(slug, article):
    path = ROOT / (slug + ".html")
    text = path.read_text(encoding="utf-8")
    script_re = re.compile(r'(<script\s+type=["\']application/ld\+json["\']\s*>)([\s\S]*?)(</script>)', re.I)
    matches = list(script_re.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"{slug}: expected one JSON-LD block, found {len(matches)}")
    match = matches[0]
    schema = json.loads(match.group(2))
    alt = IMAGE_ALTS[slug]
    cover = article["image"]
    schema["citation"] = [item["url"] for item in SOURCES[slug]]
    schema["image"] = {
        "@type": "ImageObject",
        "url": BASE + cover,
        "width": 1672,
        "height": 941,
        "caption": alt,
    }
    # Calculate visible editorial-body paragraph words, excluding navigation and source list.
    body_match = re.search(r'<section\b[^>]*class=["\'][^"\']*editorial-body[^"\']*["\'][^>]*>([\s\S]*?)</section>', text, re.I)
    if body_match:
        paragraphs = re.findall(r'<p\b[^>]*>([\s\S]*?)</p>', body_match.group(1), re.I)
        schema["wordCount"] = sum(
            len(unescape(re.sub(r'<[^>]+>', ' ', paragraph)).split())
            for paragraph in paragraphs
        )
    replacement = match.group(1) + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + match.group(3)
    text = text[:match.start()] + replacement + text[match.end():]
    text = replace_meta_tags(text, alt)

    source_rows = "".join(
        '<li><a href="' + escape(item["url"], quote=True) + '" target="_blank" rel="noopener noreferrer">'
        + escape(item["label"]) + '</a></li>'
        for item in SOURCES[slug]
    )
    source_block = (
        '<aside class="editorial-sources" aria-labelledby="editorial-sources-title">'
        '<h2 id="editorial-sources-title">Sources</h2><ul>' + source_rows + '</ul></aside>'
    )
    marker_re = re.compile(r'<!-- ttn-sources:start -->[\s\S]*?<!-- ttn-sources:end -->')
    marked = '<!-- ttn-sources:start -->' + source_block + '<!-- ttn-sources:end -->'
    if marker_re.search(text):
        text = marker_re.sub(marked, text, count=1)
    else:
        end = text.find("</section>", text.find('class="editorial-body"'))
        if end < 0:
            raise ValueError(f"{slug}: editorial body closing tag not found")
        text = text[:end] + marked + text[end:]
    path.write_text(text, encoding="utf-8")


def main():
    source = CATALOG.read_text(encoding="utf-8")
    prefix, payload = source.split("=", 1)
    articles = json.loads(payload.strip().removesuffix(";"))
    by_id = {item["id"]: item for item in articles}
    for slug, sources in SOURCES.items():
        article = by_id.get(slug)
        if article is None:
            raise ValueError("Missing article catalog entry: " + slug)
        article["sources"] = sources
        article["imageAlt"] = IMAGE_ALTS[slug]
        repair_page(slug, article)
    CATALOG.write_text(prefix.rstrip() + " = " + json.dumps(articles, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print("PASS: repaired citations, visible sources, Open Graph image alt and Article image metadata for 3 imported articles.")


if __name__ == "__main__":
    main()
