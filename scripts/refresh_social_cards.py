"""Keep static social metadata aligned with local covers and immutable image URLs.

Run after changing article images. Existing social URLs stay available for old posts.
The source filename plus a content digest changes only when its image changes.
"""
from pathlib import Path
from html.parser import HTMLParser
import hashlib, html, io, json, re, subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://globtechco.github.io/ttn-finans/'
IMAGE_TAGS = {'og:image', 'og:image:secure_url', 'og:image:type', 'og:image:width',
              'og:image:height', 'og:image:alt', 'twitter:image', 'twitter:image:alt'}

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.canonical = None
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'meta':
            self.meta[values.get('name', values.get('property', ''))] = values.get('content', '')
        if tag == 'link' and values.get('rel') == 'canonical':
            self.canonical = values.get('href')

def image_bytes(source):
    data = (ROOT / source).read_bytes()
    try:
        image = Image.open(io.BytesIO(data)); image.load()
    except (OSError, ValueError):
        # A damaged uncommitted local file must not replace a valid published cover.
        data = subprocess.check_output(['git', 'show', 'HEAD:' + source], cwd=ROOT)
        image = Image.open(io.BytesIO(data)); image.load()
    return data, image

def refresh():
    catalog = json.loads((ROOT / 'articles.js').read_text().split('const TTN_ARTICLES = ', 1)[1].strip().removesuffix(';'))
    articles = {article['id'] + '.html': article for article in catalog}
    records = []
    target = ROOT / 'assets/social'; target.mkdir(exist_ok=True)
    for page in sorted(ROOT.glob('*.html')):
        text = page.read_text()
        if 'editorial-theme.js' not in text:
            continue
        metadata = Metadata(); metadata.feed(text)
        old_url = metadata.meta.get('twitter:image', metadata.meta.get('og:image', ''))
        if page.name in articles:
            source = articles[page.name]['image']
        elif old_url.startswith(BASE):
            source = old_url.removeprefix(BASE).split('?', 1)[0]
            # A second run uses the original recorded source, rather than nesting hashes.
            previous = ROOT / 'scripts/social-card-manifest.json'
            if source.startswith('assets/social/') and previous.exists():
                old_records = json.loads(previous.read_text())['pages']
                source = next((r['source'] for r in old_records if r['page'] == page.name), source)
        else:
            source = 'assets/social/ttn-finance-card.png'
        data, image = image_bytes(source)
        digest = hashlib.sha256(data).hexdigest()
        extension = '.' + image.format.lower()
        filename = Path(source).stem + '-' + digest[:12] + extension
        destination = target / filename
        if not destination.exists() or destination.read_bytes() != data:
            destination.write_bytes(data)
        url = BASE + 'assets/social/' + filename
        alt = ('TTN Finance — Markets. Technology. Global Economy.' if source.endswith('ttn-finance-card.png') else
               metadata.meta.get('twitter:image:alt', metadata.meta.get('og:image:alt', articles.get(page.name, {}).get('title', 'TTN Finance editorial image'))))
        mime = Image.MIME[image.format]
        def remove_image_tag(match):
            parsed = Metadata(); parsed.feed(match.group())
            return '' if IMAGE_TAGS.intersection(parsed.meta) else match.group()
        text = re.sub(r'[ \t]*<meta\b[^>]*>[ \t]*\r?\n?', remove_image_tag, text, flags=re.I)
        tags = [('property', 'og:image', url), ('property', 'og:image:secure_url', url),
                ('property', 'og:image:type', mime), ('property', 'og:image:width', str(image.width)),
                ('property', 'og:image:height', str(image.height)), ('property', 'og:image:alt', alt),
                ('name', 'twitter:image', url), ('name', 'twitter:image:alt', alt)]
        # Contact and future section pages receive a complete card, too.
        title = html.unescape(re.search(r'<title>(.*?)</title>', text, re.S).group(1))
        description = metadata.meta.get('description', '')
        for attr, key, value in [('name', 'twitter:card', 'summary_large_image'),
                                 ('name', 'twitter:title', title), ('name', 'twitter:description', description),
                                 ('property', 'og:title', title), ('property', 'og:description', description),
                                 ('property', 'og:type', 'website'), ('property', 'og:url', metadata.canonical or BASE + page.name)]:
            if key not in metadata.meta:
                tags.append((attr, key, value))
        block = '\n'.join(f'<meta {attr}="{key}" content="{html.escape(value, quote=True)}">' for attr, key, value in tags)
        text = text.replace('</head>', block + '\n</head>')
        page.write_text(text)
        records.append({'page': page.name, 'source': source, 'image': 'assets/social/' + filename,
                        'sha256': digest, 'width': image.width, 'height': image.height,
                        'bytes': len(data), 'type': mime,
                        'shareUrl': BASE + page.name + '?card=' + digest[:12]})
    (ROOT / 'scripts/social-card-manifest.json').write_text(json.dumps({'pages': records}, indent=2) + '\n')
    print(f'Updated {len(records)} pages; {len({r["image"] for r in records})} immutable card images.')

if __name__ == '__main__':
    refresh()
