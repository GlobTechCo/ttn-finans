#!/usr/bin/env python3
import json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
from bs4 import BeautifulSoup
root=Path.cwd(); zip_path=root/'ttn_three_articles_publication_package.zip'
if not zip_path.is_file():sys.exit('Publication package missing')
pkg=root/'.ttn-publication-temp';pkg.mkdir(exist_ok=True)
with zipfile.ZipFile(zip_path) as z:z.extractall(pkg)
raw=(root/'articles.js').read_text();match=re.search(r'\[',raw);end=raw.rfind(']')
entries=json.loads(raw[match.start():end+1]);ids={a['id'] for a in entries}
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
new=[]
for file in sorted(pkg.glob('*-seo.json')):
    spec=json.loads(file.read_text());slug=spec['slug'];section=spec['section']
    if slug in ids or (root/(slug+'.html')).exists():sys.exit('Duplicate '+slug)
    fragment=BeautifulSoup((pkg/(slug+'-fragment.html')).read_text(),'html.parser')
    body=fragment.select_one('.editorial-body');dek=fragment.select_one('.editorial-dek')
    assert body and dek,(slug,'missing article body or intro')
    assert len(body.get_text(' ',strip=True).split())>=700,(slug,'too short')
    cover=slug+'-cover.webp'
    for name in [cover,slug+'-480.webp',slug+'-960.webp']:
        target=root/('assets/editorial' if name==cover else 'assets/responsive')/name
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(pkg/name,target)
    template='infineon-villach-gan-11-billion-2026.html' if section=='Tech & AI' else 'us-employment-cost-index-q3-2026-real-wages.html'
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
    hero['srcset']=f'assets/responsive/{slug}-480.webp 480w, assets/responsive/{slug}-960.webp 960w, assets/editorial/{cover} 1672w'
    hero['alt']=f'Editorial photo illustrating {title}'
    link=main.select_one('a[href="tech-ai.html"],a[href="analysis.html"]')
    if link:link['href']='tech-ai.html' if section=='Tech & AI' else 'analysis.html'
    badge=main.select_one('.ttn-original-badge')
    if badge:badge.string=section
    url='https://globtechco.github.io/ttn-finans/'+slug+'.html'
    image='https://globtechco.github.io/ttn-finans/assets/editorial/'+cover
    soup.title.string=spec['seoTitle']+' | TTN Finance'
    for selector,value in [('meta[name="description"]',description),('meta[property="og:title"]',title),('meta[property="og:description"]',description),('meta[property="og:url"]',url),('meta[property="article:published_time"]',now),('meta[property="og:image"]',image),('meta[property="og:image:secure_url"]',image),('meta[name="twitter:title"]',spec['seoTitle']+' | TTN Finance'),('meta[name="twitter:description"]',description),('meta[name="twitter:image"]',image)]:
        tag=soup.select_one(selector)
        if tag:tag['content']=value
    canon=soup.select_one('link[rel="canonical"]')
    if canon:canon['href']=url
    schema=soup.select_one('script[type="application/ld+json"]')
    if schema:
        obj=json.loads(schema.string);obj.update({'headline':title,'description':description,'datePublished':now,'dateModified':now,'mainEntityOfPage':url,'image':image,'articleSection':section});schema.string=json.dumps(obj,ensure_ascii=False)
    for node in main.select('details, aside.editorial-related'):node.decompose()
    (root/(slug+'.html')).write_text(str(soup))
    sources=[{'label':a.get_text(' ',strip=True),'url':a['href']} for a in fragment.select('a[href^="https://"]')]
    new.append({'id':slug,'title':title,'dek':dek.get_text(' ',strip=True),'section':'Tech & AI' if section=='Tech & AI' else 'Market Analysis','tickers':[],'imageAlt':hero['alt'],'date':now,'author':'TTN Research Desk','format':'news' if section!='Tech & AI' else 'explainer','image':spec['image'],'body':[str(n) for n in body.find_all(['p','h2'],recursive=False)],'sources':sources})
    print('Article ready:',slug,flush=True)
(root/'articles.js').write_text(raw[:match.start()]+json.dumps(new+entries,ensure_ascii=False,indent=2)+raw[end+1:])
for command in [['python3','scripts/refresh_static_editorial.py'],['python3','scripts/refresh_seo_metadata.py'],['python3','scripts/audit_article_lengths.py'],['python3','scripts/verify_site.py'],['node','scripts/test-independent-loading.cjs'],['node','scripts/test-navigation.cjs']]:
    print('CHECK',*command,flush=True);subprocess.run(command,check=True)
shutil.rmtree(pkg)
subprocess.run(['git','add','-A'],check=True)
subprocess.run(['git','commit','-m','Publish approved Ping Identity, Vistra and ANSI articles'],check=True)
subprocess.run(['git','push','origin','HEAD:main'],check=True)
print('PUBLICATION PUSHED',flush=True)
