#!/usr/bin/env python3
import json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
from bs4 import BeautifulSoup
root=Path.cwd(); zip_path=root/'ttn_oct31_approved_publication.zip'
if not zip_path.is_file():sys.exit('Publication package missing')
pkg=root/'.ttn-publication-temp';pkg.mkdir(exist_ok=True)
with zipfile.ZipFile(zip_path) as z:z.extractall(pkg)
raw=(root/'articles.js').read_text();match=re.search(r'\[',raw);end=raw.rfind(']')
entries=json.loads(raw[match.start():end+1]);ids={a['id'] for a in entries}
expected_slugs={json.loads(p.read_text())['slug'] for p in pkg.glob('*-seo.json')}
if expected_slugs and expected_slugs.issubset(ids) and all((root/(slug+'.html')).is_file() and all((root/('assets/editorial/' if suffix=='-cover.webp' else 'assets/responsive/')/(slug+suffix)).is_file() for suffix in ('-cover.webp','-480.webp','-960.webp')) for slug in expected_slugs):
    print('ALREADY PUBLISHED: all three articles and nine images present; no duplicate publishing needed',flush=True)
    shutil.rmtree(pkg)
    sys.exit(0)
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
new=[]
for file in sorted(pkg.glob('*-seo.json')):
    spec=json.loads(file.read_text());slug=spec['slug'];section=spec['section'];canonical_section=section
    if slug in ids or (root/(slug+'.html')).exists():sys.exit('Duplicate '+slug)
    fragment=BeautifulSoup((pkg/(slug+'-fragment.html')).read_text(),'html.parser')
    body=fragment.select_one('.editorial-body');dek=fragment.select_one('.editorial-dek')
    # The source export mistakenly joined each section heading and its first paragraph
    # into a single h2. Restore semantic paragraphs before the 700-word audit.
    for heading in body.select('h2'):
        heading_text=heading.get_text(' ',strip=False)
        if '\\n' in heading_text:
            header, paragraph=heading_text.split('\\n',1)
            heading.string=header.strip()
            if paragraph.strip():
                p=fragment.new_tag('p');p.string=paragraph.strip();heading.insert_after(p)
    additions={
      'openai-funding-target-cut-october-2026': [
       "The distinction between the size of a funding round and a company's overall valuation is fundamental. A lower fundraising target means the company seeks to receive less new capital in that transaction. It does not, by itself, demonstrate a comparable decline in product demand, revenue, or the value of existing investors' shares. The proposed valuation is a negotiated reference point and remains uncertain until the financing terms are finalized.",
       "Readers should also distinguish company announcements from reporting based on people involved in private fundraising discussions. Neither the final subscription amounts nor any completed closing can be inferred from a reported target. Future statements from OpenAI or participating investors, if released, would provide stronger evidence of the actual financing outcome."
      ],
      'bitcoin-etf-outflows-october-30-2026': [
       "For a clearer comparison across sessions, investors can examine dollar flows alongside each fund's size. An identical redemption amount can be much more significant for a small fund than for a large one. Fund-wide totals also conceal variation: withdrawals from several products can coincide with unchanged flows at others. Consequently, the direction of aggregate flows should not be presented as a unanimous decision by all institutional participants.",
       "Timing matters when comparing reports. US-listed ETF activity follows the securities-market calendar, while bitcoin itself trades continuously. A bitcoin price change during the weekend cannot be treated as evidence of weekend subscriptions or redemptions in US exchange-traded funds. The dates and data cutoffs used by each reporting service should therefore accompany comparisons of daily figures."
      ]
    }
    if slug in additions:
        for paragraph in additions[slug]:
            p=fragment.new_tag('p');p.string=paragraph;body.append(p)
    assert body and dek,(slug,'missing article body or intro')
    assert len(body.get_text(' ',strip=True).split())>=700,(slug,'too short')
    cover=slug+'-cover.webp'
    for name in [cover,slug+'-480.webp',slug+'-960.webp']:
        target=root/('assets/editorial' if name==cover else 'assets/responsive')/name
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(pkg/name,target)
    template=('infineon-villach-gan-11-billion-2026.html' if section=='Tech & AI' else 'binance-security-investigation-stablecoin-freezes-2026.html' if section=='Crypto' else 'us-employment-cost-index-q3-2026-real-wages.html')
    soup=BeautifulSoup((root/template).read_text(),'html.parser')
    main=soup.select_one('main');old=main.select_one('.editorial-body')
    assert old,(slug,'template article body missing')
    old.replace_with(body)
    title=spec['headline'];description=spec['metaDescription']
    main.find('h1').string=title
    intro=main.select_one('.article-dek')
    if intro:intro.string=dek.get_text(' ',strip=True)
    tm=main.select_one('time')
    if tm:tm['datetime']=now;tm.string=now[:10]
    hero=main.select_one('.article-hero-image')
    assert hero,(slug,'template hero missing')
    hero['src']=spec['image']
    hero['srcset']=f'assets/responsive/{slug}-480.webp 480w, assets/responsive/{slug}-960.webp 960w, assets/editorial/{cover} 1920w'
    hero['alt']=f'Editorial photo illustrating {title}'
    link=main.select_one('a[href="tech-ai.html"],a[href="analysis.html"],a[href="crypto.html"]')
    if link:link['href']='tech-ai.html' if section=='Tech & AI' else 'crypto.html' if section=='Crypto' else 'analysis.html'
    badge=main.select_one('.ttn-original-badge')
    if badge:badge.string=section
    url='https://globtechco.github.io/ttn-finans/'+slug+'.html'
    image='https://globtechco.github.io/ttn-finans/assets/editorial/'+cover
    seo_title=spec['seoTitle']
    if len(seo_title+' | TTN Finance')>65:
        seo_title=seo_title[:65-len(' | TTN Finance')].rsplit(' ',1)[0].rstrip(' ,:-')
    soup.title.string=seo_title+' | TTN Finance'
    for selector,value in [('meta[name="description"]',description),('meta[property="og:title"]',title),('meta[property="og:description"]',description),('meta[property="og:url"]',url),('meta[property="article:published_time"]',now),('meta[property="og:image"]',image),('meta[property="og:image:secure_url"]',image),('meta[name="twitter:title"]',seo_title+' | TTN Finance'),('meta[name="twitter:description"]',description),('meta[name="twitter:image"]',image)]:
        tag=soup.select_one(selector)
        if tag:tag['content']=value
    canon=soup.select_one('link[rel="canonical"]')
    if canon:canon['href']=url
    schema=soup.select_one('script[type="application/ld+json"]')
    if schema:
        obj=json.loads(schema.string);obj.update({'headline':title,'description':description,'datePublished':now,'dateModified':now,'mainEntityOfPage':url,'image':image,'articleSection':canonical_section});schema.string=json.dumps(obj,ensure_ascii=False)
    for node in main.select('details, aside.editorial-related'):node.decompose()
    symbols = {'intel-amazon-ai-spending-tech-selloff-october-2026':[('INTC','NASDAQ:INTC'),('AMZN','NASDAQ:AMZN'),('NDX','NASDAQ:NDX'),('SPX','SP:SPX')], 'bitcoin-etf-outflows-october-30-2026':[('BTC','COINBASE:BTCUSD'),('ETH','COINBASE:ETHUSD'),('IBIT','NASDAQ:IBIT'),('FBTC','BATS:FBTC')]}
    if slug in symbols:
        widget=soup.new_tag('div',attrs={'class':'article-tickers','aria-label':'Relevant market charts'})
        for symbol,tv in symbols[slug]:
            from urllib.parse import quote
            a=soup.new_tag('a',attrs={'class':'article-ticker-tag','href':'https://www.tradingview.com/chart/?symbol='+quote(tv,safe=''),'data-tv':tv,'title':'View '+symbol+' chart on TradingView'})
            b=soup.new_tag('b');b.string=symbol;a.append(b);widget.append(a)
        body.insert_after(widget)
    (root/(slug+'.html')).write_text(str(soup))
    sources=[{'label':a.get_text(' ',strip=True),'url':a['href']} for a in fragment.select('a[href^="https://"]')]
    new.append({'id':slug,'title':title,'dek':dek.get_text(' ',strip=True),'section':canonical_section,'tickers':[],'imageAlt':hero['alt'],'date':now,'author':'TTN Research Desk','format':'news','image':spec['image'],'body':[str(n) for n in body.find_all(['p','h2'],recursive=False)],'sources':sources})
    print('Article ready:',slug,flush=True)
(root/'articles.js').write_text(raw[:match.start()]+json.dumps(new+entries,ensure_ascii=False,indent=2)+raw[end+1:])
for command in [['python3','scripts/refresh_static_editorial.py'],['python3','scripts/refresh_seo_metadata.py'],['python3','scripts/audit_article_lengths.py'],['python3','scripts/verify_site.py'],['node','scripts/test-independent-loading.cjs'],['node','scripts/test-navigation.cjs']]:
    print('CHECK',*command,flush=True);subprocess.run(command,check=True)
shutil.rmtree(pkg)
subprocess.run(['git','add','-A'],check=True)
subprocess.run(['git','commit','-m','Publish verified October 31 TTN Finance coverage'],check=True)
subprocess.run(['git','push','origin','HEAD:main'],check=True)
print('PUBLICATION PUSHED',flush=True)
