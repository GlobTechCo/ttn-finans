"""Refresh stylesheet query versions for all published editorial HTML pages.

Run only on article pages. Leave editorial text, metadata and other assets unchanged.
"""
from pathlib import Path
import re

VERSION = {
    "editorial-theme.css": "20261031-readability-v2",
    "article-share.css": "20261031-compact-v2",
    "footer.css": "20261031-contrast-v2",
}

def main():
    count = 0
    for path in Path(".").rglob("*.html"):
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if not re.search(r'class\\s*=\\s*["\\\']editorial-body["\\\']', text):
            continue
        revised = text
        for filename, version in VERSION.items():
            pattern = r'(href=["\\\'])' + re.escape(filename) + r'(?:\\?[^"\\\']*)?(["\\\'])'
            revised = re.sub(pattern, lambda m: m.group(1) + filename + "?v=" + version + m.group(2), revised)
        if revised != text:
            path.write_text(revised, encoding="utf-8")
            count += 1
            print("Updated:", path)
    print("Article HTML pages updated:", count)

if __name__ == "__main__":
    main()
