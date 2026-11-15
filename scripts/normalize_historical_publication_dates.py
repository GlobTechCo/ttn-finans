#!/usr/bin/env python3
"""Remove unsupported clock times from historical TTN publication dates.

A publication date without a recorded timezone/source timestamp is a date,
not a verified instant. Keep dateModified untouched.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "articles.js"
FORCE_DATE_ONLY = {
    "bitcoin-four-month-low-crypto-liquidations-november-2026",
    "eba-explores-alternatives-eu-deposit-insurance-cross-border-banking-november-2026",
    "samsung-ai-data-center-infrastructure-expansion-november-2026",
}


def update_page(slug, old, new):
    path = ROOT / (slug + ".html")
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    before = text

    # Article JSON-LD: change publication time only, never dateModified.
    text, schema_count = re.subn(
        r'("datePublished"\s*:\s*")' + re.escape(old) + r'(")',
        lambda m: m.group(1) + new + m.group(2),
        text,
    )
    if schema_count != 1:
        raise ValueError(f"{slug}: expected one datePublished value, found {schema_count}")

    # Semantic publication <time>; preserve its human-readable date label.
    text, time_count = re.subn(
        r'(<time\b[^>]*\bdatetime=["\'])' + re.escape(old) + r'(["\'])',
        lambda m: m.group(1) + new + m.group(2),
        text,
        count=1,
        flags=re.I,
    )
    if time_count != 1:
        raise ValueError(f"{slug}: expected one publication <time datetime>, found {time_count}")

    # Open Graph article:published_time may use either attribute order.
    def normalize_meta(match):
        tag = match.group(0)
        if not re.search(r'property=["\']article:published_time["\']', tag, re.I):
            return tag
        return re.sub(
            r'(content=["\'])' + re.escape(old) + r'(["\'])',
            lambda m: m.group(1) + new + m.group(2),
            tag,
            count=1,
            flags=re.I,
        )

    text = re.sub(r'<meta\b[^>]*>', normalize_meta, text, flags=re.I)
    if text == before:
        raise ValueError(f"{slug}: no page changes were made")
    path.write_text(text, encoding="utf-8")


def main():
    source = CATALOG.read_text(encoding="utf-8")
    prefix, payload = source.split("=", 1)
    articles = json.loads(payload.strip().removesuffix(";"))
    changed = []
    for article in articles:
        slug = article["id"]
        value = article.get("date", "")
        date_only = None
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value):
            date_only = value[:10]
        elif slug in FORCE_DATE_ONLY and re.fullmatch(r"\d{4}-\d{2}-\d{2}T[^ ]+", value):
            date_only = value[:10]
        if date_only and date_only != value:
            update_page(slug, value, date_only)
            article["date"] = date_only
            changed.append(slug)

    if len(changed) != 85:
        raise ValueError(f"Expected 85 unsupported timestamps to normalize; found {len(changed)}")
    CATALOG.write_text(prefix + " = " + json.dumps(articles, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"PASS: normalized {len(changed)} publication dates to date-only; dateModified values preserved.")
    for slug in changed:
        print(slug)


if __name__ == "__main__":
    main()
