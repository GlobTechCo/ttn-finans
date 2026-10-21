#!/usr/bin/env python3
"""Check the owner's PDF audit targets: news 600+, explainers 700+ words.

Count only paragraph text inside editorial-body, excluding headings, decks,
sources, related reading and other site furniture. These are TTN editorial
targets, not a Google word-count requirement. No network requests or writes.
"""
import argparse
import csv
from html.parser import HTMLParser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


class ArticleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.in_paragraph = False
        self.paragraphs = []
        self.current = []
        self.in_schema = False
        self.schema = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section' and 'editorial-body' in attrs.get('class', '').split():
            self.in_body = True
        if self.in_body and tag == 'p':
            self.in_paragraph = True
            self.current = []
        if tag == 'br' and self.in_paragraph:
            self.current.append(' ')
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_schema = True

    def handle_endtag(self, tag):
        if tag == 'p' and self.in_paragraph:
            self.paragraphs.append(''.join(self.current))
            self.in_paragraph = False
        if tag == 'section':
            self.in_body = False
        if tag == 'script':
            self.in_schema = False

    def handle_data(self, data):
        if self.in_paragraph:
            self.current.append(data)
        if self.in_schema:
            self.schema.append(data)


def audit(root=ROOT):
    articles = json.loads((root / 'articles.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    rows = []
    for article in articles:
        parser = ArticleText()
        parser.feed((root / (article['id'] + '.html')).read_text())
        schema = json.loads(''.join(parser.schema))
        kind = schema['@type']
        if kind not in {'Article', 'NewsArticle'}:
            raise ValueError(f"Unrecognized article type: {article['id']}: {kind}")
        minimum = 600 if kind == 'NewsArticle' else 700
        words = sum(len(p.split()) for p in parser.paragraphs)
        text = '\n\n'.join(parser.paragraphs)
        rows.append(dict(id=article['id'], title=article['title'], date=article['date'],
                         type=kind, words=words, characters=len(text), minimum=minimum,
                         status='PASS' if words >= minimum else 'FAIL'))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text')
    args = parser.parse_args()
    rows = audit()
    failures = [r for r in rows if r['status'] == 'FAIL']
    if args.format == 'json':
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif args.format == 'csv':
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    else:
        for row in failures:
            print(f"FAIL: {row['id']}: {row['words']} < {row['minimum']} paragraph words")
        print(f"{'FAIL' if failures else 'PASS'}: {len(rows)} articles; {len(failures)} below the TTN editorial target (news 600, explainers 700).")
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
