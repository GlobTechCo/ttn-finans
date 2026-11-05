"""Verify the published five-page release without sending analytics events."""
from pathlib import Path
import hashlib, time, urllib.request, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
BASE="https://globtechco.github.io/ttn-finans/"
PAGES=["free-cash-flow-explained.html","ai-inference-unit-economics-2026.html","stablecoins-explained-depeg-risk.html","compound-interest-calculator.html","crypto-profit-loss-calculator.html"]
FILES=PAGES+["calculators.js","five-page-tools.css","article-cards.js","index.html","analysis.html","tech-ai.html","crypto.html","sitemap.xml","sitemap-pages.txt"]
def fetch(path,agent="TTN-Finance-Release-Verification/1.0"):
    req=urllib.request.Request(BASE+path,headers={"User-Agent":agent,"Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=25) as response:
        assert response.status==200,(path,response.status)
        assert "noindex" not in response.headers.get("X-Robots-Tag","").lower(),path
        return response.read()
for attempt in range(30):
    try:
        differences=[path for path in FILES if fetch(path)!=(ROOT/path).read_bytes()]
        if not differences: break
        print("Waiting for Pages publication:",differences,flush=True)
    except Exception as error:
        print("Waiting for publication:",str(error),flush=True)
    time.sleep(10)
else:
    raise SystemExit("Published release does not yet match this source commit")
ns={"s":"http://www.sitemaps.org/schemas/sitemap/0.9"}
xml=fetch("sitemap.xml")
locations=[entry.text for entry in ET.fromstring(xml).findall("s:url/s:loc",ns)]
assert fetch("sitemap-pages.txt").decode().splitlines()==locations
assert len(locations)==len(set(locations))
assert all(BASE+p in locations for p in PAGES)
assert fetch("sitemap.xml","Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")==xml
for path in FILES:print("LIVE MATCH",path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
print("PASS:",len(FILES),"live files match the release; both sitemaps agree on",len(locations),"URLs.")
print("This verifies public delivery, not a real Googlebot fetch, Search Console acceptance or Google indexing.")
