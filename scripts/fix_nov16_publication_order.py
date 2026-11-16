#!/usr/bin/env python3
"""Correct Nov. 16 article chronology using the actual publication-fix run time."""
from datetime import datetime, timezone
from pathlib import Path
import json
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SLUGS = [
    "wall-street-slides-treasury-yields-above-5-1-nvidia-earnings-november-16-2026",
    "bitcoin-64500-crypto-stocks-fall-nasdaq-november-16-2026",
    "nvidia-first-earnings-without-jensen-huang-trump-possible-return-november-16-2026",
]
stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
catalog_path = ROOT / "articles.js"
raw = catalog_path.read_text(encoding="utf-8")
prefix, payload = raw.split("=", 1)
catalog = json.loads(payload.strip().removesuffix(";"))
found = set()
for item in catalog:
    if item.get("id") in SLUGS:
        item["date"] = stamp
        found.add(item["id"])
if found != set(SLUGS):
    raise SystemExit("Expected exactly the three Nov. 16 articles in articles.js; found: " + repr(sorted(found)))
catalog_path.write_text(prefix + "= " + json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

for slug in SLUGS:
    path = ROOT / (slug + ".html")
    if not path.is_file():
        raise SystemExit("Missing article page: " + str(path))
    doc = html.parse(str(path))
    for node in doc.xpath('//meta[@property="article:published_time"]'):
        node.set("content", stamp)
    for node in doc.xpath('//script[@type="application/ld+json"]'):
        try:
            data = json.loads(node.text or "{}")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Article":
            data["datePublished"] = stamp
            data["dateModified"] = stamp
            node.text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    for node in doc.xpath("//time[@datetime]"):
        node.set("datetime", stamp)
    path.write_text(html.tostring(doc, encoding="unicode", method="html", doctype="<!DOCTYPE html>"), encoding="utf-8")
print("Applied actual UTC publication-fix timestamp", stamp, "to", len(SLUGS), "articles.")
