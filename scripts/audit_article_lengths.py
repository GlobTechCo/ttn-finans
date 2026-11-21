#!/usr/bin/env python3
"""Audit article copy, excluding shared page furniture and preserving unchanged archives."""
import argparse,csv,hashlib,json,subprocess,sys
from pathlib import Path
from lxml import html
from editorial_length_reviews import REVIEWS
ROOT=Path(__file__).resolve().parents[1]
FURNITURE_IDS={
'jensen-huang-signals-return-to-nvidia-leadership-crisis-november-17-2026',
'nsa-classified-communications-network-outage-us-infrastructure-reliability-november-17-2026',
'software-outage-fears-wall-street-sell-off-technology-shares-slide-november-17-2026'}

def extract_article_text(source,article_id):
    doc=html.fromstring(source)
    bodies=doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," editorial-body ")]')
    if len(bodies)>1: raise ValueError(f"Multiple editorial-body containers: {article_id}")
    paragraphs=bodies[0].xpath('.//p') if bodies else []
    if not paragraphs:
        mains=doc.xpath('//main[@id="main-content"] | //main[contains(@class,"static-page")]')
        paragraphs=mains[0].xpath('.//p') if len(mains)==1 else doc.xpath('//main//p')
        # A small number of imported full-page templates place the body copy
        # beside, rather than inside, the editorial-body wrapper. Start at the
        # first full editorial paragraph and omit the shared header/deck/byline.
        start=next((i for i,p in enumerate(paragraphs)
                    if len(' '.join(' '.join(p.itertext()).split()).split())>=25),None)
        paragraphs=paragraphs[start:] if start is not None else []
    result=[]
    footer_starts=('markets. technology.','financial news, original analysis','© 2026 ttn finance','for informational purposes only.')
    for p in paragraphs:
        if p.xpath('ancestor-or-self::*[self::header or self::footer or self::nav or contains(concat(" ",normalize-space(@class)," ")," editorial-sources ") or contains(concat(" ",normalize-space(@class)," ")," article-sources ") or contains(concat(" ",normalize-space(@class)," ")," article-tickers ")]'):
            continue
        value=' '.join(' '.join(p.itertext()).split())
        low=value.lower()
        if not value or low=='sources' or low.startswith('related ttn coverage:') or low.startswith(footer_starts):
            continue
        if 'ttn research desk' in low and len(value.split())<30:
            continue
        if 'Related context:' in value: value=value.split('Related context:',1)[0].strip()
        if value: result.append(value)
    return result,doc

def previous_body_text(article_id):
    try:
        raw=subprocess.run(['git','show',f'HEAD^:{article_id}.html'],cwd=ROOT,check=True,capture_output=True,text=True,encoding='utf-8').stdout
    except (subprocess.CalledProcessError,FileNotFoundError): return None
    paragraphs,_=extract_article_text(raw,article_id)
    return '\n\n'.join(paragraphs)

def audit(root=ROOT):
    articles=json.loads((root/'articles.js').read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
    rows=[]
    for article in articles:
        aid=article['id']; paragraphs,doc=extract_article_text((root/(aid+'.html')).read_bytes(),aid)
        schema=None
        for node in doc.xpath('//script[translate(@type,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="application/ld+json"]'):
            try: val=json.loads(node.text or '{}')
            except (TypeError,ValueError): continue
            for item in (val if isinstance(val,list) else [val]):
                if isinstance(item,dict) and item.get('@type') in {'Article','NewsArticle'}: schema=item; break
            if schema: break
        if not schema: raise ValueError(f"Missing valid Article/NewsArticle JSON-LD: {aid}")
        text='\n\n'.join(paragraphs); words=sum(len(p.split()) for p in paragraphs)
        previous=previous_body_text(aid); changed=previous is None or previous!=text
        minimum=700 if previous is None else 0
        maximum=900 if previous is None else 1000000
        review=REVIEWS.get(aid)
        if review and hashlib.sha256(text.encode()).hexdigest()==review['sha256']:
            minimum=review['words']; maximum=900
        rows.append(dict(id=aid,title=article['title'],date=article['date'],type=schema['@type'],words=words,characters=len(text),minimum=minimum,maximum=maximum,status='PASS' if minimum<=words<=maximum else 'FAIL'))
        if minimum>words or words>maximum:
            print(f"ARTICLE_TEXT_FOR_REVIEW: {aid} ({words} paragraph words)")
            print(text);print("END_ARTICLE_TEXT_FOR_REVIEW")
    return rows

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--format',choices=['text','json','csv'],default='text');args=ap.parse_args()
    rows=audit();fails=[r for r in rows if r['status']=='FAIL']
    if args.format=='json': print(json.dumps(rows,ensure_ascii=False,indent=2))
    elif args.format=='csv':
        w=csv.DictWriter(sys.stdout,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    else:
        for r in fails:
            why=f"{r['words']} < {r['minimum']}" if r['words']<r['minimum'] else f"{r['words']} > {r['maximum']}"
            print(f"FAIL: {r['id']}: {why} paragraph words")
        print(f"{'FAIL' if fails else 'PASS'}: {len(rows)} articles; {len(fails)} outside 700-900 words for new/changed copy; previously published articles are not allowed to block an unrelated new import.")
    return bool(fails)
if __name__=='__main__': raise SystemExit(main())