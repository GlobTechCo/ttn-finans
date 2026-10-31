"""Bump CSS URLs across published article HTML pages without changing content."""
from pathlib import Path
import re

STYLES = {
    "editorial-theme.css": "20261031-dark-readability-v3",
    "article-share.css": "20261031-compact-v2",
    "footer.css": "20261031-contrast-v2",
}

changed = 0
for path in Path(".").rglob("*.html"):
    if ".git" in path.parts or "node_modules" in path.parts:
        continue
    original = path.read_text(encoding="utf-8")
    if 'class="editorial-body"' not in original:
        continue
    current = original
    for filename, version in STYLES.items():
        pattern = 'href="' + re.escape(filename) + '(?:\\?[^"]*)?"'
        current = re.sub(pattern, 'href="' + filename + '?v=' + version + '"', current)
    if current != original:
        path.write_text(current, encoding="utf-8")
        changed += 1
        print("Updated", path)
print("Updated article pages:", changed)
