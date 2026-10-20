#!/usr/bin/env python3
"""Build a small attributed RSS snapshot; never rewrite or fetch full articles."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import json, re, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/news-feed.json"
MAX_AGE = timedelta(hours=48)

class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"): self.hidden+=1
    def handle_endtag(self, tag):
        if tag in ("script", "style"): self.hidden=max(0,self.hidden-1)
    def handle_data(self, text):
        if not self.hidden: self.parts.append(text)
def plain(value):
    parser=Text(); parser.feed(value or "")
    return re.sub(r"\s+", " ", unescape(" ".join(parser.parts))).strip()
def http_url(value):
    return isinstance(value,str) and urlparse(value).scheme in ("http","https") and bool(urlparse(value).netloc)
def children(node, name):
    return [child for child in node if child.tag.rsplit("}",1)[-1]==name]
def value(node, name):
    found=children(node,name)
    return (found[0].text or "").strip() if found else ""
def publication(text):
    try:
        dt=parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try: dt=datetime.fromisoformat(text.replace("Z","+00:00"))
        except (TypeError, ValueError): return None
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
def parse_feed(xml, name, now=None):
    now=now or datetime.now(timezone.utc); root=ET.fromstring(xml); items=[]
    for node in root.iter():
        if node.tag.rsplit("}",1)[-1] not in ("item","entry"): continue
        title=plain(value(node,"title")); link=value(node,"link")
        if not http_url(link):
            link=next((n.get("href","") for n in children(node,"link") if n.get("rel","alternate")=="alternate"),"")
        date=publication(value(node,"pubDate") or value(node,"published") or value(node,"updated"))
        if not title or not http_url(link) or not date or date>now+timedelta(minutes=15) or now-date>MAX_AGE: continue
        desc=plain(value(node,"description") or value(node,"summary"))[:220]
        image=None
        for child in node.iter():
            kind=child.tag.rsplit("}",1)[-1]
            candidate=child.get("url","")
            if kind in ("thumbnail","content","enclosure") and http_url(candidate):
                media_type=child.get("type","")
                if kind=="thumbnail" or media_type.startswith("image/") or re.search(r"\.(jpg|jpeg|png|webp)(?:\?|$)",candidate,re.I):
                    image=candidate; break
        items.append(dict(title=title,desc=desc,link=link,image=image,pubDate=date.isoformat(),source=name))
        if len(items)>=25: break
    return items
def configured_feeds():
    text=(ROOT/"config.js").read_text()
    block=re.search(r"NEWS_FEEDS:\s*\[(.*?)\n  \]",text,re.S)
    if not block: raise ValueError("NEWS_FEEDS is missing")
    return re.findall(r'\{\s*name:\s*"([^"]+)",\s*url:\s*"([^"]+)"',block[1])
def retrieve(feed):
    name,url=feed
    try:
        request=Request(url,headers={"User-Agent":"TTNFinance-RSSReader/1.0 (+https://globtechco.github.io/ttn-finans/)","Accept":"application/rss+xml, application/xml, text/xml"})
        with urlopen(request,timeout=20) as response: content=response.read(2_000_001)
        if len(content)>2_000_000: raise ValueError("Feed is too large")
        items=parse_feed(content,name)
        return items,dict(name=name,ok=bool(items),count=len(items))
    except Exception as error:
        return [],dict(name=name,ok=False,error=str(error)[:160])
def main():
    now=datetime.now(timezone.utc); items=[]; results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for batch,status in pool.map(retrieve,configured_feeds()):
            items.extend(batch); results.append(status)
    # Keep original publication times during a temporary single-source outage.
    prior={}
    if TARGET.exists():
        try: prior=json.loads(TARGET.read_text())
        except (ValueError,OSError): pass
    if not items:
        raise SystemExit("No fresh RSS responses; preserving the previous snapshot: "+json.dumps(results))
    good_sources={s["name"] for s in results if s["ok"]}
    for item in prior.get("items",[]):
        date=publication(item.get("pubDate",""))
        if item.get("source") not in good_sources and date and timedelta(0)<=now-date<=MAX_AGE:
            items.append(item)
    seen=set(); unique=[]
    for item in sorted(items,key=lambda i:i["pubDate"],reverse=True):
        if item["link"] not in seen:
            seen.add(item["link"]); unique.append(item)
    payload=dict(version=1,generatedAt=now.isoformat(),sources=results,items=unique[:150])
    TARGET.parent.mkdir(exist_ok=True)
    TARGET.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(generatedAt=payload["generatedAt"],items=len(payload["items"]),sources=results),ensure_ascii=False))
if __name__=="__main__": main()
