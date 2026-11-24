#!/usr/bin/env python3
"""Apply the audited 700–900-word correction to the November 24 Zscaler article package."""
import json
import re
import sys
import zipfile
from pathlib import Path
from lxml import html

SLUG = "crowdstrike-zscaler-43-9-billion-cybersecurity-deal-2026"
PREFIX = "The timing reflects a wider shift in cybersecurity spending."

def norm(node):
    return " ".join(" ".join(node.itertext()).split())

def count_article_words(doc):
    body = doc.xpath("//div[contains(concat(' ',normalize-space(@class),' '),' article-body ')]")
    if not body:
        body = doc.xpath("//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]")
    paragraphs = body[0].xpath(".//p") if body else doc.xpath("//p")
    total = 0
    for p in paragraphs:
        value = norm(p)
        low = value.lower()
        if not value or low == "sources" or low.startswith("related ttn coverage:"):
            continue
        if "Related context:" in value:
            value = value.split("Related context:", 1)[0].strip()
        total += len(value.split())
    return total

def fix(path):
    path = Path(path)
    with zipfile.ZipFile(path, "r") as src:
        names = src.namelist()
        if SLUG + ".html" not in names:
            print("No November 24 Zscaler article in", path, "- unchanged")
            return
        files = {name: src.read(name) for name in names}
    doc = html.fromstring(files[SLUG + ".html"])
    matches = [p for p in doc.xpath("//p") if norm(p).startswith(PREFIX)]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one redundant Zscaler paragraph; found {len(matches)}")
    matches[0].getparent().remove(matches[0])
    words = count_article_words(doc)
    if not 700 <= words <= 900:
        raise SystemExit(f"Zscaler article remains outside 700–900 words after correction: {words}")
    for node in doc.xpath("//script[@type='application/ld+json']"):
        try:
            data = json.loads(node.text or "{}")
        except (TypeError, ValueError):
            continue
        items = data if isinstance(data, list) else [data]
        changed = False
        for item in items:
            if isinstance(item, dict) and item.get("@type") in ("Article", "NewsArticle"):
                item["wordCount"] = words
                changed = True
        if changed:
            node.text = json.dumps(data, ensure_ascii=False)
    for meta in doc.xpath("//meta[@name='wordCount' or @name='wordcount' or @property='article:word_count']"):
        meta.set("content", str(words))
    files[SLUG + ".html"] = html.tostring(doc, encoding="utf-8", method="html", doctype="<!DOCTYPE html>")
    temp = path.with_suffix(".corrected.zip")
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in files.items():
            out.writestr(name, data)
    temp.replace(path)
    print(f"Corrected {SLUG}: removed one redundant paragraph; {words} article words in {path}")

if __name__ == "__main__":
    for item in sys.argv[1:]:
        fix(item)
