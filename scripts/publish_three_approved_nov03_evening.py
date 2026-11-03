#!/usr/bin/env python3
import json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
from bs4 import BeautifulSoup
# The approved archive is processed by GitHub Actions on upload or script changes.\n# November 2 archive explicitly supported; workflow exists on main for this push. Sync 21 revised leads. Refresh cards after approved editorial teaser revisions. Supports Crypto analysis format after verifier update.
root=Path.cwd()
zip_path=root/'TTN_Finance_3_Articles_AUTO_PUBLISH_2026-11-03_EVENING.zip'
if not zip_path.is_file():sys.exit('November 3 evening package missing')
pkg=root/'.ttn-three-evening-publication-temp'
if pkg.exists():shutil.rmtree(pkg)
pkg.mkdir()
with zipfile.ZipFile(zip_path) as z:
    for member in z.namelist():
        if member.startswith('/') or '..' in Path(member).parts:sys.exit('Unsafe ZIP member')
    z.extractall(pkg)
from html import escape
manifest=json.loads((pkg/'manifest.json').read_text(encoding='utf-8'))
assert len(manifest['items'])==3,'Expected three approved articles'
sections={'Tech & AI','Market Analysis','Crypto'}
for item in manifest['items']:
    slug=item['slug']
    section=item['section']
    assert section in sections,(slug,section)
    source=pkg/(slug+'-fragment.html')
    fragment=BeautifulSoup(source.read_text(encoding='utf-8'),'html.parser')
    body=fragment.select_one('section.editorial-body')
    intro=fragment.select_one('.article-dek')
    assert body and intro,(slug,'missing article body or dek')
    assert len(body.get_text(' ',strip=True).split())>=700,(slug,'insufficient editorial length')
    for link in body.select('a[href]'):
        href=link['href']
        assert href.endswith('.html') and not href.startswith(('http:','https:','/')), (slug,'only internal in-body links allowed',href)
        assert (root/href).is_file(),(slug,'broken internal article link',href)
    sources=''.join('<li><a href="'+escape(x['url'],quote=True)+'">'+escape(x['label'])+'</a></li>' for x in item['sources'])
    source.write_text(str(BeautifulSoup('<div class="editorial-dek">'+escape(item['deck'])+'</div>','html.parser'))+str(body)+'<div class="source-links"><ul>'+sources+'</ul></div>',encoding='utf-8')
    cover=pkg/item['hero']
    assert cover.is_file(),('cover missing',slug)
    shutil.copy2(cover,pkg/(slug+'-cover.webp'))
    for width in (480,960):
        responsive=pkg/'assets'/'responsive'/(slug+f'-{width}.webp')
        assert responsive.is_file(),('responsive missing',slug,width)
        shutil.copy2(responsive,pkg/(slug+f'-{width}.webp'))
    dek=item['deck'].strip()
    # Full sentences in the social and SEO descriptions, not clipped mid-sentence.
    desc=dek if len(dek)<=160 else next((dek[:m.end()] for m in reversed(list(re.finditer(r'[.!?](?=\\s|$)',dek[:160]))) if m.end()>=70),dek[:159].rsplit(' ',1)[0].rstrip(' ,;:-.')+'.')
    assert 70<=len(desc)<=160,(slug,'invalid description',desc)
    title=item['title']
    seo=item.get('seo_title',title)
    if len(seo+' | TTN Finance')>65:
        seo=seo[:65-len(' | TTN Finance')].rsplit(' ',1)[0].rstrip(' ,;:-')
    spec={'slug':slug,'section':section,'headline':title,'seoTitle':seo,'metaDescription':desc,
          'image':item['hero'],'tickers':[{'NASDAQ:ANT':'','FX:UKOIL':'Brent Oil','BITSTAMP:XRPUSD':'XRP'}.get(x,x) for x in item.get('tickers_to_review',[]) if x!='NASDAQ:ANT'],'format':'news'}
    (pkg/(slug+'-seo.json')).write_text(json.dumps(spec,ensure_ascii=False),encoding='utf-8')
