#!/usr/bin/env python3
"""Replace Original TTN Pexels photography with approved local editorial images.

Run from repository root AFTER unpacking ttn_editorial_assets_ready.zip into this repository.
Only named original article files, articles.js and sitemap-adjacent metadata are edited.
Aggregator modules news.js/config.js are never modified.
"""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parent.parent
BASE="https://globtechco.github.io/ttn-finans/"
MAPPING={
    "ai-data-center-electricity-demand-2026":"assets/editorial/ai-data-center-operations.webp",
    "ai-capex-nasdaq-correction":"assets/editorial/ai-capex-market-impact.webp",
    "ai-monetization-gap-explained":"assets/editorial/ai-revenue-test.webp",
    "circular-ai-financing-explained":"assets/editorial/ai-infrastructure-investment.webp",
}
def replace_meta(html,key,value,property_name="property"):
    pat=r'(<meta\\s+'+property_name+r'="'+re.escape(key)+r'"\\s+content=")[^"]*(")'
    return re.sub(pat,lambda m:m.group(1)+value+m.group(2),html,count=1)
def migrate():
    missing=[path for path in MAPPING.values() if not (ROOT/path).is_file()]
    if missing: raise SystemExit("Missing images; no files changed: "+", ".join(missing))
    articles=ROOT/"articles.js"
    js=articles.read_text(encoding="utf-8")
    plan=[]
    for slug,image in MAPPING.items():
        page=ROOT/(slug+".html")
        if not page.is_file(): raise SystemExit("Missing article page; no files changed: "+str(page))
        old=page.read_text(encoding="utf-8")
        new=re.sub(r'(<img\\b[^>]*\\bsrc=")https://images\\.pexels\\.com/[^"]+(")',lambda m:m.group(1)+image+m.group(2),old,count=1)
        if '<img ' not in new or 'src="'+image+'"' not in new:
            # New articles may correctly have no image at all.
            position=new.find('<h1>')
            if position<0: raise SystemExit("Missing H1: "+slug)
            stop=new.find('</h1>',position)
            new=new[:stop+5]+'\\n<img class="article-hero-image" src="'+image+'" loading="eager" decoding="async" width="1200" height="675" alt="Editorial illustration of '+slug.replace("-"," ")+'">'+new[stop+5:]
        full=BASE+image
        new=replace_meta(new,"og:image",full)
        new=replace_meta(new,"twitter:image",full,"name")
        if '<meta property="og:image"' not in new:new=new.replace('</head>','<meta property="og:image" content="'+full+'">\\n</head>')
        if '<meta name="twitter:image"' not in new:new.replace('</head>','<meta name="twitter:image" content="'+full+'">\\n</head>')
        # Update JSON-LD image only when present, otherwise preserve unrelated publisher metadata.
        new=re.sub(r'("image"\\s*:\\s*)\\[?\\s*"https://images\\.pexels\\.com/[^"]+"\\s*\\]?',lambda m:m.group(1)+'"'+full+'"',new)
        start=js.find('id: "'+slug+'"')
        if start<0:raise SystemExit("Not found in article catalog: "+slug)
        nxt=js.find('\\n  {',start+6)
        if nxt<0:nxt=len(js)
        part=js[start:nxt]
        part,count=re.subn(r'(image:\\s*")[^"]+(")',lambda m:m.group(1)+image+m.group(2),part,count=1)
        if count==0:raise SystemExit("Image entry not found for "+slug)
        js=js[:start]+part+js[nxt:]
        plan.append((page,new))
    plan.append((articles,js))
    for file,content in plan:file.write_text(content,encoding="utf-8")
    print("Migrated",len(MAPPING),"Original TTN articles including catalog, hero and social metadata")
if __name__=="__main__":migrate()
