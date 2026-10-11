#!/usr/bin/env python3
"""Audit Original TTN imagery. Never modifies news.js, config.js or external feeds.
Usage: python3 scripts/audit_original_images.py
"""
from pathlib import Path
from collections import Counter
import re
ROOT=Path(__file__).resolve().parent.parent
articles=(ROOT/"articles.js").read_text(encoding="utf-8")
matches=re.findall(r'\bimage:\s*["\']([^"\']+)["\']',articles)
pages=[p for p in ROOT.glob("*.html") if 'TTN Original' in p.read_text(encoding="utf-8",errors="replace") and p.name not in ("index.html","analysis.html")]
stock_pages=[]
social_stock=[]
for page in pages:
    text=page.read_text(encoding="utf-8",errors="replace")
    if 'images.pexels.com' in text:
        stock_pages.append(page.name)
    if re.search(r'<meta\s+(?:name|property)=["\'](?:twitter:image|og:image)["\'][^>]*pexels',text):
        social_stock.append(page.name)
print(f"Original TTN article images (articles.js): {len(matches)}")
print(f"Pexels entries in articles.js: {sum('pexels.com' in x for x in matches)}")
print(f"TTN Original standalone pages: {len(pages)}")
print(f"Standalone pages still containing Pexels: {len(stock_pages)}")
print(f"Social share images still using Pexels: {len(social_stock)}")
print("Pages requiring replacement:")
for name in stock_pages:
    print(" -",name)
