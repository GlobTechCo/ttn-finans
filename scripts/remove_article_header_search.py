#!/usr/bin/env python3
"""Remove the homepage-only news search from published article headers."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "articles.js"
SEARCH_BOX = re.compile(
    r'<div\\s+class=(["\\'])search-box\\1[^>]*>.*?</div>',
    flags=re.IGNORECASE | re.DOTALL,
)
HEADER = re.compile(r'<header\\b[^>]*>.*?</header>', flags=re.IGNORECASE | re.DOTALL)


def clean_article(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    removed = 0

    def clean_header(match):
        nonlocal removed
        cleaned, count = SEARCH_BOX.subn("", match.group(0))
        removed += count
        return cleaned

    updated = HEADER.sub(clean_header, source)
    if re.search(r'<header\\b[^>]*>.*?class=(["\\'])search-box\\1', updated, re.I | re.S):
        raise RuntimeError(f"Search box remains in article header: {path.name}")
    if updated != source:
        path.write_text(updated, encoding="utf-8")
    return removed > 0


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8").split("=", 1)[1].strip().removesuffix(";"))
    changed = []
    for article in catalog:
        path = ROOT / (article["id"] + ".html")
        if not path.is_file():
            raise FileNotFoundError(path)
        if clean_article(path):
            changed.append(path.name)
    print(f"Checked {len(catalog)} articles; removed homepage-only search from {len(changed)} article headers.")
    if changed:
        print("\\n".join(changed))


if __name__ == "__main__":
    main()
