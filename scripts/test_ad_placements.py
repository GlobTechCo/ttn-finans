#!/usr/bin/env python3
"""Verify disabled placements preserve content and cannot enable ad requests."""
from pathlib import Path
import subprocess, tempfile
from lxml import html
import ad_placements as ads

ROOT = Path(__file__).resolve().parents[1]
assert ads.ADVERTISING_ENABLED is False
assert not ads.PUBLISHER_ID
assert all(not p['enabled'] and not p['slot_id'] for p in ads.PLACEMENTS.values())
count = 0
for page in ROOT.glob('*.html'):
    document = html.fromstring(page.read_text())
    for template in document.xpath('//template[@data-ttn-ad-placement]'):
        assert template.get('data-ttn-ad-enabled') == 'false', page.name
        assert not template.xpath('.//script|.//iframe|.//*[@src or @href]'), page.name
        count += 1
    assert not document.xpath('//script[contains(@src,"adsbygoogle") or contains(@src,"fundingchoices")]'), page.name
    assert not document.xpath('//ins[contains(@class,"adsbygoogle")]'), page.name
    body = document.xpath('//section[@class="editorial-body"]')
    if body:
        assert len(document.xpath('//template[@data-ttn-ad-placement="article-content-end"]')) == 1, page.name
    if page.name in {'about.html','privacy.html','cookies.html','contact.html','404.html'}:
        assert not document.xpath('//template[@data-ttn-ad-placement]'), page.name

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    for page in ROOT.glob('*.html'):
        (root/page.name).write_bytes(page.read_bytes())
    before = {p.name:p.read_bytes() for p in root.glob('*.html')}
    ads.refresh_ad_placements(root)
    assert before == {p.name:p.read_bytes() for p in root.glob('*.html')}, 'Repeated generation changes files'
    ads.ADVERTISING_ENABLED = True
    try:
        ads.refresh_ad_placements(root)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Incomplete advertising setup was activated')
    finally:
        ads.ADVERTISING_ENABLED = False
print(f'PASS: {count} inert placements; no ad SDK/requests; no policy-page ads; idempotent generation and fail-closed activation.')
