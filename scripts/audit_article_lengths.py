#!/usr/bin/env python3
"""Enforce TTN's 700-900 paragraph-word range for new and substantially updated articles.

Parse HTML structurally with lxml rather than a streaming HTMLParser. The
streaming parser previously lost article text when imported pages used the
shared template's nested main/section layout.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from lxml import html
from editorial_length_reviews import REVIEWS

ROOT = Path(__file__).resolve().parents[1]
FURNITURE_IDS = {
    'jensen-huang-signals-return-to-nvidia-leadership-crisis-november-17-2026',
    'nsa-classified-communications-network-outage-us-infrastructure-reliability-november-17-2026',
    'software-outage-fears-wall-street-sell-off-technology-shares-slide-november-17-2026',
}
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

def audit(root=ROOT):
    articles = json.loads((root / 'articles.js').read_text(encoding='utf-8').split('=', 1)[1].strip().removesuffix(';'))
    rows = []
    for article in articles:
        article_id = article['id']
        doc = html.fromstring((root / (article_id + '.html')).read_bytes())
        bodies = doc.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " editorial-body ")]')
        if len(bodies) != 1:
            raise ValueError(f"Expected exactly one editorial-body container: {article_id}; found {len(bodies)}")
        schema_nodes = doc.xpath('//script[translate(@type,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="application/ld+json"]')
        schema = None
        for node in schema_nodes:
            try:
                value = json.loads(node.text or '{}')
            except (TypeError, ValueError):
                continue
            candidates = value if isinstance(value, list) else [value]
            schema = next((item for item in candidates if isinstance(item, dict) and item.get('@type') in {'Article', 'NewsArticle'}), None)
            if schema:
                break
        if not schema:
            raise ValueError(f"Missing valid Article/NewsArticle JSON-LD: {article_id}")
        kind = schema['@type']
        latest = max(str(schema.get('datePublished', article['date'])),
                     str(schema.get('dateModified', article.get('dateModified', article['date']))))
        minimum = 700 if kind != 'NewsArticle' or latest[:10] >= '2026-10-30' else 600
        paragraphs = []
        for paragraph in bodies[0].xpath('.//p'):
            # Match the importer's editorial-word rules and exclude site furniture.
            if paragraph.xpath('ancestor-or-self::*[contains(concat(" ",normalize-space(@class)," ")," editorial-sources ") or contains(concat(" ",normalize-space(@class)," ")," article-sources ")]'):
                continue
            text = ' '.join(' '.join(paragraph.itertext()).split())
            if text.lower() == 'sources' or text.lower().startswith('related ttn coverage:'):
                continue
            if 'Related context:' in text:
                text = text.split('Related context:', 1)[0].strip()
            if article_id in FURNITURE_IDS and text and text.lower() != 'sources' and not text.lower().startswith('related ttn coverage:'):
                paragraphs.append(text)
            elif article_id not in FURNITURE_IDS and text:
                paragraphs.append(text)
        text = '\n\n'.join(paragraphs)
        words = sum(len(paragraph.split()) for paragraph in paragraphs)
        review = REVIEWS.get(article_id)
        if review and hashlib.sha256(text.encode()).hexdigest() == review['sha256']:
            minimum = review['words']
        maximum = 900
        rows.append(dict(id=article_id, title=article['title'], date=article['date'],
                         type=kind, words=words, characters=len(text), minimum=minimum,
                         maximum=maximum, status='PASS' if minimum <= words <= maximum else 'FAIL'))
        if minimum > words or words > maximum:
            print(f"ARTICLE_TEXT_FOR_REVIEW: {article_id} ({words} paragraph words)")
            print(text)
            print("END_ARTICLE_TEXT_FOR_REVIEW")
    return rows

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text')
    args = parser.parse_args()
    rows = audit()
    failures = [row for row in rows if row['status'] == 'FAIL']
    if args.format == 'json':
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif args.format == 'csv':
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    else:
        for row in failures:
            reason = f"{row['words']} < {row['minimum']}" if row['words'] < row['minimum'] else f"{row['words']} > {row['maximum']}"
            print(f"FAIL: {row['id']}: {reason} paragraph words")
        print(f"{'FAIL' if failures else 'PASS'}: {len(rows)} articles; {len(failures)} outside the approved range (700-900 for new/substantially updated articles; unchanged earlier news retains its historical 600-word minimum, with a 900-word maximum).")
    return bool(failures)

if __name__ == '__main__':
    raise SystemExit(main())
