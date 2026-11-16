#!/usr/bin/env python3
"""Sync the reviewed South Korea bill article from its canonical HTML page."""
from pathlib import Path
import json
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SLUG = "south-korea-crypto-travel-rule-bill-2026"


def sync():
    catalog = ROOT / "articles.js"
    source = catalog.read_text(encoding="utf-8")
    prefix, payload = source.split("=", 1)
    articles = json.loads(payload.strip().removesuffix(";"))
    article = next((item for item in articles if item.get("id") == SLUG), None)
    if article is None:
        raise SystemExit(f"Missing article record: {SLUG}")

    doc = html.fromstring((ROOT / f"{SLUG}.html").read_text(encoding="utf-8"))
    h1 = doc.xpath('//main[contains(@class,"static-page")]/h1')
    dek = doc.xpath('//p[contains(concat(" ",normalize-space(@class)," ")," article-dek ")]')
    body = doc.xpath('//section[contains(concat(" ",normalize-space(@class)," ")," editorial-body ")]')
    sources = doc.xpath('//aside[contains(concat(" ",normalize-space(@class)," ")," editorial-sources ")]')
    schema_nodes = doc.xpath('//script[@type="application/ld+json"]/text()')
    if any(len(nodes) != 1 for nodes in (h1, dek, body, sources, schema_nodes)):
        raise SystemExit("Expected one headline, deck, body, source block and Article schema")
    schema = json.loads(schema_nodes[0])
    count = len(" ".join(body[0].xpath(".//p//text()")).split())
    if not 700 <= count <= 900 or schema.get("wordCount") != count:
        raise SystemExit(f"Invalid body/schema word count: body={count}, schema={schema.get('wordCount')}")

    blocks = []
    for child in body[0]:
        if child.tag == "aside" and "editorial-sources" in (child.get("class") or "").split():
            continue
        blocks.append(html.tostring(child, encoding="unicode", method="html"))
    article["title"] = h1[0].text_content().strip()
    article["dek"] = dek[0].text_content().strip()
    article["body"] = blocks
    article["sources"] = [
        {"label": a.text_content().strip(), "url": a.get("href")}
        for a in sources[0].xpath(".//a[@href]")
    ]
    article["dateModified"] = schema.get("dateModified", article.get("date"))
    catalog.write_text(
        prefix.rstrip() + " = " + json.dumps(articles, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"PASS: {SLUG}: {count} words and {len(article['sources'])} source links synced to articles.js.")


if __name__ == "__main__":
    sync()
