#!/usr/bin/env python3
"""Apply reviewed search titles/descriptions without changing visible headlines."""
from pathlib import Path
from html.parser import HTMLParser
import html,re
from seo_metadata import TITLES, DESCRIPTIONS
ROOT=Path(__file__).resolve().parents[1]
class Meta(HTMLParser):
    def __init__(self):super().__init__();self.meta={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content','')
def refresh():
    changed=0
    for page in ROOT.glob('*.html'):
        text=page.read_text();old=text
        if page.stem in TITLES:
            title=html.escape(TITLES[page.stem]+' | TTN Finance')
            text=re.sub(r'<title>.*?</title>',lambda m:'<title>'+title+'</title>',text,flags=re.S)
        if page.stem in DESCRIPTIONS:
            description=DESCRIPTIONS[page.stem]
            def metadata(match):
                parser=Meta();parser.feed(match.group())
                if {'description','og:description','twitter:description'}.intersection(parser.meta):
                    return re.sub(r'''\bcontent\s*=\s*(["']).*?\1''',lambda m:'content="'+html.escape(description,quote=True)+'"',match.group(),flags=re.S)
                return match.group()
            text=re.sub(r'<meta\b[^>]*>',metadata,text,flags=re.I)
        text=re.sub(r'editorial-related\.css(?:\?[^"\s>]*)?', 'editorial-related.css?v=audit-20261018',text)
        if text!=old:page.write_text(text);changed+=1
    print(f'Refreshed search metadata/style references on {changed} pages.')
if __name__=='__main__':refresh()
