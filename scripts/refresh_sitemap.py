"""Add missing canonical, indexable HTML pages without inventing modification dates."""
from datetime import datetime
from html import escape
from pathlib import Path
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from lxml import html

BASE = 'https://globtechco.github.io/ttn-finans/'
ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
FIELD_ORDER = {'loc': 0, 'lastmod': 1, 'changefreq': 2, 'priority': 3}


def normalize_field_order(text):
    """Honor the sitemap XSD sequence while preserving values and other entries."""
    repaired = 0
    fields = re.compile(r'\s*<(?P<tag>loc|lastmod|changefreq|priority)>[^<]*</(?P=tag)>')
    def reorder(match):
        nonlocal repaired
        body = match.group(1)
        parts = list(fields.finditer(body))
        ordered = sorted(parts, key=lambda part: FIELD_ORDER[part.group('tag')])
        if parts == ordered:
            return match.group()
        assert not fields.sub('', body).strip(), 'Cannot reorder an extended sitemap entry'
        repaired += 1
        return '<url>' + ''.join(part.group() for part in ordered) + body[parts[-1].end():] + '</url>'
    return re.sub(r'<url>(.*?)</url>', reorder, text, flags=re.S), repaired


def refresh_sitemap(root=ROOT):
    root = Path(root)
    path = root / 'sitemap.xml'
    text = path.read_text()
    entries = ET.fromstring(text).findall('s:url', NS)
    existing = [entry.find('s:loc', NS).text for entry in entries]
    assert len(existing) == len(set(existing)), 'Duplicate sitemap URLs'
    catalog = json.loads((root / 'articles.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    dates = {article['id'] + '.html': article['date'] for article in catalog}
    additions = []
    for page in sorted(root.glob('*.html')):
        doc = html.fromstring(page.read_text())
        url = BASE if page.name == 'index.html' else BASE + page.name
        if doc.xpath('//link[@rel="canonical"]/@href') != [url]:
            continue
        if any('noindex' in value.lower() for value in doc.xpath('//meta[@name="robots"]/@content')):
            continue
        if url in existing:
            continue
        modified = doc.xpath('//meta[@property="article:modified_time"]/@content')
        stamp = modified[0] if modified else dates.get(page.name)
        if not stamp:
            stamp = subprocess.check_output(['git', 'log', '-1', '--format=%cI', '--', page.name], cwd=root, text=True).strip()
        assert stamp, (page.name, 'No reliable modification date')
        datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        additions.append('<url><loc>' + escape(url) + '</loc><lastmod>' + escape(stamp) + '</lastmod></url>')
    if additions:
        assert text.count('</urlset>') == 1
        text = text.replace('</urlset>', '\n'.join(additions) + '\n</urlset>')
    text, repaired = normalize_field_order(text)
    if text != path.read_text():
        path.write_text(text)
    print(f'Sitemap: added {len(additions)} canonical pages; corrected {repaired} field orders; {len(existing) + len(additions)} total URLs.')
    return len(additions)


if __name__ == '__main__':
    refresh_sitemap()
