#!/usr/bin/env python3
"""Validate the 2026-10-12 editorial review without changing feeds or articles."""
from pathlib import Path
from html.parser import HTMLParser
import subprocess,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent
BASE='https://globtechco.github.io/ttn-finans/'
class Page(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.meta={};self.canonical=[];self.h1=[];self.hero=[];self.scripts=[];self.in_h1=False;self.current='';self.jsonld=[];self.in_json=False;self.data='';self.paras=[];self.in_body=False;self.in_p=False;self.para=''
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if t=='meta':self.meta[a.get('property',a.get('name',''))]=a.get('content','')
  if t=='link' and a.get('rel')=='canonical':self.canonical.append(a['href'])
  if t=='h1':self.in_h1=True;self.current=''
  if t=='section' and a.get('class')=='editorial-body':self.in_body=True
  if t=='p' and self.in_body:self.in_p=True;self.para=''
  if t=='img' and 'article-hero-image' in a.get('class',''):self.hero.append(a)
  if t=='script' and a.get('src'):self.scripts.append(a['src'])
  if t=='script' and a.get('type')=='application/ld+json':self.in_json=True;self.data=''
 def handle_endtag(self,t):
  if t=='h1' and self.in_h1:self.h1.append(self.current);self.in_h1=False
  if t=='section' and self.in_body:self.in_body=False
  if t=='p' and self.in_p:self.paras.append(self.para);self.in_p=False
  if t=='script' and self.in_json:self.jsonld.append(json.loads(self.data));self.in_json=False
 def handle_data(self,d):
  if self.in_h1:self.current+=d
  if self.in_p:self.para+=d
  if self.in_json:self.data+=d

def main():
 raw=(ROOT/'articles.js').read_text();catalog=json.loads(raw.split('const TTN_ARTICLES = ',1)[1].strip().removesuffix(';'))
 report=json.loads((ROOT/'scripts/editorial-review-20261012.json').read_text())
 assert len(catalog)==len({a['id'] for a in catalog})==88
 assert {a['id'] for a in catalog}=={a['article'] for a in report['articles']}
 sitemap={e.text for e in ET.parse(ROOT/'sitemap.xml').getroot().iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
 baseline=json.loads(subprocess.check_output(['node','-e',"const vm=require('vm'),fs=require('fs'),cp=require('child_process');let x={};vm.createContext(x);vm.runInContext(cp.execFileSync('git',['show','723a6b4:articles.js'],{encoding:'utf8'})+';this.a=TTN_ARTICLES;',x);console.log(JSON.stringify(x.a));"],cwd=ROOT))
 old={a['id']:a for a in baseline}
 for a in catalog:
  path=ROOT/(a['id']+'.html');html=path.read_text();p=Page();p.feed(html)
  assert p.h1==[a['title']],a['id']
  assert p.paras==a['body'],a['id']
  assert p.canonical==[BASE+a['id']+'.html'],a['id']
  assert BASE+a['id']+'.html' in sitemap,a['id']
  for k in ['description','og:description','twitter:description']:assert p.meta[k]==a['dek'],(a['id'],k)
  for k in ['og:title','twitter:title']:assert p.meta[k]==a['title'],(a['id'],k)
  assert len(p.hero)==1 and p.hero[0]['src']==old[a['id']]['image'],a['id']
  assert a['tickers']==old[a['id']]['tickers'] and a['date']==old[a['id']]['date'],a['id']
  assert (ROOT/a['image']).is_file()
  assert p.meta['og:image']==p.meta['twitter:image']==BASE+a['image']
  assert p.jsonld[0]['headline']==a['title'] and p.jsonld[0]['dateModified']==a['dateModified']
  assert p.jsonld[0]['citation']==[s['url'] for s in a['sources']]
  assert 'root=document.getElementById' not in html
  assert 'chart.js?v=article-click-fix-20261012' in p.scripts
  assert all(x not in ' '.join(a['body']).lower() for x in ['practical takeaway','genuinely worth','ttn\'s own'])
 for filename in ['news.js','config.js','app.js','tickers.js','chart.js','market-tape.js','calculators.js','calculators.html']:
  assert (ROOT/filename).read_bytes()==subprocess.check_output(['git','show','723a6b4:'+filename],cwd=ROOT),filename
 print('PASS: 88 static articles and catalogue texts match; titles, descriptions, schemas and sitemap agree; images, tickers, publication dates, calculators and aggregator preserved.')
if __name__=='__main__':main()
