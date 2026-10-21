#!/usr/bin/env python3
"""Audit currently referenced TTN covers, variants and social images.
Reads the canonical JSON catalog; does not replace images or change feeds.
"""
import json
from pathlib import Path
from urllib.parse import urlsplit
from lxml import html
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://globtechco.github.io/ttn-finans/'


def main():
    articles = json.loads((ROOT / 'articles.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    errors, large, checked, external = [], [], set(), set()
    for article in articles:
        tree = html.fromstring((ROOT / (article['id'] + '.html')).read_text())
        refs = [article['image']]
        refs.extend(article[k] for k in ['imageSmall', 'imageMedium'] if article.get(k))
        refs.extend(part.strip().split()[0] for part in article.get('imageSrcset', '').split(',') if part.strip())
        refs.extend(tree.xpath('//meta[@property="og:image" or @name="twitter:image"]/@content'))
        for ref in refs:
            if ref.startswith(BASE):
                ref = ref[len(BASE):]
            if urlsplit(ref).scheme:
                external.add((article['id'], ref))
                continue
            path = ROOT / urlsplit(ref).path
            if path in checked:
                continue
            checked.add(path)
            try:
                with Image.open(path) as image:
                    image.verify()
                if path.stat().st_size > 1_000_000:
                    large.append((ref, path.stat().st_size))
            except (OSError, ValueError) as error:
                errors.append((ref, str(error)))
    print(f"{'FAIL' if errors else 'PASS'}: {len(articles)} articles, {len(checked)} distinct referenced local images decoded; {len(errors)} errors.")
    print(f'External image references: {len(external)}')
    print(f'Performance review: {len(large)} referenced files exceed 1 MB; approved images and immutable social assets preserved.')
    for ref, size in sorted(large):
        print(f'  {ref}: {size:,} bytes')
    for ref, error in errors:
        print(f'FAIL: {ref}: {error}')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
