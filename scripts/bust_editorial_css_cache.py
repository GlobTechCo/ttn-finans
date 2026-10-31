"""Version shared CSS files on all HTML pages without editing their content."""
from pathlib import Path
import re

STYLES = {
    "editorial-theme.css": "20261031-dark-readability-v3",
    "article-share.css": "20261031-compact-v2",
    "footer.css": "20261031-site-contrast-v3",
}

changed = 0
for path in Path(".").rglob("*.html"):
    if ".git" in path.parts or "node_modules" in path.parts:
        continue
    original = path.read_text(encoding="utf-8")
    current = original
    for filename, version in STYLES.items():
        pattern = r'(href=["\\\'])' + re.escape(filename) + r'(?:\\?[^"\\\']*)?(["\\\'])'
        current = re.sub(pattern, lambda m: m.group(1) + filename + "?v=" + version + m.group(2), current)
    if current != original:
        path.write_text(current, encoding="utf-8")
        changed += 1
        print("Updated", path)
print("Updated HTML pages:", changed)
