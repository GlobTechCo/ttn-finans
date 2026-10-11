#!/usr/bin/env python3
"""Read-only SEO and editorial link quality audit for TTN Original pages.

Run: python3 scripts/audit_original_seo.py
Does not open, edit, or fetch the news aggregator.
"""
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
import json,re
ROOT=Path(__file__).resolve().parent.parent
BASE="https://globtechco.github.io/ttn-finans/"
CATALOG=(ROOT/"articles.js").read_text(encoding="utf-8")
SLUGS=re.findall(r'\bid:\s*"([^"]+)"',CATALOG)
class Metadata(HTMLParser):
    def __init__(self):
        super().__init__();self.meta={};self.links={};self.headings=[];self.images=[];self.title="";self._title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="meta":
            key=a.get("name",a.get("property",""));self.meta[key]=a.get("content","")
        if tag=="link":self.links[a.get("rel","")]=a.get("href","")
        if tag=="img":self.images.append(a)
        if tag=="h1":self.headings.append("h1")
        if tag=="title":self._title=True
    def handle_endtag(self,tag):
        if tag=="title":self._title=False
    def handle_data(self,data):
        if self._title:self.title+=data
def audit():
    issues=Counter();rows=[]
    for slug in SLUGS:
        f=ROOT/(slug+".html")
        if not f.is_file():issues["missing_standalone_page"]+=1;continue
        raw=f.read_text(encoding="utf-8");p=Metadata();p.feed(raw)
        found=[]
        checks=[
            ("missing_title",bool(p.title.strip())),
            ("missing_description",bool(p.meta.get("description"))),
            ("missing_canonical",p.links.get("canonical")==BASE+slug+".html"),
            ("missing_h1",p.headings.count("h1")==1),
            ("missing_og_title",bool(p.meta.get("og:title"))),
            ("missing_og_description",bool(p.meta.get("og:description"))),
            ("missing_social_image",bool(p.meta.get("og:image") and p.meta.get("twitter:image"))),
        ]
        for code,ok in checks:
            if not ok:issues[code]+=1;found.append(code)
        if "images.pexels.com" in raw:issues["pexels_reference"]+=1;found.append("pexels_reference")
        if any(not a.get("alt") for a in p.images):issues["image_missing_alt"]+=1;found.append("image_missing_alt")
        if found:rows.append({"article":slug,"issues":found})
    print(json.dumps({"total_original_articles":len(SLUGS),"unique_slugs":len(set(SLUGS)),"issue_counts":issues,"pages":rows},indent=2))
if __name__=="__main__":audit()
