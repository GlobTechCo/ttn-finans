"""Apply approved cover replacement packages without editing article text."""
from pathlib import Path
import io
import json
import re
import sys
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SLUG_RX = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')

def apply_one(archive_name):
    with zipfile.ZipFile(archive_name) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or 'cover-replacement.json' not in names:
            raise ValueError('Missing manifest or duplicate ZIP member')
        metadata = json.loads(archive.read('cover-replacement.json'))
        slug = metadata['slug']
        if not SLUG_RX.fullmatch(slug):
            raise ValueError('Invalid slug')
        page = ROOT / (slug + '.html')
        if not page.is_file():
            raise ValueError('Article page not found: ' + slug)
        expected = {
            'assets/editorial/' + slug + '-cover-v2.webp': (1672, 941),
            'assets/responsive/' + slug + '-cover-v2-960.webp': (960, 540),
            'assets/responsive/' + slug + '-cover-v2-480.webp': (480, 270),
        }
        if set(names) != set(expected) | {'cover-replacement.json'}:
            raise ValueError('Unexpected ZIP contents')
        for name, size in expected.items():
            image = Image.open(io.BytesIO(archive.read(name)))
            image.load()
            if image.format != 'WEBP' or image.size != size:
                raise ValueError('Invalid cover dimensions: ' + name)
            if (ROOT / name).exists():
                raise ValueError('Image version already exists: ' + name)
        old = slug + '-cover-v1'
        new = slug + '-cover-v2'
        edits = {}
        for path in [ROOT / 'articles.js', ROOT / 'article-cards.js', page]:
            text = path.read_text(encoding='utf-8')
            if old not in text:
                raise ValueError('Original cover reference not found: ' + path.name)
            edits[path] = text.replace(old, new)
        for name in expected:
            destination = ROOT / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(name))
        for path, text in edits.items():
            path.write_text(text, encoding='utf-8')
        print('Approved cover replaced for', slug)

if __name__ == '__main__':
    for item in sys.argv[1:]:
        apply_one(item)
