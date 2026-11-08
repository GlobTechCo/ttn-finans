#!/usr/bin/env python3
"""Safely import an approved TTN ZIP package; run site regeneration afterwards."""
import datetime
import html as html_std
import json
import re
import re
import sys
import zipfile
from pathlib import Path
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://globtechco.github.io/ttn-finans/"
slug_re = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
topic = {"Market Analysis": "Jobs and housing", "Tech & AI": "AI investment, infrastructure and productivity", "Crypto": "Crypto, stablecoins and market structure"}

def check(condition, message):
    if not condition:
        raise ValueError(message)

def publish(archive):
    archive = Path(archive)
    check(archive.stat().st_size <= 30_000_000, "ZIP exceeds 30 MB")
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        check(len(names) == len(set(names)) and len(names) <= 100, "Duplicate or excessive ZIP entries")
        check(sum(i.file_size for i in z.infolist()) <= 100_000_000, "Expanded ZIP too large")
        for i in z.infolist():
            p = Path(i.filename)
            safe = i.filename in ("publication-manifest.json", "README-PUBLISH.txt")
            safe |= len(p.parts) == 1 and p.suffix == ".html" and bool(slug_re.fullmatch(p.stem))
            safe |= len(p.parts) == 3 and p.parts[0] == "assets" and p.parts[1] in ("social", "editorial", "responsive") and p.suffix.lower() in (".webp", ".png", ".jpg") and bool(slug_re.fullmatch(p.stem))
            check(safe and not i.is_dir() and ".." not in p.parts and "\\" not in i.filename, "Unsafe ZIP entry: " + i.filename)
        manifest = json.loads(z.read("publication-manifest.json"))
        check(isinstance(manifest, list) and 1 <= len(manifest) <= 12, "Manifest needs 1 to 12 articles")
        catalog_path = ROOT / "articles.js"
        catalog = json.loads(catalog_path.read_text().split("=", 1)[1].strip().removesuffix(";"))
        existing = {a["id"] for a in catalog}
        entries = []
        relations = {}
        for m in manifest:
            slug = m["slug"]
            check(isinstance(slug, str) and bool(slug_re.fullmatch(slug)), "Invalid article slug")
            check(slug not in existing and slug not in relations, "Existing or duplicate article: " + slug)
            check(m["section"] in topic and m["format"] in ("news", "analysis", "explainer"), "Invalid editorial section or format")
            check(datetime.datetime.fromisoformat(m["date"].replace("Z", "+00:00")).tzinfo is not None, "Date needs UTC offset")
            file = slug + ".html"
            cover = m["cover"]
            check(file in names and cover in names and cover.startswith("assets/editorial/" + slug + "-"), "Article/cover missing")
            doc = html.fromstring(z.read(file))
            check(doc.xpath("//link[@rel='canonical']/@href") == [BASE + file], "Wrong canonical URL: " + slug)
            check(doc.xpath("//meta[@property='article:published_time']/@content") == [m["date"]], "Date mismatch: " + slug)
            check(["".join(h.itertext()).strip() for h in doc.xpath("//h1")] == [m["title"]], "Headline mismatch: " + slug)
            body_nodes = doc.xpath("//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]")
            check(len(body_nodes) == 1, "No editorial body: " + slug)
            word_count = sum(len(" ".join(p.itertext()).split()) for p in body_nodes[0].xpath("./p"))
            check(word_count >= 700, "Article shorter than 700 words: " + slug)
            # An end-of-article Related reading block alone is not contextual linking.
            # Require at least two distinct TTN Finance article links within body paragraphs.
            inline_links = [
                href for href in body_nodes[0].xpath(".//p//a/@href")
                if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*[.]html", href or "")
            ]
            check(len(set(inline_links)) >= 2, "Missing contextual TTN Finance links inside the article body: " + slug)
            for href in set(inline_links):
                check((ROOT / href).is_file() or href in names, "Unknown internal article link: " + href)

            check(doc.xpath("//figure[contains(@class,'ttn-editorial-figure')]//img/@src") == [cover], "Cover mismatch: " + slug)
            alt = doc.xpath("//figure[contains(@class,'ttn-editorial-figure')]//img/@alt")
            check(bool(alt and alt[0]), "Missing image alt text: " + slug)
            stem = Path(cover).stem
            sm = "assets/responsive/" + stem + "-480.webp"
            md = "assets/responsive/" + stem + "-960.webp"
            check(sm in names and md in names, "Responsive images missing: " + slug)
            related = m.get("related", [])
            check(isinstance(related, list) and all(isinstance(s, str) and slug_re.fullmatch(s) for s in related), "Invalid related reading")
            relations[slug] = related
            # Short SEO titles are required by the static-site audit. Preserve the visible H1.
            seo_suffix = " | TTN Finance"
            seo_title = m["title"]
            if len(seo_title + seo_suffix) > 65:
                available = 65 - len(seo_suffix)
                seo_title = seo_title[:available].rsplit(" ", 1)[0].rstrip(" ,:;-")
            check(len(seo_title) > 12, "SEO title cannot be shortened: " + slug)
            new_title = html_std.escape(seo_title + seo_suffix)
            original_html = z.read(file).decode("utf-8")
            # Editorial correction to the November 7 Michigan SEO summary. The
            # archived 161-character sentence breached the site's 160-character
            # limit; preserve the article body and all approved images unchanged.
            if slug == "us-november-consumer-sentiment-51-inflation-ai-bubble-2026":
                old_summary = "The University of Michigan's preliminary November index rose three points, while inflation expectations eased and worries about living costs remained widespread."
                new_summary = "The University of Michigan's preliminary November index rose three points, as inflation expectations eased despite lingering cost concerns."
                original_html = original_html.replace(html_std.escape(old_summary, quote=True), html_std.escape(new_summary, quote=True))
            # The publication manifest is the approved source of the section.
            # Correct mismatched JSON-LD inside the packaged page before auditing.
            # Keep the site-wide verifier strict so later metadata regressions fail.
            jsonld_pattern = re.compile(
                r'(<script[^>]+application/ld[+]json[^>]*>)(.*?)(</script>)',
                flags=re.I | re.S,
            )
            corrected_section = False

            def align_section(match):
                nonlocal corrected_section
                structured = json.loads(match.group(2))
                if not isinstance(structured, dict) or "articleSection" not in structured:
                    return match.group(0)
                corrected_section = True
                if structured["articleSection"] == m["section"]:
                    return match.group(0)
                structured["articleSection"] = m["section"]
                return match.group(1) + json.dumps(structured, ensure_ascii=False) + match.group(3)

            original_html = jsonld_pattern.sub(align_section, original_html)
            check(corrected_section, "Missing articleSection JSON-LD: " + slug)
            # Validate SEO metadata before committing imported files.
            checked_doc = html.fromstring(original_html)
            summaries = checked_doc.xpath('//meta[@name="description"]/@content')
            check(len(summaries) == 1 and 70 <= len(summaries[0]) <= 160, "Invalid SEO meta description (70-160 chars): " + slug)
            # Apply the existing responsive 16:9 article image styles to every imported cover.
            # Preserve pre-existing image classes; avoid duplicate class attributes.
            if '<figure class="ttn-editorial-figure"><img class=' not in original_html:
                original_html = original_html.replace(
                    '<figure class="ttn-editorial-figure"><img ',
                    '<figure class="ttn-editorial-figure"><img class="article-hero-image" ',
                    1,
                )
            original_html = re.sub(r"<title>.*?</title>", "<title>" + new_title + "</title>", original_html, count=1, flags=re.S)
            # The site has an inline financial disclaimer, not disclaimer.html.
            # Remove this obsolete footer link rather than introducing a dead URL.
            original_html = original_html.replace(' · <a href="disclaimer.html">Disclaimer</a>', '')
            # These bytes replace the packaged HTML after full archive validation.
            relations[slug + ":validated-html"] = original_html
            entries.append(dict(
                id=slug, title=m["title"], dek=m["dek"], section=m["section"], format=m["format"],
                date=m["date"], author="TTN Research Desk", tickers=m.get("tickers", []),
                image=cover, imageSmall=sm, imageMedium=md,
                imageSrcset=sm + " 480w, " + md + " 960w, " + cover + " 1672w",
                imageAlt=alt[0], body=[html.tostring(el, encoding="unicode") for el in body_nodes[0]],
                sources=[]
            ))
        all_ids = existing | {a["id"] for a in entries}
        check(all(r in all_ids for slug, refs in relations.items() if not slug.endswith(":validated-html") for r in refs), "Related reading points to missing articles")
        # Refuse all collisions before writing any files.
        for name in names:
            if name in ("publication-manifest.json", "README-PUBLISH.txt"):
                continue
            dest = ROOT / name
            check(not dest.exists() or dest.read_bytes() == z.read(name), "Would overwrite published file: " + name)
        for name in names:
            if name in ("publication-manifest.json", "README-PUBLISH.txt"):
                continue
            dest = ROOT / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                if name.endswith(".html") and (name[:-5] + ":validated-html") in relations:
                    dest.write_text(relations[name[:-5] + ":validated-html"], encoding="utf-8")
                else:
                    dest.write_bytes(z.read(name))
        catalog.extend(entries)
        catalog_path.write_text("const TTN_ARTICLES = " + json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + ";\n")
        path = ROOT / "scripts/editorial_topics.py"
        with path.open("a") as out:
            out.write("\n# Approved ZIP auto-publication\n")
            for a in entries:
                out.write("GROUPS.setdefault(" + repr(topic[a["section"]]) + ", []).append(" + repr(a["id"]) + ")\n")
                out.write("RELATED[" + repr(a["id"]) + "] = " + repr(relations[a["id"]]) + "\n")
        print("Imported", len(entries), "articles from", archive)

if __name__ == "__main__":
    for file in sys.argv[1:]:
        publish(file)
