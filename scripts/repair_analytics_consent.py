#!/usr/bin/env python3
"""Backfill consistent GA4 consent controls on all published TTN pages.

Idempotent: safe for historical articles and for newly imported ZIP articles.
Only injects controls on pages that already load analytics.js.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONSENT_TAG = '<script defer src="consent.js?v=ga4-consent-20261109"></script>'
PREFERENCE_BUTTON = '<button class="ttn-cookie-preferences" type="button" data-cookie-preferences>Cookie preferences</button>'

def repair(root=ROOT):
    changes = []
    for page in sorted(Path(root).glob("*.html")):
        content = page.read_text(encoding="utf-8")
        if not re.search(r'<script\b[^>]*\bsrc=["\'][^"\']*analytics\.js(?:\?[^"\']*)?["\']', content, re.I):
            continue
        original = content
        if not re.search(r'<script\b[^>]*\bsrc=["\'][^"\']*consent\.js(?:\?[^"\']*)?["\']', content, re.I):
            if "</body>" not in content:
                raise ValueError("Missing body close on " + page.name)
            content = content.replace("</body>", CONSENT_TAG + "</body>", 1)
        if 'data-cookie-preferences' not in content:
            marker = re.search(r'<p\s+class=["\']ttn-footer-disclaimer["\']', content)
            if not marker:
                raise ValueError("No footer disclaimer on " + page.name)
            content = content[:marker.start()] + PREFERENCE_BUTTON + content[marker.start():]
        if content != original:
            page.write_text(content, encoding="utf-8")
            changes.append(page.name)
    print(f"GA4 consent audit: repaired {len(changes)} of {len(list(Path(root).glob('*.html')))} HTML pages.")
    if changes:
        print("Repaired pages: " + ", ".join(changes[:30]))
    return changes

if __name__ == "__main__":
    repair()