print('Validated three articles, all internal links, assets and social metadata',flush=True)
raw=(root/'articles.js').read_text();match=re.search(r'\[',raw);end=raw.rfind(']')
entries=json.loads(raw[match.start():end+1]);ids={a['id'] for a in entries}
expected_slugs={json.loads(p.read_text())['slug'] for p in pkg.glob('*-seo.json')}
if expected_slugs and expected_slugs.issubset(ids) and all((root/(slug+'.html')).is_file() and all((root/('assets/editorial/' if suffix=='-cover.webp' else 'assets/responsive/')/(slug+suffix)).is_file() for suffix in ('-cover.webp','-480.webp','-960.webp')) for slug in expected_slugs):
    print('ALREADY PUBLISHED: refreshing site indexes and cards without duplicating articles',flush=True)
    shutil.rmtree(pkg)
    subprocess.run(['python3','scripts/refresh_static_editorial.py'],check=True)
    subprocess.run(['python3','scripts/verify_site.py'],check=True)
    subprocess.run(['git','add','-A'],check=True)
    if subprocess.run(['git','diff','--cached','--quiet']).returncode:
        subprocess.run(['git','commit','-m','Expose Crypto analysis in homepage and topic archive'],check=True)
        subprocess.run(['git','pull','--rebase','origin','main'],check=True)
        subprocess.run(['git','push','origin','HEAD:main'],check=True)
    sys.exit(0)
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
new=[]
for file in sorted(pkg.glob('*-seo.json')):
    spec=json.loads(file.read_text());slug=spec['slug'];section=spec['section'];canonical_section=section
    assert section in {'Tech & AI','Market Analysis','Crypto'}, (slug,section)
    if slug in ids or (root/(slug+'.html')).exists():sys.exit('Duplicate '+slug)
    fragment=BeautifulSoup((pkg/(slug+'-fragment.html')).read_text(),'html.parser')
    body=fragment.select_one('.editorial-body');dek=fragment.select_one('.editorial-dek')
    assert body and dek,(slug,'missing article body or intro')
    # Site ticker refresh expects exactly one semantic section.editorial-body.
    body.name='section'
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
    title=spec['headline'];description=spec['metaDescription'].strip()
    assert len(description)<=160,(slug,'meta description too long')
    assert 70<=len(description)<=160,(slug,'meta description length',len(description))
    main.find('h1').string=title
    intro=main.select_one('.article-dek')
    if intro:intro.string=dek.get_text(' ',strip=True)
    tm=main.select_one('time')
    if tm:tm['datetime']=now;tm.string=now[:10]
    hero=main.select_one('.article-hero-image')
    assert hero,(slug,'template hero missing')
    hero['src']=spec['image']
    hero['srcset']=f'assets/responsive/{slug}-480.webp 480w, assets/responsive/{slug}-960.webp 960w, assets/editorial/{cover} 1920w'
    hero['alt']=next((x.get('cover_alt') for x in manifest['items'] if x['slug']==slug),f'Editorial illustration accompanying {title}')
    link=main.select_one('a[href="tech-ai.html"],a[href="analysis.html"],a[href="crypto.html"]')
    if link:link['href']={'Tech & AI':'tech-ai.html','Market Analysis':'analysis.html','Crypto':'crypto.html'}[section]
    badge=main.select_one('.ttn-original-badge')
    if badge:badge.string=section
    url='https://globtechco.github.io/ttn-finans/'+slug+'.html'
    image='https://globtechco.github.io/ttn-finans/assets/editorial/'+cover
    # Derive complete social text from the reviewed headline and deck, not old template tags.
    seo_title=spec['seoTitle']
    if len(seo_title+' | TTN Finance')>65:
        seo_title=seo_title[:65-len(' | TTN Finance')].rsplit(' ',1)[0].rstrip(' ,:-')
    soup.title.string=seo_title+' | TTN Finance'
    for selector,value in [('meta[name="description"]',description),('meta[property="og:title"]',title),('meta[property="og:description"]',description),('meta[property="og:url"]',url),('meta[property="article:published_time"]',now),('meta[property="og:image"]',image),('meta[property="og:image:secure_url"]',image),('meta[name="twitter:title"]',seo_title+' | TTN Finance'),('meta[name="twitter:description"]',description),('meta[name="twitter:image"]',image)]:
        tag=soup.select_one(selector)
        if tag:tag['content']=value
    alt=next((x.get('cover_alt') for x in manifest['items'] if x['slug']==slug),'Editorial illustration accompanying '+title)
    for selector in ['meta[property="og:image:alt"]','meta[name="twitter:image:alt"]']:
        tag=soup.select_one(selector)
        if tag: tag['content']=alt
    for selector,value in [('meta[property="og:image:width"]','1920'),('meta[property="og:image:height"]','1080'),('meta[property="og:image:type"]','image/webp')]:
        tag=soup.select_one(selector)
        if tag:tag['content']=value
    canon=soup.select_one('link[rel="canonical"]')
    if canon:canon['href']=url
    schema=soup.select_one('script[type="application/ld+json"]')
    if schema:
        obj=json.loads(schema.string);obj.update({'headline':title,'description':description,'datePublished':now,'dateModified':now,'mainEntityOfPage':url,'image':image,'articleSection':canonical_section});schema.string=json.dumps(obj,ensure_ascii=False)
    for node in main.select('details, aside.editorial-related'):node.decompose()
    # Preserve a discreet primary-source block below the article and ticker controls.
    reference_links=[(a.get_text(' ',strip=True),a['href']) for a in fragment.select('a[href^="https://"]')]
    if reference_links and not main.select_one('.editorial-sources'):
        from html import escape as html_escape
        rows=''.join('<li><a href="'+html_escape(url,quote=True)+'" target="_blank" rel="noopener noreferrer">'+html_escape(label)+'</a></li>' for label,url in reference_links)
        note=BeautifulSoup('<details class="editorial-sources"><summary>Sources and methodology</summary><p>Primary sources and supporting documentation.</p><ul>'+rows+'</ul></details>','html.parser')
        main.append(note)
    # Keep source references in the lower article area, before related reading.
    if section=='Crypto':
        for nav in main.select('a[href="analysis.html"]'):
            nav['href']='crypto.html'
    (root/(slug+'.html')).write_text(str(soup))
    sources=[{'label':a.get_text(' ',strip=True),'url':a['href']} for a in fragment.select('a[href^="https://"]')]
    new.append({'id':slug,'title':title,'dek':dek.get_text(' ',strip=True),'section':canonical_section,'tickers':spec.get('tickers',[]),'imageAlt':hero['alt'],'date':now,'author':'TTN Research Desk','format':spec.get('format','news' if section!='Tech & AI' else 'explainer'),'image':spec['image'],'body':[str(n) for n in body.find_all(['p','h2'],recursive=False)],'sources':sources})
    print('Article ready:',slug,flush=True)
(root/'articles.js').write_text(raw[:match.start()]+json.dumps(new+entries,ensure_ascii=False,indent=2)+raw[end+1:])
for command in [['python3','scripts/refresh_static_editorial.py'],['python3','scripts/refresh_seo_metadata.py'],['python3','scripts/audit_article_lengths.py'],['python3','scripts/verify_site.py'],['node','scripts/test-independent-loading.cjs'],['node','scripts/test-navigation.cjs']]:
    print('CHECK',*command,flush=True);subprocess.run(command,check=True)
shutil.rmtree(pkg)
subprocess.run(['git','add','-A'],check=True)
subprocess.run(['git','commit','-m','Publish approved TTN Finance editorial articles'],check=True)
subprocess.run(['git','pull','--rebase','origin','main'],check=True)
subprocess.run(['git','push','origin','HEAD:main'],check=True)
print('PUBLICATION PUSHED',flush=True)
