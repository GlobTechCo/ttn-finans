#!/usr/bin/env python3
"""Audit editorial word counts without reclassifying unchanged historical articles."""
import argparse, csv, hashlib, json, subprocess, sys
from pathlib import Path
from lxml import html
from editorial_length_reviews import REVIEWS

ROOT = Path(__file__).resolve().parents[1]
FURNITURE_IDS = {
 'jensen-huang-signals-return-to-nvidia-leadership-crisis-november-17-2026',
 'nsa-classified-communications-network-outage-us-infrastructure-reliability-november-17-2026',
 'software-outage-fears-wall-street-sell-off-technology-shares-slide-november-17-2026',
}

def extract_article_text(source, article_id):
    doc = html.fromstring(source)
    bodies = doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," editorial-body ")]')
    if len(bodies) > 1:
        raise ValueError(f"Multiple editorial-body containers: {article_id}")
    body = bodies[0] if bodies else None
    paragraphs = body.xpath('.//p') if body is not None else []
    # Imported pages can place the article paragraphs in the shared main flow
    # while retaining the editorial-body class on a non-paragraph wrapper.
    if not paragraphs:
        mains = doc.xpath('//main[@id="main-content"] | //main[contains(@class,"static-page")]')
        paragraphs = mains[0].xpath('.//p') if len(mains) == 1 else doc.xpath('//article//p')
    result = []
    for p in paragraphs:
        if p.xpath('ancestor-or-self::*[contains(concat(" ",normalize-space(@class)," ")," editorial-sources ") or contains(concat(" ",normalize-space(@class)," ")," article-sources ")]'):
            continue
        value = ' '.join(' '.join(p.itertext()).split())
        if value.lower() == 'sources' or value.lower().startswith('related ttn coverage:'):
            continue
        if 'Related context:' in value:
            value = value.split('Related context:', 1)[0].strip()
        if value:
            result.append(value)
    return result, doc

def previous_body_text(article_id):
    try:
        previous = subprocess.run(
            ['git','show',f'HEAD^:{article_id}.html'], cwd=ROOT,
            check=True, capture_output=True, text=True, encoding='utf-8'
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    paragraphs, _ = extract_article_text(previous, article_id)
    return '\n\n'.join(paragraphs)

def audit(root=ROOT):
    articles=json.loads((root/'articles.js').read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
    rows=[]
    for article in articles:
        article_id=article['id']
        paragraphs,doc=extract_article_text((root/(article_id+'.html')).read_bytes(),article_id)
        schema=None
        for node in doc.xpath('//script[translate(@type,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="application/ld+json"]'):
            try: value=json.loads(node.text or '{}')
            except (TypeError,ValueError): continue
            for candidate in (value if isinstance(value,list) else [value]):
                if isinstance(candidate,dict) and candidate.get('@type') in {'Article','NewsArticle'}:
                    schema=candidate; break
            if schema: break
        if not schema: raise ValueError(f"Missing valid Article/NewsArticle JSON-LD: {article_id}")
        kind=schema['@type']
        text='\n\n'.join(paragraphs)
        words=sum(len(p.split()) for p in paragraphs)
        previous=previous_body_text(article_id)
        # Metadata refreshes must not turn untouched legacy stories into newly
        # edited copy. Apply the strict 700-word minimum only to new/changed text.
        changed = previous is None or previous != text
        minimum=700 if changed else 0
        review=REVIEWS.get(article_id)
        if review and hashlib.sha256(text.encode()).hexdigest()==review['sha256']:
            minimum=review['words']
        maximum=900
        rows.append(dict(id=article_id,title=article['title'],date=article['date'],type=kind,
                         words=words,characters=len(text),minimum=minimum,maximum=maximum,
                         status='PASS' if minimum<=words<=maximum else 'FAIL'))
        if minimum>words or words>maximum:
            print(f"ARTICLE_TEXT_FOR_REVIEW: {article_id} ({words} paragraph words)")
            print(text); print("END_ARTICLE_TEXT_FOR_REVIEW")
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format',choices=['text','json','csv'],default='text')
    args=parser.parse_args(); rows=audit(); failures=[r for r in rows if r['status']=='FAIL']
    if args.format=='json': print(json.dumps(rows,ensure_ascii=False,indent=2))
    elif args.format=='csv':
        writer=csv.DictWriter(sys.stdout,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    else:
        for r in failures:
            reason=f"{r['words']} < {r['minimum']}" if r['words']<r['minimum'] else f"{r['words']} > {r['maximum']}"
            print(f"FAIL: {r['id']}: {reason} paragraph words")
        print(f"{'FAIL' if failures else 'PASS'}: {len(rows)} articles; {len(failures)} outside the approved range (700-900 for new or substantively changed copy; unchanged historical copy is preserved, with a 900-word maximum).")
    return bool(failures)

if __name__=='__main__':
    raise SystemExit(main())
