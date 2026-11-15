#!/usr/bin/env python3
"""Normalize Gemini's dated three-article folder package to TTN's importer schema."""
import json, re, sys, zipfile
from datetime import date
from pathlib import Path
from lxml import html, etree

archive_path = Path(sys.argv[1])
root = Path.cwd()
base = "https://globtechco.github.io/ttn-finans/"
package = "ttn-finans-publication-package/"
sections = {"Market Analysis":"Market Analysis","Tech & AI":"Tech & AI","Crypto":"Crypto"}
seo_fallback = {
 "eba-explores-alternatives-eu-deposit-insurance-cross-border-banking-november-2026": {
  "seoTitle":"EU Explores Alternatives to Common Deposit Insurance | TTN Finance",
  "metaDescription":"EU regulators are weighing parent-bank guarantees, branch structures and a two-tier safety net as political disputes stall common deposit insurance.",
  "dek":"European regulators are examining narrower ways to support cross-border banks as disagreement continues to block a common EU deposit insurance system."
 }
}
with zipfile.ZipFile(archive_path, "r") as src:
    raw = {n[len(package):]: src.read(n) for n in src.namelist() if n.startswith(package) and not n.endswith("/")}
articles = []
for name, data in list(raw.items()):
    if not name.endswith("-seo.json"): continue
    meta = json.loads(data.decode("utf-8"))
    slug = meta["slug"]
    section = meta["section"]
    # Never invent a publication clock time. Prefer a date supplied in the approved metadata.
    published_date = str(meta.get("publishedAt") or meta.get("datePublished") or meta.get("date") or date.today().isoformat()).split("T", 1)[0]
    fallback = seo_fallback.get(slug, {})
    title = meta["headline"]
    seo_title = meta.get("seoTitle") or fallback.get("seoTitle") or (title[:48].rsplit(" ",1)[0] + " | TTN Finance")
    description = meta.get("metaDescription") or fallback.get("metaDescription")
    fragment_name = slug + "-fragment.html"
    fragment = raw[fragment_name].decode("utf-8")
    frag = html.fromstring("<div>" + fragment + "</div>")
    dek_node = frag.xpath(".//*[contains(concat(' ',normalize-space(@class),' '),' editorial-dek ')]")
    dek = " ".join(dek_node[0].itertext()).strip() if dek_node else ""
    if not dek: dek = fallback.get("dek") or description
    body_nodes = frag.xpath(".//*[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]")
    if len(body_nodes) != 1: raise SystemExit("Missing editorial body for " + slug)
    body_html = html.tostring(body_nodes[0], encoding="unicode")
    cover = "assets/editorial/" + slug + "-cover.webp"
    small = "assets/responsive/" + slug + "-cover-480.webp"
    medium = "assets/responsive/" + slug + "-cover-960.webp"
    # Use a live TTN article as the structural template; all editorial content below is replaced.
    template = html.parse(str(root / "private-credit-shadow-banking-explained.html"))
    doc = template
    head = doc.xpath("//head")[0]
    def set_meta(selector, attr, value):
        nodes = head.xpath(selector)
        if nodes: nodes[0].set(attr, value)
        else:
            node = html.Element("meta")
            node.set(attr, value)
            head.append(node)
    canon = base + slug + ".html"
    title_nodes = head.xpath("./title")
    if title_nodes: title_nodes[0].text = seo_title
    else: etree.SubElement(head, "title").text = seo_title
    set_meta('//meta[@name="description"]', "content", description)
    set_meta('//meta[@property="og:title"]', "content", title)
    set_meta('//meta[@property="og:description"]', "content", description)
    set_meta('//meta[@property="og:url"]', "content", canon)
    set_meta('//meta[@name="twitter:title"]', "content", title)
    set_meta('//meta[@name="twitter:description"]', "content", description)
    published_nodes = head.xpath('./meta[@property="article:published_time"]')
    if published_nodes: published_nodes[0].set("content", published_date)
    else: etree.SubElement(head, "meta", property="article:published_time", content="2026-11-15T10:00:00+00:00")
    canon_nodes = head.xpath('./link[@rel="canonical"]')
    if canon_nodes: canon_nodes[0].set("href", canon)
    else: etree.SubElement(head, "link", rel="canonical", href=canon)
    robots = head.xpath('./meta[@name="robots"]')
    if robots: robots[0].set("content","index,follow,max-image-preview:large")
    scripts = head.xpath('./script[@type="application/ld+json"]')
    structured = json.loads(scripts[0].text) if scripts and scripts[0].text else {}
    structured.update({"@context":"https://schema.org","@type":"Article","headline":title,"description":description,"datePublished":"2026-11-15T10:00:00+00:00","dateModified":"2026-11-15T10:00:00+00:00","inLanguage":"en-US","articleSection":section,"mainEntityOfPage":{"@type":"WebPage","@id":canon},"author":{"@type":"Organization","name":"TTN Research Desk"},"publisher":{"@type":"Organization","name":"TTN Finance","url":base}})
    if scripts: scripts[0].text = json.dumps(structured, ensure_ascii=False)
    else:
        sc=etree.SubElement(head,"script",type="application/ld+json");sc.text=json.dumps(structured,ensure_ascii=False)
    main = doc.xpath("//main")[0]
    for child in list(main): main.remove(child)
    main.set("id","main-content"); main.set("class","static-page"); main.set("tabindex","-1")
    nav=etree.SubElement(main,"p"); a=etree.SubElement(nav,"a",href={"Market Analysis":"analysis.html","Tech & AI":"tech-ai.html","Crypto":"crypto.html"}[section]); a.text="← "+section
    badge=etree.SubElement(main,"span",attrib={"class":"ttn-original-badge"}); badge.text=section
    h1=etree.SubElement(main,"h1"); h1.text=title
    d=etree.SubElement(main,"p",attrib={"class":"article-dek"}); d.text=dek
    by=etree.SubElement(main,"p",attrib={"class":"editorial-meta","data-editorial-byline":"","data-author":"TTN Research Desk"})
    sp=etree.SubElement(by,"span",attrib={"class":"editorial-author"}); sp.text="TTN Research Desk"
    pub=etree.SubElement(by,"span",attrib={"class":"editorial-published"})
    tm=etree.SubElement(pub,"time",datetime="2026-11-15T10:00:00+00:00"); tm.text="Nov 15, 2026"
    fig=etree.SubElement(main,"figure",attrib={"class":"ttn-editorial-figure"})
    img=etree.SubElement(fig,"img",src=cover,alt=title,attrib={"class":"article-hero-image","width":"1672","height":"941","loading":"eager","fetchpriority":"high"})
    img.set("srcset",small+" 480w, "+medium+" 960w, "+cover+" 1672w"); img.set("sizes","(max-width: 900px) calc(100vw - 36px), 820px")
    body=html.fromstring(body_html)
    body.tag="section"
    body.set("class","editorial-body")
    main.append(body)
    raw[slug+".html"] = html.tostring(doc, encoding="utf-8", method="html", doctype="<!DOCTYPE html>")
    articles.append({"slug":slug,"title":title,"dek":dek,"section":section,"format":"news" if slug.startswith("bitcoin-") or slug.startswith("eba-") else "analysis","date":"2026-11-15T10:00:00+00:00","cover":cover})
    # Move package images into the importer's canonical asset folders.
    stem = slug + "-cover"
    for suffix, dest in [("-cover.webp","assets/editorial/"+slug+"-cover.webp"),("-480.webp","assets/responsive/"+slug+"-cover-480.webp"),("-960.webp","assets/responsive/"+slug+"-cover-960.webp")]:
        key=slug+suffix
        if key not in raw: raise SystemExit("Missing image " + key)
        raw[dest]=raw.pop(key)
    raw.pop(fragment_name, None)
    raw.pop(name, None)
if len(articles)!=3: raise SystemExit("Expected exactly 3 article SEO records")
raw["publication-manifest.json"]=json.dumps(articles,ensure_ascii=False,indent=2).encode()
# The source ZIP's README is informational only and is not imported.
for key in list(raw):
    if key.endswith("README.txt"): raw.pop(key)
tmp=archive_path.with_suffix(".normalized.zip")
with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_DEFLATED) as out:
    for name,data in raw.items(): out.writestr(name,data)
tmp.replace(archive_path)
print("Normalized ZIP:", archive_path, "articles:", len(articles), "entries:", len(raw))
