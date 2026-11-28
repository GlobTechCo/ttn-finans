"""Add missing canonical, indexable HTML pages without inventing modification dates."""
from datetime import datetime, timezone
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



def normalize_content(value):
    """Ignore formatting-only changes when deciding whether page content changed."""
    return re.sub(r'\s+', ' ', value).strip()


def git_last_significant_change(root, filename):
    """Return the latest commit date that changed the file beyond whitespace."""
    commits = subprocess.check_output(
        ['git', 'log', '--format=%H', '--', filename], cwd=root, text=True
    ).splitlines()
    for commit in commits:
        parents = subprocess.check_output(
            ['git', 'rev-list', '--parents', '-n', '1', commit], cwd=root, text=True
        ).split()
        current = subprocess.check_output(
            ['git', 'show', commit + ':' + filename], cwd=root, text=True
        )
        previous = ''
        if len(parents) > 1:
            try:
                previous = subprocess.check_output(
                    ['git', 'show', parents[1] + ':' + filename], cwd=root, text=True,
                    stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                previous = ''
        if normalize_content(current) != normalize_content(previous):
            return subprocess.check_output(
                ['git', 'show', '-s', '--format=%cI', commit], cwd=root, text=True
            ).strip()
    return ''


def reliable_lastmod(root, page, existing=''):
    """Use article metadata or the last substantive HTML change, never mass build time."""
    source = page.read_text(encoding='utf-8')
    doc = html.fromstring(source)
    modified = doc.xpath('//meta[@property="article:modified_time"]/@content')
    if modified:
        assert len(modified) == 1, (page.name, 'duplicate article:modified_time')
        stamp = modified[0]
    else:
        stamp = ''
        for raw in doc.xpath('//script[@type="application/ld+json"]/text()'):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get('dateModified'):
                stamp = data['dateModified']
                break
        if not stamp:
            head = subprocess.run(
                ['git', 'show', 'HEAD:' + page.name], cwd=root, text=True,
                capture_output=True
            )
            if head.returncode == 0 and normalize_content(head.stdout) != normalize_content(source):
                stamp = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
            else:
                if existing in {'2026-11-26T15:43:21Z', '2026-11-27T11:28:21Z', '2026-11-26T16:17:19Z'}:
                    stamp = git_last_significant_change(root, page.name) or existing
                else:
                    stamp = existing
    if stamp:
        parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        assert parsed.tzinfo is not None, (page.name, 'lastmod must include a timezone')
        return parsed.isoformat(timespec='seconds').replace('+00:00', 'Z')
    return existing


def refresh_sitemap(root=ROOT):
    root = Path(root)
    path = root / 'sitemap.xml'
    text = path.read_text()
    entries = ET.fromstring(text).findall('s:url', NS)
    existing = [entry.find('s:loc', NS).text for entry in entries]
    assert len(existing) == len(set(existing)), 'Duplicate sitemap URLs'

    additions = []
    updates = {}
    for page in sorted(root.glob('*.html')):
        doc = html.fromstring(page.read_text(encoding='utf-8'))
        url = BASE if page.name == 'index.html' else BASE + page.name
        if doc.xpath('//link[@rel="canonical"]/@href') != [url]:
            continue
        if any('noindex' in value.lower() for value in doc.xpath('//meta[@name="robots"]/@content')):
            continue
        old_stamp = ''
        if url in existing:
            old_entry = next(entry for entry in entries if entry.find('s:loc', NS).text == url)
            old_node = old_entry.find('s:lastmod', NS)
            old_stamp = old_node.text if old_node is not None else ''
        stamp = reliable_lastmod(root, page, old_stamp)
        if not stamp:
            assert url in existing, (page.name, 'No reliable modification date for new sitemap URL')
            continue
        if url in existing:
            if stamp != old_stamp:
                updates[url] = stamp
        else:
            additions.append('<url><loc>' + escape(url) + '</loc><lastmod>' + escape(stamp) + '</lastmod></url>')
    if additions:
        assert text.count('</urlset>') == 1
        text = text.replace('</urlset>', '\n'.join(additions) + '\n</urlset>')
    # Reconcile every existing entry against its page's real modification metadata.
    # This removes false mass timestamps left by whitespace-only archive rewrites.
    for url, stamp in updates.items():
        pattern = r'(<url>\s*<loc>' + re.escape(url) + r'</loc>\s*<lastmod>)([^<]+)(</lastmod>)'
        updated, matches = re.subn(pattern, lambda m: m.group(1) + stamp + m.group(3), text, count=1)
        assert matches == 1, ('Cannot reconcile sitemap lastmod', url)
        text = updated
    text, repaired = normalize_field_order(text)
    if text != path.read_text():
        path.write_text(text)
    # A plain-text companion provides an independent supported sitemap format.
    locations = [node.text for node in ET.fromstring(text).findall('s:url/s:loc', NS)]
    companion = root / 'sitemap-pages.txt'
    listing = '\n'.join(locations) + '\n'
    if not companion.exists() or companion.read_text() != listing:
        companion.write_text(listing, encoding='utf-8')
    print(f'Sitemap: added {len(additions)} canonical pages; corrected {len(updates)} modification dates; corrected {repaired} field orders; {len(existing) + len(additions)} total URLs.')
    return len(additions)


if __name__ == '__main__':
    refresh_sitemap()
