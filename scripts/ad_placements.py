#!/usr/bin/env python3
"""Maintain inert advertising locations. No ad scripts or live ad requests.

Activation is a separate integration: publisher/slot IDs, certified consent where
applicable, labels, sizing and an ad loader must be reviewed before going live.
"""
from pathlib import Path
import re
from lxml import html

ADVERTISING_ENABLED = False
PUBLISHER_ID = ''
PLACEMENTS = {
    'home-editorial-end': {'enabled': False, 'format': 'horizontal', 'slot_id': ''},
    'home-content-end': {'enabled': False, 'format': 'horizontal', 'slot_id': ''},
    'archive-content-end': {'enabled': False, 'format': 'horizontal', 'slot_id': ''},
    'article-inline': {'enabled': False, 'format': 'responsive', 'slot_id': ''},
    'article-content-end': {'enabled': False, 'format': 'responsive', 'slot_id': ''},
}
MARKER = re.compile(r'<!-- ttn-ad:[a-z-]+:start -->.*?<!-- ttn-ad:[a-z-]+:end -->\n?', re.S)

def placeholder(name):
    config = PLACEMENTS[name]
    return (f'<!-- ttn-ad:{name}:start -->\n'
            f'<template data-ttn-ad-placement="{name}" data-ttn-ad-enabled="false" '
            f'data-ttn-ad-format="{config["format"]}"><aside class="ttn-ad-slot" '
            'aria-label="Advertisement"><div class="ttn-ad-content"></div></aside></template>\n'
            f'<!-- ttn-ad:{name}:end -->\n')

def refresh_ad_placements(root=None):
    if ADVERTISING_ENABLED or any(p['enabled'] for p in PLACEMENTS.values()):
        raise RuntimeError('Advertising is not integrated: configure IDs, consent and rendering before activation.')
    root = root or Path(__file__).resolve().parents[1]
    count = 0
    for page in root.glob('*.html'):
        original = page.read_text()
        text = MARKER.sub('', original)
        body = re.search(r'(<section class="editorial-body">)(.*?)(</section>)', text, re.S)
        if body:
            content = body[2]
            total = len(html.fragment_fromstring(content, create_parent='div').text_content().split())
            # Longer articles get one midpoint location, with substantial copy on both sides.
            # Native templates have no layout box, focusable controls or resource requests.
            if total >= 600:
                cumulative = 0
                candidates = []
                for block in re.finditer(r'<(?:p|h[23])\b[^>]*>.*?</(?:p|h[23])>', content, re.S):
                    cumulative += len(html.fromstring(block[0]).text_content().split())
                    if block[0].startswith('<p') and cumulative >= 150 and total-cumulative >= 150:
                        candidates.append((abs(cumulative-total/2), block.end()))
                if candidates:
                    at = min(candidates)[1]
                    content = content[:at]+placeholder('article-inline')+content[at:]
                    count += 1
            text = text[:body.start()]+body[1]+content+body[3]+placeholder('article-content-end')+text[body.end():]
            count += 1
        elif page.name == 'index.html':
            # The feed and news rail remain untouched; locations sit between page sections.
            needle = '<div class="home-news-row">'
            assert needle in text
            text = text.replace(needle, placeholder('home-editorial-end')+needle, 1)
            text = text.replace('</main>', placeholder('home-content-end')+'</main>', 1)
            count += 2
        elif page.name in {'analysis.html', 'tech-ai.html', 'crypto.html'}:
            needle = '<!-- editorial-topics:start -->'
            assert needle in text
            text = text.replace(needle, placeholder('archive-content-end')+needle, 1)
            count += 1
        if text != original:
            page.write_text(text)
    print(f'Prepared {count} inert advertising locations; advertising remains disabled.')

if __name__ == '__main__':
    refresh_ad_placements()
