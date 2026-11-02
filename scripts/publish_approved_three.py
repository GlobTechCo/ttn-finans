#!/usr/bin/env python3
import json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
from bs4 import BeautifulSoup
# The approved archive is processed by GitHub Actions on upload or script changes. Sync 21 revised leads. Refresh cards after approved editorial teaser revisions. Supports Crypto analysis format after verifier update.
root=Path.cwd()
archives=['TTN_Finance_3_publications_2026-11-02.zip','TTN_Two_Approved_Articles_PUBLISH_2026-11-02.zip','TTN_Three_Articles_APPROVED_PUBLISH_2026-11-02.zip','TTN_Polymarket_DeepSeek_APPROVED_PUBLISH_2026-11-01.zip','TTN_BTC_ETH_October_2026_PUBLISH.zip','TTN_DEWA_approved_article_PUBLISH_2026-11-01.zip','TTN_Finance_3_approved_articles_PUBLISH_2026-11-01.zip','TTN_NVIDIA_RTX_Spark_827_words_FINAL.zip','ttn_three_articles_publication_package.zip']
zip_path=next((root/name for name in archives if (root/name).is_file()),root/archives[-1])
if not zip_path.is_file():sys.exit('Publication package missing')
pkg=root/'.ttn-publication-temp';pkg.mkdir(exist_ok=True)
with zipfile.ZipFile(zip_path) as z:z.extractall(pkg)
# Normalize the approved November 2 editorial archive to the site's publication schema.
if (pkg/'manifest.json').exists():
    from html import escape
    from bs4 import BeautifulSoup
    manifest=json.loads((pkg/'manifest.json').read_text(encoding='utf-8'))
    assert len(manifest['items'])==3, 'Expected three approved stories'
    for item in manifest['items']:
        slug=item['slug']
        assert item['section'].strip()=='Market Analysis',slug
        fragment=BeautifulSoup((pkg/item['body_html']).read_text(encoding='utf-8'),'html.parser')
        body=fragment.select_one('.editorial-body')
        assert body and len(body.get_text(' ',strip=True).split())>=700,slug
        if slug.startswith('opec-'):
            assert not re.search(r'russia|russian',body.get_text(' ',strip=True),re.I),'OPEC editorial restriction'
        cover=pkg/item['hero']
        assert cover.is_file(),('approved cover missing',slug)
        shutil.copy2(cover,pkg/(slug+'-cover.webp'))
        # Responsive paths are required by the site template.
        # ImageMagick is available in the publishing runner; fall back to original bytes.
        for width in (480,960):
            dst=pkg/(slug+f'-{width}.webp')
            convert=shutil.which('convert') or shutil.which('magick')
            if convert:
                cp=[convert,str(cover),'-resize',f'{width}x',str(dst)]
                subprocess.run(cp,check=True)
            else:shutil.copy2(cover,dst)
        sources=''.join('<li><a href="'+escape(x['url'],quote=True)+'">'+escape(x['label'])+'</a></li>' for x in item['sources'])
        container=BeautifulSoup('<div class="editorial-dek">'+escape(item['dek'])+'</div>'+str(body)+'<div class="source-links"><ul>'+sources+'</ul></div>','html.parser')
        (pkg/(slug+'-fragment.html')).write_text(str(container),encoding='utf-8')
        spec={'slug':slug,'section':'Market Analysis','headline':item['title'],
              'seoTitle':item['suggested_headline'],'metaDescription':item['dek'][:155].rsplit(' ',1)[0].rstrip(' ,;:-.')+'.',
              'image':item['hero'],'tickers':item.get('tickers_to_review',[]),'format':'news'}
        (pkg/(slug+'-seo.json')).write_text(json.dumps(spec,ensure_ascii=False),encoding='utf-8')
    print('Normalized three approved November 2 articles, sources and images',flush=True)
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
        subprocess.run(['git','push','origin','HEAD:main'],check=True)
    sys.exit(0)
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
new=[]
for file in sorted(pkg.glob('*-seo.json')):
    spec=json.loads(file.read_text());slug=spec['slug'];section=spec['section'];canonical_section=section
    assert section in {'Tech & AI','Market Analysis','Crypto'}, (slug,section)
    if slug in ids or (root/(slug+'.html')).exists():sys.exit('Duplicate '+slug)
    fragment=BeautifulSoup((pkg/(slug+'-fragment.html')).read_text(),'html.parser')
    # Keep editorial internal links valid: replace outdated placeholder with an existing oil-sector report.
    for internal in fragment.select('a[href="oil-prices-brent-2026.html"]'):
        internal['href']='bp-q3-2026-profit-debt-deepwater-horizon.html'
        internal.string='our coverage of BP’s quarterly results'
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
    if len(description)>160:
        description=description[:157].rsplit(' ',1)[0].rstrip(' ,;:-.')+'.'
    assert 70<=len(description)<=160,(slug,'meta description length',len(description))
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
    if link:link['href']={'Tech & AI':'tech-ai.html','Market Analysis':'analysis.html','Crypto':'crypto.html'}[section]
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
subprocess.run(['git','push','origin','HEAD:main'],check=True)
print('PUBLICATION PUSHED',flush=True)
