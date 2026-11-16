#!/usr/bin/env python3
"""Sync the reviewed November 16 article copy from canonical HTML into articles.js.

The static HTML pages are the reviewed source for this one-time correction. This
keeps the large canonical article catalog, generated cards, archives and ticker
controls consistent without manually rewriting the multi-megabyte catalog.
"""
from pathlib import Path
import json
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "articles.js"
SLUGS = {
    "dbs-jpmorgan-tokenised-deposit-cross-border-transfers-2026",
    "south-korea-crypto-travel-rule-bill-2026",
    "stark-future-1-2-billion-valuation-150-million-funding-2026",
}


def visible_words(node):
    return len(" ".join(node.xpath(".//p//text()")).split())


def sync():
    source = CATALOG.read_text(encoding="utf-8")
    prefix, payload = source.split("=", 1)
    articles = json.loads(payload.strip().removesuffix(";"))
    by_id = {item["id"]: item for item in articles}
    missing = SLUGS - set(by_id)
    if missing:
        raise SystemExit("Missing canonical article records: " + ", ".join(sorted(missing)))

    for slug in sorted(SLUGS):
        page = ROOT / (slug + ".html")
        doc = html.fromstring(page.read_text(encoding="utf-8"))
        article = by_id[slug]
        headings = doc.xpath('//main[contains(@class,"static-page")]/h1')
        decks = doc.xpath('//p[contains(concat(" ",normalize-space(@class)," ")," article-dek ")]')
        bodies = doc.xpath('//section[contains(concat(" ",normalize-space(@class)," ")," editorial-body ")]')
        sources = doc.xpath('//aside[contains(concat(" ",normalize-space(@class)," ")," editorial-sources ")]')
        if len(headings) != 1 or len(decks) != 1 or len(bodies) != 1 or len(sources) != 1:
            raise SystemExit(f"{slug}: missing or duplicate headline, deck, body or source block")

        body = bodies[0]
        count = visible_words(body)
        if not 700 <= count <= 900:
            raise SystemExit(f"{slug}: body has {count} words, outside 700-900")
        schema_nodes = doc.xpath('//script[@type="application/ld+json"]/text()')
        if len(schema_nodes) != 1:
            raise SystemExit(f"{slug}: expected exactly one Article schema block")
        schema = json.loads(schema_nodes[0])
        if schema.get("wordCount") != count:
            raise SystemExit(f"{slug}: schema wordCount {schema.get('wordCount')} does not match body count {count}")

        source_links = sources[0].xpath(".//a[@href]")
        source_records = [
            {"label": link.text_content().strip(), "url": link.get("href")}
            for link in source_links
        ]
        if len(source_records) < 2:
            raise SystemExit(f"{slug}: insufficient visible source links")

        blocks = []
        for child in body:
            classes = (child.get("class") or "").split()
            if child.tag == "aside" and "editorial-sources" in classes:
                continue
            blocks.append(html.tostring(child, encoding="unicode", method="html"))

        article["title"] = headings[0].text_content().strip()
        article["dek"] = decks[0].text_content().strip()
        article["body"] = blocks
        article["sources"] = source_records
        hero = doc.xpath('//img[contains(concat(" ",normalize-space(@class)," ")," article-hero-image ")]')
        if hero and hero[0].get("alt"):
            article["imageAlt"] = hero[0].get("alt")
        article["dateModified"] = schema.get("dateModified", article.get("date"))
        if slug == "dbs-jpmorgan-tokenised-deposit-cross-border-transfers-2026":
            # This is a banking/tokenisation story, not a Bitcoin market article.
            article["tickers"] = []

        print(f"PASS: {slug}: {count} words, {len(source_records)} sources, canonical copy synced.")

    CATALOG.write_text(
        prefix.rstrip() + " = " + json.dumps(articles, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print("PASS: updated canonical articles.js records for all three November 16 articles.")


if __name__ == "__main__":
    sync()
