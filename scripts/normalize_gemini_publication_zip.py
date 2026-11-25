#!/usr/bin/env python3
"""Normalize Gemini's dated three-article folder package to TTN's importer schema."""
import json, re, sys, zipfile
from io import BytesIO
from PIL import Image
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from lxml import html, etree

archive_path = Path(sys.argv[1])

# Native TTN publication packages already use the importer's canonical schema.
# Preserve the approved article HTML and cover bytes exactly; only legacy Gemini
# folder packages should pass through the transformation logic below.
with zipfile.ZipFile(archive_path, "r") as canonical_zip:
    canonical_names = set(canonical_zip.namelist())
    if "publication-manifest.json" in canonical_names:
        canonical_manifest = json.loads(canonical_zip.read("publication-manifest.json"))
        if not isinstance(canonical_manifest, list) or not 1 <= len(canonical_manifest) <= 12:
            raise SystemExit("Invalid canonical publication manifest: expected 1 to 12 article records.")
        for item in canonical_manifest:
            slug = item.get("slug", "")
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                raise SystemExit("Invalid canonical article slug: " + str(slug))
            if slug + ".html" not in canonical_names:
                raise SystemExit("Canonical package is missing article HTML: " + slug + ".html")
            cover = item.get("cover", "")
            if cover not in canonical_names or not cover.startswith("assets/editorial/" + slug + "-"):
                raise SystemExit("Canonical package is missing its matching editorial cover: " + str(cover))
            for suffix in ("-480.webp", "-960.webp"):
                responsive = "assets/responsive/" + Path(cover).stem + suffix
                if responsive not in canonical_names:
                    raise SystemExit("Canonical package is missing responsive image: " + responsive)
        print("Native TTN publication package detected; preserving approved HTML and image bytes unchanged.")
        raise SystemExit(0)
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
source_fallback = {
 "bitcoin-four-month-low-crypto-liquidations-november-2026": [{"label":"Business Standard (Bloomberg), Bitcoin tumbles to four-month low as leveraged bets face mass liquidations","url":"https://www.business-standard.com/markets/cryptocurrency/bitcoin-tumbles-to-four-month-low-as-leveraged-bets-face-mass-liquidations-126111500058_1.html"}],
 "eba-explores-alternatives-eu-deposit-insurance-cross-border-banking-november-2026": [{"label":"Financial Times, EU banking watchdog veers away from single deposit insurance scheme","url":"https://www.ft.com/content/016ce22d-1e09-4f1d-a7e6-9acf183e757f"},{"label":"European Commission, European deposit insurance scheme","url":"https://finance.ec.europa.eu/banking/banking-union/european-deposit-insurance-scheme_en"},{"label":"EUR-Lex, Directive 2014/49/EU on deposit guarantee schemes","url":"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0049"}],
 "samsung-ai-data-center-infrastructure-expansion-november-2026": [{"label":"Financial Times, Samsung conquered AI chips. Now it wants to build data centres","url":"https://www.ft.com/content/ee5b23b3-89b3-41f7-9158-56c1586759c2"},{"label":"Samsung Global Newsroom, Samsung to invest USD 1 billion in Helix","url":"https://news.samsung.com/global/samsung-to-invest-usd-1-billion-in-ai-infrastructure-company-helix"},{"label":"Helix Digital Infrastructure, Samsung commits USD 1 billion to Helix","url":"https://www.helixdi.com/news-insights/samsung-commits-1-billion-to-helix-digital-infrastructure-to-support-global-ai-infrastructure-buildout/"}],
 "wall-street-sell-off-deepens-dow-plunges-1100-points-ai-fears-spread-november-20-2026": [{"label":"Associated Press, How major US stock indexes fared Thursday 11/19/2026","url":"https://apnews.com/article/2f178054aea79d282e5ccf8d62f26a28"},{"label":"Reuters, Wall Street ends sharply lower as Anthropic's debut fails to revive AI fervor","url":"https://www.investing.com/news/stock-market-news/wall-street-ends-sharply-lower-asanthropics-debut-fails-to-revive-ai-fervor-5040108"}],
 "alibaba-ai-cloud-revenue-jumps-53-infrastructure-spending-cash-flow-november-20-2026": [{"label":"Alibaba Group, September Quarter 2026 Results","url":"https://home.alibabagroup.com/en-US/document-2060213191907999744"},{"label":"U.S. Securities and Exchange Commission, Alibaba September Quarter 2026 Results","url":"https://www.sec.gov/Archives/edgar/data/1577552/000110465926130115/tm2630263d1_ex99-1.htm"}],
 "eu-gives-czechia-spain-two-months-crypto-tax-reporting-rules-dac8-november-20-2026": [{"label":"European Commission, November 2026 Infringement Package","url":"https://ec.europa.eu/commission/presscorner/api/files/document/print/en/inf_26_2269/INF_26_2269_EN.pdf"},{"label":"European Commission, DAC8: Tax transparency for crypto-assets","url":"https://taxation-customs.ec.europa.eu/taxation/tax-transparency-cooperation/administrative-co-operation-and-mutual-assistance/directive-administrative-cooperation-dac/dac8_en"}],
 "global-stocks-ai-selloff-9-trillion-november-21-2026": [{"label":"Reuters via Yahoo Finance, The snowballing selloff in global markets","url":"https://finance.yahoo.com/markets/articles/snowballing-selloff-global-markets-151205233.html"},{"label":"Reuters via Investing.com, The snowballing selloff in global markets","url":"https://au.investing.com/news/economy-news/the-snowballing-selloff-in-global-markets-4787059"}],
 "trump-data-center-tax-threat-ai-infrastructure-november-21-2026": [{"label":"Associated Press, Trump threatens tax on US companies building data centers overseas","url":"https://apnews.com/article/f1ac03b73d13445400eeed8631d9d879"},{"label":"Axios, Trump floats taxing U.S. companies constructing data centers overseas","url":"https://www.axios.com/2026/11/20/us-ai-trump-data-centers-overseas"}],
 "bitcoin-two-year-low-55830-ai-market-selloff-november-21-2026": [{"label":"Reuters, Bitcoin falls to its lowest in two years","url":"https://www.reuters.com/business/bitcoin-falls-357-56814-2026-11-21/"},{"label":"Reuters via Business Recorder, Bitcoin falls 5.10% to $55,830","url":"https://www.brecorder.com/news/40450104"}]
}
with zipfile.ZipFile(archive_path, "r") as src:
    raw = {n[len(package):]: src.read(n) for n in src.namelist() if n.startswith(package) and not n.endswith("/")}
    flat_package = not bool(raw)
    # Gemini may keep the canonical article covers inside covers/ or assets/editorial/.
    # The importer consumes slug-cover.webp at the package root, so expose those
    # exact-named assets without changing or recompressing their bytes.
    for asset_name, asset_data in list(raw.items()):
        asset_path = Path(asset_name)
        if asset_path.suffix.lower() == ".webp" and asset_path.name.endswith("-cover.webp") and any(part in {"covers", "editorial"} for part in asset_path.parts[:-1]):
            raw.setdefault(asset_path.name, asset_data)
            # The importer permits canonical assets/ paths, not Gemini's covers/ folder.
            if "covers" in asset_path.parts[:-1]:
                raw.pop(asset_name, None)
    if flat_package:
        raw = {n: src.read(n) for n in src.namelist() if not n.endswith("/") and n != "README-PUBLISH.txt"}
        # Gemini's November 17 package uses separate articles/, pages/, covers/ and seo/ folders.
        # Flatten those known directories into the importer's legacy slug-based file names.
        if any(Path(n).parts and Path(n).parts[0] in {"articles", "pages", "covers", "seo"} for n in raw):
            flattened = {"GEMINI_INSTRUCTIONS.txt": raw["GEMINI_INSTRUCTIONS.txt"]} if "GEMINI_INSTRUCTIONS.txt" in raw else {}
            for path, data in raw.items():
                parts = Path(path).parts
                item = Path(parts[-1])
                # Preserve root-level Gemini fragments and SEO records in hybrid packages.
                if len(parts) == 1:
                    flattened[item.name] = data
                    continue
                # Keep canonical cover assets supplied under assets/editorial or assets/responsive.
                if len(parts) == 3 and parts[0] == "assets" and parts[1] in {"editorial", "responsive"}:
                    flattened[item.name] = data
                    continue
                if len(parts) != 2:
                    continue
                folder, filename = parts
                item = Path(filename)
                if folder == "articles" and item.suffix.lower() == ".md":
                    flattened[item.name] = data
                elif folder == "pages" and item.suffix.lower() == ".html":
                    flattened[item.stem + "-fragment.html"] = data
                elif folder == "seo" and item.suffix.lower() == ".json":
                    flattened[item.stem + "-seo.json"] = data
                elif folder == "covers" and item.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                    flattened[item.stem + "-cover" + item.suffix.lower()] = data
            raw = flattened
        print("Detected Gemini publication archive; adapting folder layout, metadata and image variants.")
        for seo_name in [n for n in raw if n.endswith("-seo.json")]:
            meta = json.loads(raw[seo_name].decode("utf-8"))
            slug = meta["slug"]
            meta["headline"] = meta.get("headline") or meta.get("title")
            meta["section"] = meta.get("section") or meta.get("category")
            section_aliases = {"Technology": "Tech & AI", "Technology & AI": "Tech & AI", "Tech and AI": "Tech & AI", "Markets": "Market Analysis", "Finance": "Market Analysis", "Cryptocurrency": "Crypto"}
            meta["section"] = section_aliases.get(meta["section"], meta["section"])
            meta["metaDescription"] = meta.get("metaDescription") or meta.get("description")
            meta["date"] = meta.get("date") or meta.get("datePublished")
            fragment_name = slug + "-fragment.html"
            fragment_doc = html.fromstring("<div>" + raw[fragment_name].decode("utf-8") + "</div>")
            body = fragment_doc.xpath(".//*[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]")
            if not body:
                for heading in fragment_doc.xpath(".//h1"):
                    heading.getparent().remove(heading)
                body = [fragment_doc]
            # Correct Gemini's stale internal TTN slugs to the canonical live article URLs.
            internal_link_aliases = {
                "anthropic-895-billion-compute-commitments-november-16-2026.html": "anthropic-895-billion-compute-commitments-ipo-2026.html",
                "nasdaq-earlier-ai-buildout-sell-off-november-2026.html": "nasdaq-correction-ai-buildout-selloff-november-5-2026.html",
                "us-services-growth-slows-high-costs-complicate-fed-next-move-november-2026.html": "us-ism-services-october-2026-growth-prices-fed.html",
                "uk-cyber-agency-ai-powered-ransomware-critical-infrastructure-november-2026.html": "uk-ai-ransomware-critical-infrastructure-2028.html",
            }
            for link in body[0].xpath(".//a[@href]"):
                href = (link.get("href") or "").strip()
                for stale_slug, canonical_slug in internal_link_aliases.items():
                    if href.endswith("/" + stale_slug):
                        link.set("href", base + canonical_slug)
                        break
            sources = []
            if body:
                seen_urls = set()
                for link in body[0].xpath(".//a[@href]"):
                    href = (link.get("href") or "").strip()
                    label = " ".join(" ".join(link.itertext()).split())
                    if href.startswith("https://") and label and href not in seen_urls:
                        sources.append({"label": label, "url": href})
                        seen_urls.add(href)
            if not sources:
                md_name = slug + ".md"
                md_text = raw.get(md_name, b"").decode("utf-8", errors="replace")
                for label, href in re.findall(r"\[([^\]]+)\]\((https://[^)]+)\)", md_text):
                    if href not in {x["url"] for x in sources}:
                        sources.append({"label": label.strip(), "url": href.strip()})
            meta["sources"] = meta.get("sources") or meta.get("citations") or sources
            raw[seo_name] = json.dumps(meta, ensure_ascii=False).encode("utf-8")
            cover_name = slug + "-cover.webp"
            if cover_name not in raw:
                # Gemini's Nov. 17 package uses the original image_*.jpg names.
                # Match the audited cover files to their article slugs before
                # generating the canonical WebP cover and responsive variants.
                cover_aliases = {
                    "china-us-ai-model-distillation-domestic-rivals-chip-curbs-november-17-2026": "image_474cc8.jpg",
                    "ethereum-mev-25-million-peraire-bueno-brothers-acquittal-november-17-2026": "image_474d25.jpg",
                    "new-zealand-central-bank-private-credit-global-financial-risks-november-17-2026": "image_474ceb.jpg",
                }
                alias = cover_aliases.get(slug)
                source_name = next((n for n in raw if alias and Path(n).stem == Path(alias).stem), None)
                if source_name is None:
                    source_name = next((n for n in raw if Path(n).stem == slug + "-cover" and Path(n).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")), None)
                if source_name is None:
                    image_names = [n for n in raw if Path(n).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
                    raise SystemExit("Missing cover image: " + cover_name + "; checked " + str(alias) + "; available image files: " + ", ".join(image_names))
                with Image.open(BytesIO(raw[source_name])) as source_image:
                    converted = BytesIO()
                    source_image.convert("RGB").save(converted, format="WEBP", quality=90, method=6)
                    raw[cover_name] = converted.getvalue()
            with Image.open(BytesIO(raw[cover_name])) as im:
                im = im.convert("RGB")
                for width, suffix in ((480, "-480.webp"), (960, "-960.webp")):
                    height = round(im.height * width / im.width)
                    resized = im.resize((width, height), Image.Resampling.LANCZOS)
                    buffer = BytesIO()
                    resized.save(buffer, format="WEBP", quality=86, method=6)
                    raw[slug + suffix] = buffer.getvalue()

# Compatibility path for the approved Markdown handoff package with three matched covers.
if flat_package and not any(name.endswith("-seo.json") for name in raw):
    markdown_files = sorted(n for n in raw if Path(n).suffix.lower() == ".md" and Path(n).name != "README.md")
    if len(markdown_files) == 3:
        import markdown as markdown_lib
        section_by_prefix = {"market-analysis-":"Market Analysis", "tech-ai-":"Tech & AI", "crypto-":"Crypto"}
        prepared_at = datetime.now(ZoneInfo("America/New_York")).isoformat(timespec="seconds")
        for md_name in markdown_files:
            slug = Path(md_name).stem
            section = next((v for prefix, v in section_by_prefix.items() if slug.startswith(prefix)), None)
            if not section: raise SystemExit("Cannot determine section from filename: " + md_name)
            md_text = raw[md_name].decode("utf-8-sig", errors="replace")
            if md_text.startswith("---\n"):
                closing = md_text.find("\n---", 4)
                if closing >= 0: md_text = md_text[closing + 4:].lstrip()
            rendered = markdown_lib.markdown(md_text, extensions=["extra", "sane_lists", "smarty"])
            doc = html.fromstring("<div>" + rendered + "</div>")
            h1_nodes = doc.xpath(".//h1")
            if len(h1_nodes) != 1: raise SystemExit("Expected exactly one H1 in " + md_name)
            headline = " ".join(" ".join(h1_nodes[0].itertext()).split())
            h1_nodes[0].getparent().remove(h1_nodes[0])
            paragraphs = doc.xpath(".//p")
            deck = ""
            # This handoff format labels the category and deck as ordinary Markdown paragraphs.
            for paragraph in list(paragraphs[:4]):
                line = " ".join(" ".join(paragraph.itertext()).split())
                if re.match(r"^Category\s*:", line, re.I):
                    paragraph.getparent().remove(paragraph)
                elif re.match(r"^(?:Deck|Subheadline|Standfirst)\s*:", line, re.I):
                    deck = re.sub(r"^(?:Deck|Subheadline|Standfirst)\s*:\s*", "", line, flags=re.I)
                    paragraph.getparent().remove(paragraph)
            if not deck:
                for paragraph in doc.xpath(".//p")[:3]:
                    candidate = " ".join(" ".join(paragraph.itertext()).split())
                    if 10 <= len(candidate.split()) <= 30:
                        deck = candidate
                        paragraph.getparent().remove(paragraph)
                        break
            if not deck:
                preview = [" ".join(" ".join(node.itertext()).split())[:240] for node in list(doc)[:8]]
                raise SystemExit("Could not identify the supplied deck in " + md_name + "; opening blocks=" + repr(preview))
            sources, tickers, seen_urls = [], [], set()
            for heading in list(doc.xpath(".//h2|.//h3")):
                heading_text = " ".join(" ".join(heading.itertext()).split()).lower().rstrip(":")
                if heading_text in {"sources", "references", "source notes", "references and sources"}:
                    parent = heading.getparent()
                    siblings = list(parent)
                    idx = siblings.index(heading) if heading in siblings else -1
                    if idx >= 0:
                        for sibling in siblings[idx + 1:]:
                            if sibling.tag in {"h1","h2","h3"}: break
                            for link in sibling.xpath(".//a[@href]"):
                                href=(link.get("href") or "").strip(); label=" ".join(" ".join(link.itertext()).split())
                                if href.startswith("https://") and label and href not in seen_urls:
                                    sources.append({"label":label,"url":href}); seen_urls.add(href)
                            parent.remove(sibling)
                    parent.remove(heading)
                elif heading_text in {"tradingview tickers","tickers","tradingview"}:
                    parent=heading.getparent(); siblings=list(parent); idx=siblings.index(heading) if heading in siblings else -1
                    if idx>=0:
                        for sibling in siblings[idx+1:]:
                            if sibling.tag in {"h1","h2","h3"}: break
                            line=" ".join(" ".join(sibling.itertext()).split())
                            tickers.extend(re.findall(r"\b(?:NASDAQ|NYSE|AMEX|LSE|HKEX|KRX|TSE|ASX|FX_IDC|BINANCE|COINBASE):[A-Z0-9._/-]+\b|\b(?:BTC|ETH|SOL|XRP)\b",line))
                            parent.remove(sibling)
                    parent.remove(heading)
            for link in doc.xpath(".//a[@href]"):
                href=(link.get("href") or "").strip(); label=" ".join(" ".join(link.itertext()).split())
                if href.startswith("https://") and label and href not in seen_urls:
                    sources.append({"label":label,"url":href}); seen_urls.add(href)
            for paragraph in list(doc.xpath(".//p")):
                line=" ".join(" ".join(paragraph.itertext()).split())
                if re.match(r"^(?:TradingView\s+)?Tickers?\s*:",line,re.I):
                    tickers.extend(re.findall(r"\b(?:NASDAQ|NYSE|AMEX|LSE|HKEX|KRX|TSE|ASX|FX_IDC|BINANCE|COINBASE):[A-Z0-9._/-]+\b|\b(?:BTC|ETH|SOL|XRP)\b",line))
                    paragraph.getparent().remove(paragraph)
            tickers=list(dict.fromkeys(tickers))
            # Remove the handoff's plain-text Sources line; the importer builds one canonical linked Sources block.
            for paragraph in list(doc.xpath(".//p")):
                line = " ".join(" ".join(paragraph.itertext()).split())
                if re.match(r"^(?:Sources?|References?)\s*:", line, re.I):
                    paragraph.getparent().remove(paragraph)
            if not sources:
                source_fallback_20261123 = {
                    "market-analysis-morgan-stanley-bullish-stocks": [
                        {"label":"Reuters, Morgan Stanley turns most bullish on stocks since April after last week's selloff","url":"https://www.reuters.com/business/morgan-stanley-turns-most-bullish-stocks-since-april-after-last-weeks-selloff-2026-11-23/"},
                        {"label":"MarketWatch, Morgan Stanley strategist sees a buying opportunity after the selloff","url":"https://www.marketwatch.com/story/stocks-are-serving-up-a-fat-pitch-for-investors-right-now-as-morgan-stanleys-top-strategist-19abe30a"}
                    ],
                    "tech-ai-nvidia-reinstates-jensen-huang": [
                        {"label":"NVIDIA, Board reinstates Jensen Huang as President, CEO and Board Director","url":"https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Board-Reinstates-Jensen-Huang-as-President-CEO-and-Board-Director/default.aspx"},
                        {"label":"Associated Press, Nvidia board reinstates Jensen Huang as CEO","url":"https://apnews.com/article/39d4b34ffaa867b4e669893b5fd5028f"},
                        {"label":"Reuters via Yahoo Finance, Nvidia reinstates Jensen Huang as CEO","url":"https://finance.yahoo.com/news/nvidia-reinstates-jensen-huang-ceo-135916841.html"}
                    ],
                    "crypto-bitcoin-seven-week-losing-streak": [
                        {"label":"CoinDesk, Bitcoin's losing streak is second-longest ever","url":"https://www.coindesk.com/daybook-us/2026/11/23/bitcoin-s-losing-streak-is-second-longest-ever-and-some-observers-see-more-downside"},
                        {"label":"The Block, Spot bitcoin ETFs shed $1.79 billion in past week","url":"https://www.theblock.co/news/markets/2026-11-23-spot-bitcoin-etfs-shed-1-79-billion-in-past-week-444857"},
                        {"label":"Glassnode, BTC Market Pulse: Week 48","url":"https://research.glassnode.com/btc-market-pulse-week-48-2026/"}
                    ]
                }
                sources = source_fallback_20261123.get(slug, [])
            if not sources: raise SystemExit("No source links found in " + md_name)
            deck_overrides = {
                "market-analysis-morgan-stanley-bullish-stocks": "Morgan Stanley sees a buying opportunity after the selloff, but earnings, rates and AI spending remain key risks.",
                "tech-ai-nvidia-reinstates-jensen-huang": "Nvidia's board restored Jensen Huang as CEO, reversing course while national-security and governance investigations continue.",
                "crypto-bitcoin-seven-week-losing-streak": "Bitcoin's seven-week decline and heavy ETF withdrawals underscore weakening institutional demand and fragile market sentiment."
            }
            deck = deck_overrides.get(slug, deck)
            body=html.Element("div",attrib={"class":"editorial-body"})
            for child in list(doc): body.append(child)
            if not body.xpath(".//p"): raise SystemExit("No article paragraphs in " + md_name)
            word_count=sum(len(" ".join(p.itertext()).split()) for p in body.xpath(".//p"))
            if word_count < 700 or word_count > 1100:
                raise SystemExit(f"Article word count outside 700–1100: {slug}: {word_count}")
            jpgs=(slug+"-cover.jpg","assets/editorial/"+slug+"-cover.jpg"); pngs=(slug+"-cover.png","assets/editorial/"+slug+"-cover.png"); webps=(slug+"-cover.webp","assets/editorial/"+slug+"-cover.webp")
            source_cover=next((p for p in jpgs if p in raw),None) or next((p for p in pngs if p in raw),None) or next((p for p in webps if p in raw),None)
            if not source_cover: raise SystemExit("Missing exact matching cover for " + slug)
            with Image.open(BytesIO(raw[source_cover])) as im:
                width,height=im.size
                if not 1.70 <= width/height <= 1.80:
                    raise SystemExit(f"Invalid cover aspect ratio for {slug}: {width}x{height}")
                # Gemini supplied clean 16:9 covers at 1024px. Upscale without cropping or changing composition to TTN's established 2576×1438 master size.
                im=im.convert("RGB")
                if width < 2576 or height < 1438:
                    im=im.resize((2576,1438),Image.Resampling.LANCZOS)
                converted=BytesIO(); im.save(converted,format="WEBP",quality=92,method=6)
                raw[slug+"-cover.webp"]=converted.getvalue()
            with Image.open(BytesIO(raw[slug+"-cover.webp"])) as master:
                master=master.convert("RGB")
                for target_width,suffix in ((480,"-480.webp"),(960,"-960.webp")):
                    target_height=round(master.height*target_width/master.width)
                    resized=master.resize((target_width,target_height),Image.Resampling.LANCZOS)
                    buffer=BytesIO(); resized.save(buffer,format="WEBP",quality=86,method=6)
                    raw[slug+suffix]=buffer.getvalue()
            raw.pop(source_cover,None)
            description=deck if len(deck)>=70 else headline+" — "+deck
            if len(description)>160: description=description[:157].rsplit(" ",1)[0].rstrip(" ,;:-.")+"."
            seo_titles = {
                "market-analysis-morgan-stanley-bullish-stocks": "Morgan Stanley Turns Bullish After Selloff | TTN Finance",
                "tech-ai-nvidia-reinstates-jensen-huang": "Nvidia Reinstates Jensen Huang as CEO | TTN Finance",
                "crypto-bitcoin-seven-week-losing-streak": "Bitcoin Extends Seven-Week Losing Streak | TTN Finance"
            }
            seo_title=seo_titles.get(slug, headline + " | TTN Finance")
            if len(seo_title)>65: raise SystemExit("SEO title exceeds 65 characters: " + slug)
            meta={"slug":slug,"headline":headline,"section":section,"format":"news" if section=="Tech & AI" else "analysis",
                  "metaDescription":description,"seoTitle":seo_title,"date":prepared_at,
                  "imageAlt":headline,"sources":sources,"tickers":tickers}
            raw[slug+"-fragment.html"]=html.tostring(body,encoding="utf-8",method="html")
            raw[slug+"-seo.json"]=json.dumps(meta,ensure_ascii=False).encode("utf-8")
            raw.pop(md_name,None)
        print("Detected three-article Markdown handoff package; preserved article copy and matched covers.")

# Compatibility path for approved flat ZIPs containing complete article HTML files
# plus their cover images, rather than separate *-seo.json and *-fragment.html files.
if flat_package and not any(name.endswith("-seo.json") for name in raw):
    html_candidates = [
        name for name in raw
        if Path(name).suffix.lower() == ".html"
        and len(Path(name).parts) == 1
        and not name.endswith("-fragment.html")
    ]
    if len(html_candidates) == 3:
        section_aliases = {
            "Technology": "Tech & AI", "Technology & AI": "Tech & AI",
            "Tech and AI": "Tech & AI", "Markets": "Market Analysis",
            "Finance": "Market Analysis", "Cryptocurrency": "Crypto",
        }
        for page_name in html_candidates:
            slug = Path(page_name).stem
            doc = html.fromstring(raw[page_name].decode("utf-8", errors="replace"))
            h1 = doc.xpath("(//h1)[1]")
            if not h1:
                raise SystemExit("Article HTML has no H1: " + page_name)
            headline = " ".join(" ".join(h1[0].itertext()).split())
            body_nodes = doc.xpath(
                '//*[contains(concat(" ",normalize-space(@class)," ")," editorial-body ")]'
            )
            if len(body_nodes) != 1:
                body_nodes = doc.xpath("//main")
            if len(body_nodes) != 1:
                raise SystemExit("Cannot identify one article body in " + page_name)
            body = body_nodes[0]
            for heading in body.xpath(".//h1"):
                heading.getparent().remove(heading)
            fragment_name = slug + "-fragment.html"
            raw[fragment_name] = html.tostring(body, encoding="utf-8", method="html")
            dek_nodes = doc.xpath(
                '//*[contains(concat(" ",normalize-space(@class)," ")," article-dek ") or '
                'contains(concat(" ",normalize-space(@class)," ")," editorial-dek ")]'
            )
            dek = " ".join(" ".join(dek_nodes[0].itertext()).split()) if dek_nodes else ""
            meta_desc = doc.xpath('//meta[@name="description"]/@content | //meta[@property="og:description"]/@content')
            seo_title = doc.xpath("//head/title/text()")
            jsonld = []
            for node in doc.xpath('//script[@type="application/ld+json"]'):
                try:
                    value = json.loads(node.text or "{}")
                    if isinstance(value, dict):
                        jsonld.append(value)
                except Exception:
                    pass
            schema = next((x for x in jsonld if x.get("@type") in ("Article", "NewsArticle")), {})
            section_values = (
                doc.xpath('//meta[@property="article:section"]/@content')
                + doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," ttn-original-badge ")]/text()')
                + [str(schema.get("articleSection") or "")]
            )
            section_raw = next((str(x).strip() for x in section_values if str(x).strip()), "")
            section = section_aliases.get(section_raw, section_raw)
            if section not in sections:
                raise SystemExit("Missing or invalid article section in " + page_name + ": " + section_raw)
            published_values = (
                doc.xpath('//meta[@property="article:published_time"]/@content')
                + doc.xpath("//time/@datetime")
                + [str(schema.get("datePublished") or "")]
            )
            published = next((str(x).strip() for x in published_values if str(x).strip()), "")
            if not published:
                date_match = re.search(r"20\\d{2}-\\d{2}-\\d{2}", page_name)
                published = date_match.group(0) if date_match else date.today().isoformat()
            image_alt = doc.xpath('(//img[@src])[1]/@alt')
            source_links, seen_source_urls = [], set()
            # Gemini may place its bibliography outside .editorial-body.
            # Read article-body citations and explicit bibliography blocks
            # from this same page; never manufacture source URLs.
            source_nodes = list(body.xpath(".//a[@href]"))
            source_nodes += doc.xpath(
                '//*[contains(concat(" ",normalize-space(@class)," ")," editorial-sources ") '
                'or contains(concat(" ",normalize-space(@class)," ")," article-sources ") '
                'or contains(concat(" ",normalize-space(@class)," ")," sources ") '
                'or contains(concat(" ",normalize-space(@class)," ")," citations ") '
                'or contains(concat(" ",normalize-space(@class)," ")," references ")]//a[@href]'
            )
            for link in source_nodes:
                href = (link.get("href") or "").strip()
                label = " ".join(" ".join(link.itertext()).split())
                if href.startswith("https://") and label and href not in seen_source_urls:
                    source_links.append({"label": label, "url": href})
                    seen_source_urls.add(href)
            image_files = [
                n for n in raw
                if Path(n).suffix.lower() in (".webp", ".png", ".jpg", ".jpeg")
            ]
            cover_source = next((n for n in image_files if slug in Path(n).stem), None)
            if cover_source is None:
                hero_refs = doc.xpath('(//main//img[@src])[1]/@src')
                if hero_refs:
                    hero_name = Path(hero_refs[0].split("?", 1)[0]).name
                    cover_source = next((n for n in image_files if Path(n).name == hero_name), None)
            if cover_source is None:
                raise SystemExit(
                    "Cannot match an approved cover to " + page_name
                    + "; image files: " + ", ".join(image_files)
                )
            cover_target = slug + "-cover.webp"
            if cover_source != cover_target:
                with Image.open(BytesIO(raw[cover_source])) as source_image:
                    converted = BytesIO()
                    source_image.convert("RGB").save(converted, format="WEBP", quality=90, method=6)
                    raw[cover_target] = converted.getvalue()
            with Image.open(BytesIO(raw[cover_target])) as cover_image:
                cover_image = cover_image.convert("RGB")
                for width, suffix in ((480, "-480.webp"), (960, "-960.webp")):
                    height = round(cover_image.height * width / cover_image.width)
                    resized = cover_image.resize((width, height), Image.Resampling.LANCZOS)
                    buffer = BytesIO()
                    resized.save(buffer, format="WEBP", quality=86, method=6)
                    raw[slug + suffix] = buffer.getvalue()
            meta = {
                "slug": slug,
                "headline": headline,
                "section": section,
                "metaDescription": (meta_desc[0] if meta_desc else ""),
                "seoTitle": (seo_title[0] if seo_title else headline),
                "date": published,
                "imageAlt": (image_alt[0] if image_alt and image_alt[0].strip() else headline),
                "sources": source_links,
            }
            raw[slug + "-seo.json"] = json.dumps(meta, ensure_ascii=False).encode("utf-8")
        print("Detected three complete flat article pages; extracted publication metadata and matched cover assets.")

internal_link_aliases = {
    "anthropic-895-billion-compute-commitments-november-16-2026.html": "anthropic-895-billion-compute-commitments-ipo-2026.html",
    "nasdaq-earlier-ai-buildout-sell-off-november-2026.html": "nasdaq-correction-ai-buildout-selloff-november-5-2026.html",
    "us-services-growth-slows-high-costs-complicate-fed-next-move-november-2026.html": "us-ism-services-october-2026-growth-prices-fed.html",
    "uk-cyber-agency-ai-powered-ransomware-critical-infrastructure-november-2026.html": "uk-ai-ransomware-critical-infrastructure-2028.html",
}

articles = []
for name, data in list(raw.items()):
    if not name.endswith("-seo.json"): continue
    meta = json.loads(data.decode("utf-8"))
    slug = meta["slug"]
    section = meta["section"]
    # Never invent a publication clock time. Prefer a date supplied in the approved metadata.
    published_date = str(meta.get("publishedAt") or meta.get("datePublished") or meta.get("date") or date.today().isoformat()).strip()
    fallback = seo_fallback.get(slug, {})
    title = meta["headline"]
    image_alt = meta.get("imageAlt") or title
    sources = meta.get("sources") or meta.get("citations") or source_fallback.get(slug, [])
    seo_title = meta.get("seoTitle") or fallback.get("seoTitle") or (title[:48].rsplit(" ",1)[0] + " | TTN Finance")
    seo_title_overrides = {
        "global-banks-trading-revenue-record-301-billion-2026": "Banks’ Trading Revenue Set for Record in 2026 | TTN Finance",
        "crowdstrike-zscaler-43-9-billion-cybersecurity-deal-2026": "CrowdStrike to Buy Zscaler in $43.9 Billion Deal | TTN Finance",
        "ecb-tokenized-securities-eurosystem-collateral-2027": "ECB to Accept Tokenized Securities as Collateral | TTN Finance",
    }
    seo_title = seo_title_overrides.get(slug, seo_title)
    description = meta.get("metaDescription") or fallback.get("metaDescription")
    if len(description) > 160:
        description = description[:157].rsplit(" ", 1)[0].rstrip(" ,;:-.") + "."
    fragment_name = slug + "-fragment.html"
    fragment = raw[fragment_name].decode("utf-8")
    frag = html.fromstring("<div>" + fragment + "</div>")
    dek_node = frag.xpath(".//*[contains(concat(' ',normalize-space(@class),' '),' editorial-dek ')]")
    dek = " ".join(dek_node[0].itertext()).strip() if dek_node else ""
    editorial_overrides = {
        "alibaba-ai-cloud-revenue-jumps-53-infrastructure-spending-cash-flow-november-20-2026": {
            "dek": "Alibaba's AI cloud revenue rose 53% as capital spending climbed 60%, widening free cash outflow.",
            "seoTitle": "Alibaba AI Cloud Revenue Jumps 53% | TTN Finance",
            "metaDescription": "Alibaba's AI cloud revenue rose 53% to RMB60.97 billion, while capital spending climbed 60% and free cash outflow widened."
        },
        "eu-gives-czechia-spain-two-months-crypto-tax-reporting-rules-dac8-november-20-2026": {
            "dek": "EU regulators gave Czechia and Spain two months to complete national DAC8 crypto-asset reporting rules.",
            "seoTitle": "EU Presses Czechia, Spain on DAC8 Crypto Rules | TTN Finance",
            "metaDescription": "The European Commission gave Czechia and Spain two months to complete DAC8 rules for reporting crypto-asset transactions."
        },
        "wall-street-sell-off-deepens-dow-plunges-1100-points-ai-fears-spread-november-20-2026": {
            "dek": "The Dow fell 1,101 points as Wall Street extended its sell-off and investors reassessed AI valuations.",
            "seoTitle": "Wall Street Sell-Off: Dow Drops 1,101 Points | TTN Finance",
            "metaDescription": "The Dow fell 1,101 points, the S&P 500 logged a sixth straight loss and the Nasdaq dropped 2.3% as U.S. stocks sold off."
        },
        "sec-fake-crypto-platforms-37-million-fraud-november-2026": {
            "dek": "The SEC charged eight entities over an alleged $37 million fraud involving fake advisers and cryptocurrency trading platforms.",
            "metaDescription": "The SEC accused eight entities of using fake crypto investment platforms in an alleged fraud that raised more than $37 million.",
            "tickers": []
        },
        "sk-hynix-mars-cxl-memory-pooling-ai-inference-2026": {
            "dek": "SK hynix showed its MARS AI rack and CXL memory pooling at Supercomputing 2026, targeting memory efficiency.",
            "metaDescription": "SK hynix demonstrated its MARS AI rack and CXL memory-pooling technology, highlighting memory as a growing constraint in AI infrastructure.",
            "tickers": ["KRX:000660"]
        },
        "swiss-inflation-snb-second-round-effects-december-policy-2026": {
            "dek": "Swiss inflation reached 1.5% in October as the SNB monitored second-round effects ahead of its December policy decision.",
            "metaDescription": "Swiss inflation rose to 1.5% in October. The SNB is watching for second-round effects as it prepares its December rate decision.",
            "tickers": ["FX_IDC:USDCHF", "FX_IDC:EURCHF"]
        },
        "brookfield-acquire-pgp-glass-blackstone-1-7-billion-2026": {
            "dek": "Brookfield's $1.7 billion PGP Glass deal expands its packaging exposure and gives Blackstone an exit from the business.",
            "seoTitle": "Brookfield to Buy PGP Glass for $1.7B | TTN Finance",
            "metaDescription": "Brookfield agreed to acquire PGP Glass from Blackstone for $1.7 billion, expanding its exposure to India's glass packaging market.",
            "tickers": ["BAM", "BX"]
        },
        "europe-sovereign-cloud-push-us-tech-dominance-2026": {
            "dek": "European sovereignty rules are creating cloud opportunities, but migration costs and US hyperscaler scale limit rapid market-share shifts.",
            "seoTitle": "Europe's Sovereign Cloud Push Tests US Cloud Giants | TTN Finance",
            "metaDescription": "European sovereign-cloud procurement is creating opportunities for regional providers, while migration costs and US hyperscaler scale limit rapid market-share shifts.",
            "tickers": ["AMZN", "MSFT", "GOOGL"]
        },
        "kraken-bitcoin-flash-crash-fragmented-crypto-liquidity-2026": {
            "dek": "Kraken's Canadian-dollar Bitcoin dislocation exposed how thin local order books can amplify selling despite stable global prices.",
            "seoTitle": "Kraken Bitcoin Flash Crash Exposes Liquidity Risk | TTN Finance",
            "metaDescription": "A sharp Bitcoin dislocation on Kraken's Canadian-dollar market exposed fragmented liquidity, execution risk and questions about exchange safeguards.",
            "tickers": ["BTC", "ETH", "XRP"]
        },
        "global-banks-trading-revenue-record-301-billion-2026": {
            "dek": "Banks are projected to earn a record $301.1 billion in 2026 as volatility lifts equities and prime brokerage.",
            "seoTitle": "Banks’ Trading Revenue Set for Record in 2026 | TTN Finance",
            "metaDescription": "Crisil Coalition Greenwich projects global banks' markets revenue will reach $301.1 billion in 2026, driven by equities and prime brokerage.",
            "tickers": []
        },
        "crowdstrike-zscaler-43-9-billion-cybersecurity-deal-2026": {
            "dek": "CrowdStrike’s proposed $43.9 billion Zscaler takeover would combine endpoint protection with cloud-based zero-trust security for enterprise customers.",
            "seoTitle": "CrowdStrike to Buy Zscaler in $43.9 Billion Deal | TTN Finance",
            "metaDescription": "CrowdStrike's proposed $43.9 billion all-stock Zscaler acquisition would combine endpoint protection with cloud-based zero-trust security.",
            "tickers": ["CRWD", "ZS"]
        },
        "ecb-tokenized-securities-eurosystem-collateral-2027": {
            "dek": "The ECB will accept eligible tokenized securities as collateral from June 2027, expanding institutional use of distributed ledgers.",
            "seoTitle": "ECB to Accept Tokenized Securities as Collateral | TTN Finance",
            "metaDescription": "From June 2027, the ECB will accept eligible DLT-issued securities under the EU pilot regime as Eurosystem collateral.",
            "tickers": []
        }
    }
    editorial_override = editorial_overrides.get(slug, {})
    dek = editorial_override.get("dek", dek)
    seo_title = editorial_override.get("seoTitle", seo_title)
    description = editorial_override.get("metaDescription", description)
    if not dek: dek = fallback.get("dek") or description or title
    # Enforce TTN's 70-160 character description rule using the article's own approved dek.
    if not description or len(description) < 70:
        description = dek if len(dek) >= 70 else (title + " — " + dek)
    if len(description) > 160:
        description = description[:157].rsplit(" ", 1)[0].rstrip(" ,;:-.") + "."
    body_nodes = frag.xpath(".//*[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]")
    if not body_nodes:
        for heading in frag.xpath(".//h1"):
            heading.getparent().remove(heading)
        body_nodes = [frag]
    if len(body_nodes) != 1: raise SystemExit("Missing editorial body for " + slug)
    # Rebuild the Sources block once from normalized metadata; do not retain
    # a source list embedded in the supplied full-page HTML and append a duplicate.
    for old_sources in list(body_nodes[0].xpath(
        './/*[contains(concat(" ",normalize-space(@class)," ")," editorial-sources ")]'
    )):
        parent = old_sources.getparent()
        if parent is not None:
            parent.remove(old_sources)
    if flat_package:
        trim_order = {
            "jensen-huang-signals-return-to-nvidia-leadership-crisis-november-17-2026": [],
            "nsa-classified-communications-network-outage-us-infrastructure-reliability-november-17-2026": [17, 14],
            "software-outage-fears-wall-street-sell-off-technology-shares-slide-november-17-2026": [22, 21, 19],
            "dbs-jpmorgan-tokenised-deposit-cross-border-transfers-2026": [15, 12, 10, 6],
            "south-korea-crypto-travel-rule-bill-2026": [13, 8],
            "stark-future-1-2-billion-valuation-150-million-funding-2026": [12, 7, 4],
            # November 20: remove repetitive explanatory paragraphs while preserving
            # every key result, regulatory deadline, cash-flow figure and conclusion.
            "alibaba-ai-cloud-revenue-jumps-53-infrastructure-spending-cash-flow-november-20-2026": [25, 24, 20, 19, 17, 15, 14, 11, 10, 8, 6, 5],
            "eu-gives-czechia-spain-two-months-crypto-tax-reporting-rules-dac8-november-20-2026": [36, 35, 32, 30, 29, 27, 26, 25, 22, 20, 19, 17, 16, 14, 5],
            "wall-street-sell-off-deepens-dow-plunges-1100-points-ai-fears-spread-november-20-2026": [24, 23, 22, 21, 19, 17, 15, 14, 12, 10, 9, 6, 5, 4],
            # November 23: remove repetitive background while retaining contract
            # values, market-share evidence, provider responses and investment implications.
            "europe-sovereign-cloud-push-us-tech-dominance-2026": [11, 4, 2],
            # Remove repeated liquidity explanations and duplicate conclusions while
            # preserving the price dislocation, cross-pair data, Kraken response and risk analysis.
            "kraken-bitcoin-flash-crash-fragmented-crypto-liquidity-2026": [21, 15, 6, 4],
            # November 24: remove one repetitive market-context paragraph while preserving the deal terms,
            # financial metrics, integration risks and transaction implications.
            "crowdstrike-zscaler-43-9-billion-cybersecurity-deal-2026": [12],
        }
        paragraphs = body_nodes[0].xpath(".//p")
        for paragraph_index in sorted(trim_order.get(slug, []), reverse=True):
            if paragraph_index < len(paragraphs):
                paragraph = paragraphs[paragraph_index]
                paragraph.getparent().remove(paragraph)
    body_html = html.tostring(body_nodes[0], encoding="unicode")
    # Apply aliases to the final serialized body as well: the importer consumes this HTML,
    # not the earlier parsed fragment. This catches absolute, root-relative and relative hrefs.
    for stale_slug, canonical_slug in internal_link_aliases.items():
        body_html = body_html.replace(stale_slug, canonical_slug)
    cover = "assets/editorial/" + slug + "-cover.webp"
    small = "assets/responsive/" + slug + "-cover-480.webp"
    medium = "assets/responsive/" + slug + "-cover-960.webp"
    # Use a live TTN article as the structural template; all editorial content below is replaced.
    template = html.parse(str(root / "private-credit-shadow-banking-explained.html"))
    doc = template
    head = doc.xpath("//head")[0]
    def set_meta(selector, attr, value):
        nodes = head.xpath(selector)
        if nodes:
            nodes[0].set(attr, value)
            for duplicate in nodes[1:]:
                duplicate.getparent().remove(duplicate)
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
    set_meta('//meta[@property="og:image:alt"]', "content", image_alt)
    set_meta('//meta[@name="twitter:image:alt"]', "content", image_alt)
    set_meta('//meta[@name="twitter:title"]', "content", title)
    set_meta('//meta[@name="twitter:description"]', "content", description)
    published_nodes = head.xpath('./meta[@property="article:published_time"]')
    if published_nodes: published_nodes[0].set("content", published_date)
    else: etree.SubElement(head, "meta", property="article:published_time", content=published_date)
    modified_date = published_date
    if slug in {
        "global-banks-trading-revenue-record-301-billion-2026",
        "crowdstrike-zscaler-43-9-billion-cybersecurity-deal-2026",
        "ecb-tokenized-securities-eurosystem-collateral-2027",
    }:
        modified_date = datetime.now(ZoneInfo("America/New_York")).isoformat(timespec="seconds")
    set_meta('//meta[@property="article:modified_time"]', "content", modified_date)
    canon_nodes = head.xpath('./link[@rel="canonical"]')
    if canon_nodes: canon_nodes[0].set("href", canon)
    else: etree.SubElement(head, "link", rel="canonical", href=canon)
    robots = head.xpath('./meta[@name="robots"]')
    if robots: robots[0].set("content","index,follow,max-image-preview:large")
    scripts = head.xpath('./script[@type="application/ld+json"]')
    structured = json.loads(scripts[0].text) if scripts and scripts[0].text else {}
    structured.update({"@context":"https://schema.org","@type":"Article","headline":title,"description":description,"datePublished":published_date,"dateModified":modified_date,"inLanguage":"en-US","articleSection":section,"mainEntityOfPage":{"@type":"WebPage","@id":canon},"author":{"@type":"Organization","name":"TTN Research Desk"},"publisher":{"@type":"Organization","name":"TTN Finance","url":base},"citation":[s["url"] for s in sources],"image":{"@type":"ImageObject","url":base+cover,"width":2576,"height":1438,"caption":image_alt},"wordCount":sum(len(" ".join(p.itertext()).split()) for p in body_nodes[0].xpath(".//p"))})
    if scripts:
        scripts[0].text = json.dumps(structured, ensure_ascii=False)
        for duplicate in scripts[1:]:
            duplicate.getparent().remove(duplicate)
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
    tm=etree.SubElement(pub,"time",datetime=published_date)
    published_dt = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
    local_dt = published_dt.astimezone(ZoneInfo("America/New_York")) if published_dt.tzinfo else published_dt
    tm.text = local_dt.strftime("%b %-d, %Y")
    if "T" in published_date:
        tm.text += " · " + local_dt.strftime("%-I:%M %p %Z")
    fig=etree.SubElement(main,"figure",attrib={"class":"ttn-editorial-figure"})
    img=etree.SubElement(fig,"img",src=cover,alt=image_alt,attrib={"class":"article-hero-image","width":"2576","height":"1438","loading":"eager","fetchpriority":"high"})
    img.set("srcset",small+" 480w, "+medium+" 960w, "+cover+" 2576w"); img.set("sizes","(max-width: 900px) calc(100vw - 36px), 820px")
    body=html.fromstring(body_html)
    body.tag="section"
    body.set("class","editorial-body")
    if sources:
        aside=etree.SubElement(body,"aside",attrib={"class":"editorial-sources","aria-labelledby":"editorial-sources-title"})
        etree.SubElement(aside,"h2",id="editorial-sources-title").text="Sources"
        ul=etree.SubElement(aside,"ul")
        for source in sources:
            link=etree.SubElement(etree.SubElement(ul,"li"),"a",href=source["url"],target="_blank",rel="noopener noreferrer")
            link.text=source["label"]
    main.append(body)
    # Preserve the first occurrence of each HTML id; imported source fragments can
    # repeat IDs already present in the shared page template.
    seen_ids = set()
    for node in doc.xpath("//*[@id]"):
        node_id = node.get("id")
        if node_id in seen_ids:
            node.attrib.pop("id", None)
        else:
            seen_ids.add(node_id)
    raw[slug+".html"] = html.tostring(doc, encoding="utf-8", method="html", doctype="<!DOCTYPE html>")
    articles.append({"slug":slug,"title":title,"dek":dek,"section":section,"format":meta.get("format", "news"),"date":published_date,"cover":cover,"sources":sources,"imageAlt":image_alt,"tickers":meta.get("tickers") or editorial_override.get("tickers", []),"seoTitle":seo_title})
    # Move package images into the importer's canonical asset folders.
    stem = slug
    for suffix, dest in [("-cover.webp","assets/editorial/"+slug+"-cover.webp"),("-480.webp","assets/responsive/"+slug+"-cover-480.webp"),("-960.webp","assets/responsive/"+slug+"-cover-960.webp")]:
        key=slug+suffix
        if key not in raw and suffix in ("-480.webp", "-960.webp"):
            # Responsive variants are derivative assets; recreate them from the
            # canonical master when Gemini supplies only the editorial cover.
            master_key = "assets/editorial/" + slug + "-cover.webp"
            if master_key in raw:
                target_width = 480 if suffix == "-480.webp" else 960
                with Image.open(BytesIO(raw[master_key])) as master_image:
                    master_image = master_image.convert("RGB")
                    target_height = round(master_image.height * target_width / master_image.width)
                    resized = master_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    generated = BytesIO()
                    resized.save(generated, format="WEBP", quality=86, method=6)
                    raw[key] = generated.getvalue()
        if key not in raw: raise SystemExit("Missing image " + key)
        raw[dest]=raw.pop(key)
    raw.pop(fragment_name, None)
    raw.pop(slug + ".md", None)
    raw.pop(name, None)
if len(articles)!=3: raise SystemExit("Expected exactly 3 article SEO records")
raw["publication-manifest.json"]=json.dumps(articles,ensure_ascii=False,indent=2).encode()
# The source ZIP's README is informational only and is not imported.
for key in list(raw):
    if Path(key).name.lower() in {"readme.txt", "readme.md"}: raw.pop(key)
tmp=archive_path.with_suffix(".normalized.zip")
with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_DEFLATED) as out:
    for name,data in raw.items(): out.writestr(name,data)
tmp.replace(archive_path)
print("Normalized ZIP:", archive_path, "articles:", len(articles), "entries:", len(raw))
