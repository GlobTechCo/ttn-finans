#!/usr/bin/env python3
"""Check published HTML, complete static discovery and generated card integrity."""
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse, unquote
import hashlib,json,re,xml.etree.ElementTree as ET
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
BASE='https://globtechco.github.io/ttn-finans/'

def verify():
    articles=json.loads((ROOT/'articles.js').read_text().split('=',1)[1].strip().removesuffix(';'))
    ids={a['id'] for a in articles};assert len(ids)==len(articles)
    cards=json.loads((ROOT/'article-cards.js').read_text().split('const TTN_ARTICLES = ',1)[1].strip().removesuffix(';'))
    assert {a['id'] for a in cards}==ids
    cards_by_id={a['id']:a for a in cards}
    assert not any('body' in a or 'sources' in a for a in cards)
    assert (ROOT/'article-cards.js').stat().st_size < (ROOT/'articles.js').stat().st_size * .3
    docs={p.name:html.fromstring(p.read_text()) for p in ROOT.glob('*.html')}
    inbound=defaultdict(set);broken=[];schema_count=0
    for name,doc in docs.items():
        if name.startswith('google') and not doc.xpath('//head'):continue
        if name.startswith('google') and not doc.xpath('//title'):continue
        robots=' '.join(doc.xpath('//meta[@name="robots"]/@content'))
        if 'noindex' not in robots:
            assert len(doc.xpath('//h1'))==1,(name,'H1')
            title=doc.findtext('.//title');assert title and len(title)<=65,(name,'title',title)
            descriptions=doc.xpath('//meta[@name="description"]/@content');assert len(descriptions)==1 and 70<=len(descriptions[0])<=160,(name,'description',descriptions)
            canonical=doc.xpath('//link[@rel="canonical"]/@href');assert canonical==[BASE if name=='index.html' else BASE+name],(name,canonical)
        for value in doc.xpath('//script[@type="application/ld+json"]/text()'):json.loads(value);schema_count+=1
        for image in doc.xpath('//img'):assert image.get('alt') is not None,(name,'image alt')
        for element in doc.xpath('//*[@href or @src]'):
            attr='href' if element.get('href') is not None else 'src';value=element.get(attr);u=urlparse(value)
            if u.scheme in {'mailto','tel','data','javascript'}:continue
            if u.netloc and not value.startswith(BASE):continue
            if u.netloc:path=unquote(u.path.removeprefix('/ttn-finans/'))
            elif u.path.startswith('/ttn-finans/'):path=unquote(u.path.removeprefix('/ttn-finans/'))
            else:path=unquote(u.path.lstrip('/'))
            if not path:path=name if not u.netloc else 'index.html'
            target=ROOT/path
            if path.endswith('/'):target=target/'index.html'
            if not target.exists():broken.append((name,value))
            if element.tag=='a' and path!=name and path.removesuffix('.html') in ids:inbound[path].add(name)
        for image in doc.xpath('//img[@srcset]'):
            for item in image.get('srcset').split(','):
                source=item.strip().split()[0]
                if not urlparse(source).scheme:assert (ROOT/source).is_file(),(name,'srcset',source)
    assert not broken,broken
    for a in articles:
        doc=docs[a['id']+'.html']
        assert doc.xpath('//h1')[0].text_content()==a['title'],a['id']
        schema=json.loads(doc.xpath('//script[@type="application/ld+json"]/text()')[0])
        assert schema['datePublished']==a['date']==cards_by_id[a['id']]['date'],(a['id'],'publication date')
        published=doc.xpath('//meta[@property="article:published_time"]/@content')
        if published:assert published==[a['date']],(a['id'],'publication metadata')
        blocks=doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," editorial-related ")]')
        assert len(blocks)==1,(a['id'],'related blocks')
        links=blocks[0].xpath('.//a/@href')
        assert len(links)==3 and len(set(links))==3,(a['id'],links)
        assert all(i.endswith('.html') and (ROOT/i).is_file() and i!=a['id']+'.html' for i in links)
        assert inbound[a['id']+'.html'],(a['id'],'orphan')
        assert 'articles.js' not in (ROOT/(a['id']+'.html')).read_text()
    directory_links=set()
    for name in ['analysis.html','tech-ai.html']:
        directory=docs[name].xpath('//*[contains(concat(" ",normalize-space(@class)," ")," editorial-topics ")]')
        assert len(directory)==1
        directory_links.update(directory[0].xpath('.//a/@href'))
    assert directory_links=={i+'.html' for i in ids}
    card_version=hashlib.sha256((ROOT/'article-cards.js').read_bytes()).hexdigest()[:12]
    for name in ['index.html','analysis.html','tech-ai.html']:
        assert docs[name].xpath('//script[starts-with(@src,"article-cards.js")]/@src')==['article-cards.js?v='+card_version],(name,'stale card catalog')
    assert docs['index.html'].xpath('//noscript')
    assert 'This page could not be found' in docs['404.html'].text_content()
    assert docs['404.html'].xpath('//base/@href')==[BASE]
    assert docs['404.html'].xpath('//meta[@name="robots"]/@content')==['noindex,follow']
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'};urls=ET.parse(ROOT/'sitemap.xml').findall('s:url',ns)
    assert all(u.find('s:lastmod',ns) is not None and u.find('s:lastmod',ns).text for u in urls)
    assert not any(u.find('s:loc',ns).text.endswith('404.html') for u in urls)
    assert (ROOT/'_config.yml').read_text().count('  - scripts')==1
    assert len(list((ROOT/'scripts').glob('*.json')))==2
    print(f'PASS: {len(docs)} pages; {len(articles)} articles; {schema_count} JSON-LD blocks; no broken local references or orphan articles; complete topic directories, concise metadata and dated sitemap.')
if __name__=='__main__':verify()
