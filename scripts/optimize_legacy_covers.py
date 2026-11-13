#!/usr/bin/env python3
"""Create loss-optimized WebP delivery copies for three oversized legacy covers.

Original approved PNG files are immutable and remain in the repository.
This script updates only the active article/catalog references to same-size WebP
derivatives, then refresh_social_cards.py rebuilds immutable social-card copies.
"""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "meta-muse-ten-million-us-downloads-october-20-2026": "assets/editorial/meta-muse-ten-million-us-downloads-october-20-2026-cover-v1.png",
    "nacha-same-day-ach-growth-third-quarter-2026": "assets/editorial/nacha-same-day-ach-growth-third-quarter-2026-cover-v1.png",
    "reliable-robotics-financing-autonomous-flight-october-20-2026": "assets/editorial/reliable-robotics-financing-autonomous-flight-october-20-2026-cover-v2.png",
}


def main():
    catalog_path = ROOT / "articles.js"
    prefix, raw = catalog_path.read_text().split("const TTN_ARTICLES = ", 1)
    articles = json.loads(raw.strip().removesuffix(";"))
    by_id = {article["id"]: article for article in articles}
    replacements = {}

    for article_id, source_rel in TARGETS.items():
        if article_id not in by_id:
            raise SystemExit(f"Missing article catalog entry: {article_id}")
        source = ROOT / source_rel
        if not source.is_file():
            raise SystemExit(f"Missing approved original cover: {source_rel}")
        target_rel = str(Path(source_rel).with_suffix(".webp")).replace("\\", "/")
        target = ROOT / target_rel
        article = by_id[article_id]
        current_image = article.get("image")
        if current_image not in (source_rel, target_rel):
            raise SystemExit(f"Unexpected catalog image for {article_id}: {current_image}")
        with Image.open(source) as original:
            original.load()
            original_size = original.size
            image = original.copy() if current_image == source_rel else None
        if image is not None:
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target, "WEBP", quality=90, method=6)
        if not target.is_file():
            raise SystemExit(f"Missing optimized WebP derivative: {target_rel}")
        with Image.open(target) as optimized:
            optimized.verify()
        with Image.open(target) as optimized:
            if optimized.size != original_size or optimized.format != "WEBP":
                raise SystemExit(f"Invalid WebP derivative: {target_rel}")
        original_bytes, optimized_bytes = source.stat().st_size, target.stat().st_size
        if optimized_bytes >= original_bytes or optimized_bytes > 1_000_000:
            raise SystemExit(f"Insufficient optimization for {article_id}: {original_bytes} -> {optimized_bytes}")
        article["image"] = target_rel
        article["imageSrcset"] = f"{target_rel} {original_size[0]}w"
        replacements[source_rel] = target_rel
        state = "already optimized" if current_image == target_rel else "optimized"
        print(f"{article_id}: {state}; {original_bytes:,} -> {optimized_bytes:,} bytes ({optimized_bytes / original_bytes:.1%}); dimensions unchanged at {original_size[0]}x{original_size[1]}")

    catalog_path.write_text(prefix + "const TTN_ARTICLES = " + json.dumps(articles, ensure_ascii=False, separators=(",", ":")) + ";\n")

    cards_path = ROOT / "article-cards.js"
    cards_text = cards_path.read_text()
    for old, new in replacements.items():
        cards_text = cards_text.replace(old, new)
    cards_path.write_text(cards_text)
    card_version = hashlib.sha256(cards_path.read_bytes()).hexdigest()[:12]
    for filename in ("index.html", "analysis.html", "tech-ai.html", "crypto.html"):
        page = ROOT / filename
        page_text = page.read_text()
        page_text, count = re.subn(
            r'article-cards[.]js(?:[?][^">]*)?',
            "article-cards.js?v=" + card_version,
            page_text,
        )
        if count != 1:
            raise SystemExit(f"Expected one article-cards.js reference in {filename}, found {count}")
        page.write_text(page_text)

    for article_id, old in TARGETS.items():
        page = ROOT / f"{article_id}.html"
        text = page.read_text()
        new = replacements[old]
        if old in text:
            text = text.replace(old, new)
        elif new not in text:
            raise SystemExit(f"Expected approved image reference missing from {page.name}")
        page.write_text(text)

    print("Original approved PNG covers preserved. Article, JSON-LD, srcset and card-catalog references now use same-dimension WebP derivatives.")


if __name__ == "__main__":
    main()
