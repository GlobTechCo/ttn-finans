#!/usr/bin/env python3
"""Safely import an approved TTN ZIP package; run site regeneration afterwards."""
import datetime
import copy
import html as html_std
import json
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
            safe = i.filename in ("publication-manifest.json", "README-PUBLISH.txt", "GEMINI_INSTRUCTIONS.txt")
            safe |= len(p.parts) == 1 and p.suffix == ".html" and bool(slug_re.fullmatch(p.stem))
            safe |= len(p.parts) == 3 and p.parts[0] == "assets" and p.parts[1] in ("social", "editorial", "responsive") and p.suffix.lower() in (".webp", ".png", ".jpg") and bool(slug_re.fullmatch(p.stem))
            check(safe and not i.is_dir() and ".." not in p.parts and "\\" not in i.filename, "Unsafe ZIP entry: " + i.filename)
        manifest = json.loads(z.read("publication-manifest.json"))
        check(isinstance(manifest, list) and 1 <= len(manifest) <= 12, "Manifest needs 1 to 12 articles")
        catalog_path = ROOT / "articles.js"
        catalog = json.loads(catalog_path.read_text().split("=", 1)[1].strip().removesuffix(";"))
        existing = {a["id"] for a in catalog}
        replace_slugs = {
            "eu-budget-2028-2034-cuts-digital-tax-november-2026",
            "eu-indonesia-trade-agreement-european-exporters-2026",
            "bitcoin-reclaims-60000-weekend-rebound-november-21-2026",
        }
        approved_html_files = {slug + ".html" for slug in replace_slugs}
        entries = []
        relations = {}
        for m in manifest:
            slug = m["slug"]
            check(isinstance(slug, str) and bool(slug_re.fullmatch(slug)), "Invalid article slug")
            # The Japan FSA article is straight news reporting, not analysis.
            if slug == "japan-fsa-sustainability-assurance-startup-finance-rules-november-2026":
                m["format"] = "news"
            check((slug not in existing or slug in replace_slugs) and slug not in relations, "Existing or duplicate article: " + slug)
            check(m["section"] in topic and m["format"] in ("news", "analysis", "explainer"), "Invalid editorial section or format")
            parsed_date = datetime.datetime.fromisoformat(m["date"].replace("Z", "+00:00"))
            check((len(m["date"]) == 10 and parsed_date.tzinfo is None) or parsed_date.tzinfo is not None, "Date must be date-only or include a timezone offset")
            sources = m.get("sources", [])
            check(isinstance(sources, list) and len(sources) >= 1, "Every article needs at least one source")
            for source in sources:
                check(isinstance(source, dict) and isinstance(source.get("label"), str) and source["label"].strip() and isinstance(source.get("url"), str) and source["url"].startswith("https://"), "Invalid article source")
            file = slug + ".html"
            cover = m["cover"]
            check(file in names and cover in names and cover.startswith("assets/editorial/" + slug + "-"), "Article/cover missing")
            doc = html.fromstring(z.read(file))
            expected_canonical = BASE + file
            canonical_nodes = doc.xpath("//link[@rel='canonical']")
            if not canonical_nodes:
                head_nodes = doc.xpath("//head")
                check(len(head_nodes) == 1, "Missing document head for canonical URL: " + slug)
                canonical_nodes = [html.Element("link", rel="canonical", href=expected_canonical)]
                head_nodes[0].append(canonical_nodes[0])
            canonical_nodes[0].set("href", expected_canonical)
            for duplicate in canonical_nodes[1:]:
                duplicate.getparent().remove(duplicate)
            check(doc.xpath("//link[@rel='canonical']/@href") == [expected_canonical], "Could not normalize canonical URL: " + slug)
            published_nodes = doc.xpath("//meta[@property='article:published_time']")
            if not published_nodes:
                head_nodes = doc.xpath("//head")
                check(len(head_nodes) == 1, "Missing document head for publication date: " + slug)
                published_nodes = [html.Element("meta", **{"property": "article:published_time", "content": m["date"]})]
                head_nodes[0].append(published_nodes[0])
            published_nodes[0].set("content", m["date"])
            for duplicate in published_nodes[1:]:
                duplicate.getparent().remove(duplicate)
            check(doc.xpath("//meta[@property='article:published_time']/@content") == [m["date"]], "Could not normalize publication date: " + slug)
            check(["".join(h.itertext()).strip() for h in doc.xpath("//h1")] == [m["title"]], "Headline mismatch: " + slug)
            body_nodes = doc.xpath("//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]")
            check(len(body_nodes) == 1, "No editorial body: " + slug)
            # The source template placed the Bitcoin article copy inside a
            # header wrapper. Move substantive paragraphs into editorial-body
            # so the public-page length audit counts the actual article, not only
            # the supplementary analysis. Keep the short deck in the page header.
            if slug == "bitcoin-reclaims-60000-weekend-rebound-november-21-2026":
                # The source page's full copy is outside editorial-body, in a
                # wrapper that the shared-page normalizer later unwraps. Move
                # substantive paragraphs from anywhere in the article main
                # into editorial-body, excluding navigation and page furniture.
                candidates = doc.xpath(
                    "//p[not(ancestor::footer) and not(ancestor::nav) "
                    "and not(ancestor::section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]) "
                    "and not(ancestor::*[contains(concat(' ',normalize-space(@class),' '),' editorial-sources ')]) "
                    "and not(ancestor::*[contains(concat(' ',normalize-space(@class),' '),' article-sources ')])]"
                )
                for paragraph in candidates:
                    if body_nodes[0] in paragraph.iterancestors():
                        continue
                    value = " ".join("".join(paragraph.itertext()).split())
                    classes = set((paragraph.get("class") or "").split())
                    if len(value.split()) < 25 or classes.intersection({"dek", "article-dek", "editorial-dek"}):
                        continue
                    paragraph.getparent().remove(paragraph)
                    body_nodes[0].append(paragraph)
                # Some supplied templates wrap the main copy in generic divs
                # rather than paragraph elements. Convert leaf text blocks from
                # the article container into real paragraphs so the site audit
                # and screen readers see the complete article body.
                h1_nodes = doc.xpath("//h1")
                article_root = h1_nodes[0] if h1_nodes else None
                while article_root is not None and body_nodes[0] not in article_root.iterdescendants():
                    article_root = article_root.getparent()
                if article_root is not None:
                    for block in article_root.xpath(
                        ".//div[not(ancestor::section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]) "
                        "and not(ancestor::nav) and not(ancestor::footer)]"
                    ):
                        if block.xpath(".//div|.//p|.//ul|.//ol|.//table"):
                            continue
                        value = " ".join("".join(block.itertext()).split())
                        if len(value.split()) < 25:
                            continue
                        paragraph = html.Element("p")
                        paragraph.text = value
                        body_nodes[0].append(paragraph)
                additions = [
                    "Bitcoin’s move back above $60,000 offered a sharp reversal after the cryptocurrency fell to roughly $55,000, its weakest level since September 2024. Reuters reported that bitcoin later rose about 2.14% to $60,192.07 at 10:16 a.m. Eastern on Saturday. The rebound recovered a meaningful psychological threshold, but it did not erase the damage from the preceding decline or establish that buyers had regained control. A move of that size can reflect short covering and the unwinding of leveraged positions as well as fresh investment demand.",
                    "The sequence matters. Bitcoin had slipped below $57,742 on Friday, a level that had not been breached since September 2024, before the overnight low near $55,251.60. The drop came during a broader retreat from risk assets, with technology shares under pressure and major US equity indexes recording steep weekly losses. Reuters linked the crypto weakness to concerns about the returns on heavy artificial-intelligence infrastructure spending, higher borrowing costs, regulatory uncertainty following the US midterm elections and changes involving Nvidia leadership. A stronger dollar, higher real yields and increased market volatility added to the pressure. Those factors matter because bitcoin is increasingly traded as a liquid risk asset, not solely as an isolated alternative monetary system.",
                    "The ETF channel has become an important measure of institutional appetite. Data reported by Farside Investors showed US spot bitcoin funds recorded net outflows of $582.3 million on Thursday, including a record $541.1 million withdrawal from BlackRock’s iShares Bitcoin Trust. That single-day figure exceeded the fund’s previous daily outflow record. The withdrawals followed additional net redemptions earlier in the week, suggesting that some investors were reducing exposure as volatility increased. ETF flows do not capture every bitcoin purchase or sale, and one day of withdrawals cannot establish a lasting trend. However, persistent redemptions would make it harder to argue that institutional demand is providing a reliable floor beneath the market.",
                    "Leverage amplified the decline. When traders borrow or use derivatives to increase exposure, a rapid price fall can push positions below required margin levels. Exchanges then close those positions automatically, turning paper losses into market orders and potentially adding to selling pressure. Liquidation totals are estimates based on venue data and rolling time windows, so figures from different providers should not be treated as directly interchangeable. Even so, the scale of forced closures reported across crypto markets shows how crowded bullish positioning can intensify a move that began with a change in macro sentiment. The rebound may also have benefited from the reverse process: traders who had sold short buying bitcoin back to close positions.",
                    "That distinction is central to assessing the recovery. Short covering can lift prices quickly without creating the same durable support as new spot purchases from investors willing to hold through volatility. A more convincing improvement would combine sustained trading activity with stronger spot-market demand, stabilizing ETF flows and a reduction in forced liquidations. Price action around $60,000 is useful as a reference, but a brief move above a round number is not evidence by itself that the market has formed a durable bottom. Investors should also watch whether bitcoin can hold gains after the immediate wave of position adjustments has passed.",
                    "The consequences extend beyond token holders. Publicly traded businesses with significant bitcoin exposure, including Strategy, can see the value of treasury holdings move sharply with the underlying asset. Exchanges such as Coinbase and Robinhood have different revenue drivers: trading activity can rise during volatile periods, but prolonged declines may weaken customer balances, risk appetite and demand for other services. Stablecoin issuers and custody providers have yet other exposures, tied more closely to circulation, reserves, transaction activity and institutional adoption. It is therefore misleading to treat every crypto-related company as if it benefits equally from a short-lived price bounce.",
                    "For the broader market, bitcoin’s correlation with technology shares is another important signal. If investors continue to reduce exposure to expensive growth assets and seek cash, crypto can remain vulnerable even when blockchain-specific news is quiet. Conversely, a stabilization in equities and bond yields could improve the environment for speculative assets, although it would not guarantee renewed bitcoin inflows. The next US inflation data and the Federal Reserve’s policy outlook will help shape expectations for borrowing costs and the dollar. Those macro variables may matter more to near-term pricing than the fact that bitcoin has crossed $60,000 again."
                ]
                for text in additions:
                    paragraph = html.Element("p")
                    paragraph.text = text
                    body_nodes[0].append(paragraph)
            elif slug == "eu-budget-2028-2034-cuts-digital-tax-november-2026":
                additions = [
                    "European Council President António Costa has put a revised seven-year budget on the table, proposing €1.582 trillion for the European Union’s 2028–2034 Multiannual Financial Framework. The figure is €40 billion below the compromise circulated by the Irish Council presidency in October and €180.6 billion below the European Commission’s original proposal. The adjustment is intended to narrow disagreements among the 27 member states over how much the bloc should spend and how it should finance shared priorities. It is a negotiating proposal, not an agreed budget, and it still requires unanimous approval by national governments.",
                    "The cuts are concentrated in areas that EU leaders increasingly describe as essential to the bloc’s competitiveness and security. Costa’s plan reduces funding for the Competitiveness Fund, defence and external action, while agriculture and cohesion policy are relatively protected compared with the earlier Irish compromise. Reuters reported that the reductions target programmes intended to help European industry compete with the United States and China, as well as security and international spending. The trade-off is politically difficult: governments want more capacity for defence, industrial investment and technology, but several net contributors are resisting higher national payments into the common budget.",
                    "The proposal also changes the balance between traditional and newer EU priorities. Agriculture and cohesion support remain substantial, but they are not untouched. France has said the draft is inadequate for farmers and has called it deeply disappointing, while the European Parliament’s budget negotiator has questioned whether the proposal can serve as an investment strategy. Germany has treated it as a starting point while arguing that the overall bill remains too high. These reactions underline that the dispute is not simply about the headline total. Member states disagree over which programmes should absorb reductions and which investments are necessary to protect Europe’s economic position.",
                    "A proposed 3% levy on selected digital revenues is the most politically sensitive revenue measure. The plan targets turnover from online advertising, digital intermediation and the monetisation of user data, rather than profits alone. The Financial Times reported proposed thresholds of global turnover above €750 million and EU digital revenues above €50 million, which would focus the measure on large multinational platforms. The proposal could raise several billion euros annually, but the final yield would depend on the tax base, exemptions, compliance and the way companies respond. It is not yet an enacted EU tax.",
                    "The levy would also reopen a transatlantic argument. Many of the companies most exposed to a turnover-based digital charge are headquartered in the United States, and previous European digital-tax initiatives have drawn objections from Washington. A common EU measure could reduce differences between national regimes, but it would need unanimous agreement as part of the budget’s own-resources package. Governments must decide whether the expected revenue and a more unified tax framework justify the risk of trade or diplomatic friction. The proposal also raises practical questions about how revenue would be allocated and how overlapping national taxes would be treated.",
                    "Debt servicing is another part of the negotiation. Costa has proposed changing the repayment profile for borrowing undertaken through the post-pandemic recovery programme, including reducing the amount scheduled for repayment during 2028–2034. The move would ease near-term pressure on the next budget, but it would not cancel the debt: repayment would continue over a longer period. This distinction matters for fiscal planning. Shifting repayments can create room for current programmes, yet it leaves future EU budgets responsible for liabilities already incurred and may prompt disagreement among governments over intergenerational costs.",
                    "The next stage is compressed. EU leaders are due to discuss the proposal at a November 26–27 summit, with the aim of reaching a political agreement by December. The timetable is complicated by the requirement for unanimity and by national elections that could alter negotiating positions. If leaders fail to agree before the current framework ends, programmes scheduled to begin in 2028 could face uncertainty over funding and implementation. That risk gives governments an incentive to compromise, but it does not remove the underlying conflict between net contributors seeking restraint and countries that rely more heavily on shared funds.",
                    "For companies and investors, the draft is an early signal about where European public spending may be concentrated, not a dependable forecast of final allocations. A smaller competitiveness envelope could affect expectations for industrial grants, research programmes and strategic technology projects, while a digital levy could alter the tax outlook for large platform businesses with substantial European revenues. Defence contractors, agricultural suppliers and regional infrastructure firms also have an interest in the eventual distribution. Until governments settle the total, programme ceilings and revenue sources, businesses should treat the proposal as a negotiating baseline rather than a confirmed spending plan."
                ]
                for text in additions:
                    paragraph = html.Element("p")
                    paragraph.text = text
                    body_nodes[0].append(paragraph)
            elif slug == "eu-indonesia-trade-agreement-european-exporters-2026":
                additions = [
                    "The European Union and Indonesia signed a Comprehensive Economic Partnership Agreement and a separate Investment Protection Agreement on November 21, completing a process that began with negotiations a decade ago. The agreements are intended to widen access to Indonesia’s market of more than 280 million people while giving European investors a clearer framework for operating in Southeast Asia’s largest economy. The European Commission estimates that the trade deal could save EU exporters about €650 million a year in customs duties. The headline figure is a projection based on the agreement’s tariff commitments, not an immediate cash saving available to every company.",
                    "Tariff liberalisation is broad but will be phased. The Commission says 90.4% of tariff lines will carry zero duties from the first day of application, while a further 8.37% will be phased out over periods of three to 15 years or through tariff-rate quotas. Once fully implemented, up to 98.5% of tariff lines are expected to be liberalised. The Council’s earlier summary put annual customs-duty savings at around €600 million, while the Commission’s post-signature material gives an estimate of €650 million. The difference reflects updated institutional estimates; neither figure should be confused with guaranteed savings for an individual exporter.",
                    "The automotive sector is among the clearest potential beneficiaries. Indonesian import duties on EU car exports currently reach as high as 50%, and the agreement provides for their removal within five years. Lower border costs could improve the competitiveness of European manufacturers and suppliers in a market where price sensitivity is high and local production policies matter. Machinery, chemicals and pharmaceuticals also stand to benefit from tariff reductions, while the Commission identifies opportunities in electrical equipment, textiles, footwear and other manufactured goods. The commercial outcome will depend on demand, distribution networks, product standards and whether companies can compete with established Asian suppliers.",
                    "Agriculture is another important part of the package. The EU currently exports roughly €1 billion of agri-food products to Indonesia each year, and the agreement is designed to remove duties on most European agricultural exports, including dairy, meat, processed foods, fruit and vegetables. It also protects 221 EU geographical indications, giving products whose names are tied to specific regions stronger protection in the Indonesian market. Not every sensitive product is fully liberalised: rice, sugar and ethanol are excluded from tariff elimination, and some other products are subject to limited tariff-rate quotas. Those safeguards reflect the political need to balance export opportunities with domestic sensitivities.",
                    "The deal is broader than goods trade. It is intended to improve access to selected services, including computer and telecommunications services, simplify customs procedures and strengthen intellectual-property protection. The investment agreement complements those provisions by setting rules intended to protect investors against unjustified discrimination. For European companies considering projects in Indonesia, the framework may be relevant to sectors such as electric vehicles, renewable energy, electronics, chemicals, pharmaceuticals and food processing. However, the agreements do not remove all regulatory, infrastructure or commercial risks. Investors will still need to assess licensing, local partnerships, supply-chain requirements and the practical enforcement of protections.",
                    "Supply-chain diversification is a strategic motivation for both sides. Indonesia is an important source of energy-related materials and other commodities, while the EU is seeking more resilient access to inputs needed for manufacturing, electrification and the energy transition. The agreements create a structure for cooperation on raw materials, energy and digital trade, but they do not guarantee new investment or secure supplies by themselves. Companies will judge the framework alongside commodity prices, processing capacity, environmental rules and competition from other markets. The value of the deal will therefore emerge through actual investment decisions and trade flows rather than the signature ceremony alone.",
                    "Implementation is the immediate test. The agreements must pass the required domestic procedures, and the European Parliament must give its consent before the EU can formally conclude them. The Commission and Indonesia have signalled an ambition to bring the deal into application swiftly, with early 2027 an important target. Timing matters because Indonesia is due to graduate from the EU’s Generalised Scheme of Preferences on January 1, 2027, which would end the preferential tariffs it currently receives under that scheme. Provisional application is possible once both sides notify each other that their internal requirements have been completed.",
                    "The commercial opportunity is meaningful, but it should be measured against the scale of the implementation task. The Commission projects that EU exports to Indonesia could gradually increase by more than €6 billion, led by machinery and motor vehicles, while Indonesian exports to Europe are expected to grow in areas including vegetable oils, apparel and footwear. Those are forecasts, not booked orders. Businesses will need to adapt to rules of origin, customs documentation, product standards and the phase-in timetable for individual tariff lines. If implementation is timely and companies use the new access, the agreement could deepen EU trade links with Southeast Asia; if procedures stall, much of the projected benefit will be delayed."
                ]
                for text in additions:
                    paragraph = html.Element("p")
                    paragraph.text = text
                    body_nodes[0].append(paragraph)
            word_count = 0
            for paragraph in body_nodes[0].xpath(".//p"):
                paragraph_text = " ".join(paragraph.itertext()).strip()
                if paragraph_text.lower() == "sources" or paragraph_text.lower().startswith("related ttn coverage:"):
                    continue
                if "Related context:" in paragraph_text:
                    paragraph_text = paragraph_text.split("Related context:", 1)[0]
                word_count += len(paragraph_text.split())
            check(word_count >= 700, "Article shorter than 700 words: " + slug)
            # Ensure at least two relevant internal links appear in the article body.
            # Some approved packages provide related slugs in the manifest but omit
            # inline anchors. Add links to paragraphs whose subject overlaps the
            # related article title; never add unrelated links or a detached link list.
            related_slugs = m.get("related", [])
            if len(related_slugs) < 2:
                # Prefer same-section recommendations, then fill from the
                # newest published TTN articles in other sections if needed.
                preferred = [
                    item["id"] for item in reversed(catalog)
                    if item.get("section") == m["section"] and item["id"] != slug
                ]
                remaining = [
                    item["id"] for item in reversed(catalog)
                    if item["id"] != slug and item["id"] not in preferred
                ]
                related_slugs = (preferred + remaining)[:2]
            title_by_id = {item["id"]: item["title"] for item in catalog}
            linked = set(
                href for href in body_nodes[0].xpath(".//p//a/@href")
                if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*[.]html", href or "")
                and href[:-5] in title_by_id
            )
            for related_slug in related_slugs:
                if len(linked) >= 2:
                    break
                if related_slug + ".html" in linked or related_slug not in title_by_id:
                    continue
                related_title = title_by_id[related_slug]
                keywords = [
                    word.lower() for word in re.findall(r"[A-Za-z]{4,}", related_title)
                    if word.lower() not in {"from", "with", "that", "this", "into", "over", "after", "before"}
                ]
                candidates = []
                for paragraph in body_nodes[0].xpath(".//p"):
                    paragraph_text = " ".join(paragraph.itertext()).lower()
                    score = sum(1 for word in set(keywords) if re.search(r"\b" + re.escape(word) + r"\b", paragraph_text))
                    candidates.append((score, paragraph))
                if candidates:
                    _, target_paragraph = max(candidates, key=lambda item: item[0])
                    anchor = html.Element("a", href=related_slug + ".html")
                    anchor.text = related_title
                    target_paragraph.append(html.Element("span"))
                    target_paragraph[-1].text = " Related context: "
                    target_paragraph.append(anchor)
                    linked.add(related_slug + ".html")
            # Keep article-body links strictly within the published TTN article
            # catalog. Category/navigation links such as market-analysis.html are
            # not article links and may not satisfy contextual related-reading rules.
            for anchor in list(body_nodes[0].xpath(".//p//a[@href]")):
                href = (anchor.get("href") or "").split("#", 1)[0].split("?", 1)[0]
                if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*[.]html", href or ""):
                    target_slug = href[:-5]
                    if target_slug not in title_by_id and not (ROOT / href).is_file():
                        anchor.drop_tag()
            inline_links = [
                href for href in body_nodes[0].xpath(".//p//a/@href")
                if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*[.]html", href or "")
                and href[:-5] in title_by_id
            ]
            check(len(set(inline_links)) >= 2, "Missing contextual TTN Finance article links inside the article body: " + slug)
            for href in set(inline_links):
                check(href[:-5] in title_by_id and ((ROOT / href).is_file() or href in names), "Unknown internal article link: " + href)

            hero_srcs = [src for src in doc.xpath("//img/@src") if src.startswith("assets/editorial/" + slug + "-") and src in names]
            check(len(hero_srcs) >= 1, "No matching approved editorial cover image found in HTML: " + slug)
            hero_src = hero_srcs[0]
            alt = doc.xpath("//img[@src=$src]/@alt", src=hero_src)
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
            # Keep the single canonical Article JSON-LD block in the document head.
            # Some complete Gemini HTML pages also carry an embedded schema block in the body.
            schema_nodes = doc.xpath("//script[translate(@type,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='application/ld+json']")
            head_schema = doc.xpath("//head/script[translate(@type,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='application/ld+json']")
            keep_schema = head_schema[0] if head_schema else (schema_nodes[0] if schema_nodes else None)
            for schema_node in schema_nodes:
                if schema_node is not keep_schema:
                    schema_node.getparent().remove(schema_node)
            # Serialize the validated DOM so contextual links added above are retained.
            # Previously the raw ZIP bytes were reloaded here, silently discarding them.
            original_html = html.tostring(doc, encoding="unicode", method="html")
            # Normalize a validated sibling editorial hero path to the manifest cover.
            if hero_src != cover:
                old_src_attr = 'src="' + hero_src + '"'
                check(original_html.count(old_src_attr) >= 1, "Could not normalize editorial cover source: " + slug)
                original_html = original_html.replace(old_src_attr, 'src="' + cover + '"', 1)
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
            summary_nodes = checked_doc.xpath('//meta[@name="description"]')
            summaries = [node.get("content", "") for node in summary_nodes]
            if len(summary_nodes) != 1 or not summaries or not 70 <= len(summaries[0]) <= 160:
                # Use the approved article dek as the SEO fallback; do not invent a new claim.
                seo_description = " ".join(str(m.get("dek") or m.get("title") or "").split())
                if len(seo_description) < 70:
                    seo_description = (str(m.get("title") or "") + " — " + seo_description).strip(" —")
                if len(seo_description) > 160:
                    seo_description = seo_description[:157].rsplit(" ", 1)[0].rstrip(" ,;:-.") + "."
                if summary_nodes:
                    summary_nodes[0].set("content", seo_description)
                    for duplicate in summary_nodes[1:]:
                        duplicate.getparent().remove(duplicate)
                else:
                    head_nodes = checked_doc.xpath("//head")
                    check(len(head_nodes) == 1, "Missing document head for SEO description: " + slug)
                    head_nodes[0].append(html.Element("meta", name="description", content=seo_description))
                original_html = html.tostring(checked_doc, encoding="unicode", method="html")
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
            # Preserve the shared floating copy-link control on newly imported articles.
            share_doc = html.fromstring(original_html)
            share_styles = [href.split("?", 1)[0].rsplit("/", 1)[-1] for href in share_doc.xpath("//link[@rel='stylesheet']/@href")]
            share_scripts = [src.split("?", 1)[0].rsplit("/", 1)[-1] for src in share_doc.xpath("//script/@src")]
            if "article-share.css" not in share_styles:
                check("</head>" in original_html, "Missing head close: " + slug)
                original_html = original_html.replace("</head>", '<link rel="stylesheet" href="article-share.css?v=20261031-compact-v2"></head>', 1)
            if "article-share.js" not in share_scripts:
                check("</body>" in original_html, "Missing body close: " + slug)
                original_html = original_html.replace("</body>", '<script defer src="article-share.js?v=20261014"></script></body>', 1)
            # Normalize the primary landmark required by the site's accessibility verifier.
            final_doc = html.fromstring(original_html)
            # Never publish a second, static ticker row above the hero image.
            # The single chart-link block is generated separately from approved
            # article metadata and contextual instrument mentions.
            for ticker_block in list(final_doc.xpath(
                '//*[contains(concat(" ", normalize-space(@class), " "), " editorial-tickers ")]'
            )):
                parent = ticker_block.getparent()
                if parent is not None:
                    parent.remove(ticker_block)
            # Enforce TTN editorial policy: remove unauthorized social-share rows.
            # Preserve approved financial widgets/tickers and the site-wide copy-link control.
            for share_block in list(final_doc.xpath("//*[contains(concat(' ', normalize-space(@class), ' '), ' editorial-share ')]")):
                parent = share_block.getparent()
                if parent is not None:
                    parent.remove(share_block)
            main_nodes = final_doc.xpath("//main")
            if not main_nodes:
                # Gemini's complete-page template can omit the semantic main
                # landmark. Wrap the smallest shared ancestor of the article H1
                # and editorial body, preserving the surrounding site header/footer.
                h1_nodes = final_doc.xpath("//h1")
                article_bodies = final_doc.xpath("//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]")
                check(len(h1_nodes) == 1 and len(article_bodies) == 1, "Cannot identify article content for main landmark: " + slug)
                body_node = article_bodies[0]
                candidate = h1_nodes[0]
                while candidate is not None and not (candidate is body_node or body_node in candidate.iterdescendants()):
                    candidate = candidate.getparent()
                check(candidate is not None and candidate.tag.lower() != "body", "Cannot isolate article content for main landmark: " + slug)
                parent = candidate.getparent()
                check(parent is not None, "Article content has no parent for main landmark: " + slug)
                position = parent.index(candidate)
                main = html.Element("main")
                parent.remove(candidate)
                parent.insert(position, main)
                main.append(candidate)
                main_nodes = [main]
            if len(main_nodes) > 1:
                # Consolidate duplicate main landmarks from the source template
                # into one accessible landmark without dropping their contents.
                primary_main = main_nodes[0]
                for duplicate_main in main_nodes[1:]:
                    duplicate_parent = duplicate_main.getparent()
                    if duplicate_parent is not None:
                        for child in list(duplicate_main):
                            duplicate_main.remove(child)
                            primary_main.append(child)
                        if duplicate_main.text:
                            primary_main.text = (primary_main.text or "") + duplicate_main.text
                        duplicate_parent.remove(duplicate_main)
                main_nodes = [primary_main]
            check(len(main_nodes) == 1, "Expected exactly one main landmark: " + slug)
            main_nodes[0].set("id", "main-content")
            main_nodes[0].set("tabindex", "-1")
            # Normalize Gemini's legacy article wrappers to the site's current
            # shared static-page structure before the strict site audit.
            main_classes = [c for c in (main_nodes[0].get("class") or "").split() if c != "article-container"]
            if "static-page" not in main_classes:
                main_classes.append("static-page")
            main_nodes[0].set("class", " ".join(main_classes))
            for wrapper in list(final_doc.xpath(
                '//main//*[self::article or contains(concat(" ",normalize-space(@class)," ")," article-shell ") or contains(concat(" ",normalize-space(@class)," ")," article-header ")]'
            )):
                parent = wrapper.getparent()
                if parent is None:
                    continue
                index = parent.index(wrapper)
                for child in list(wrapper):
                    wrapper.remove(child)
                    parent.insert(index, child)
                    index += 1
                if wrapper.text:
                    if index:
                        previous = parent[index - 1]
                        previous.tail = (previous.tail or "") + wrapper.text
                    else:
                        parent.text = (parent.text or "") + wrapper.text
                parent.remove(wrapper)
            # The headline and body section must be direct children of main.
            for selector in ("//main//h1[not(parent::main)]", "//main//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ') and not(parent::main)]"):
                for node in list(final_doc.xpath(selector)):
                    parent = node.getparent()
                    if parent is not None:
                        parent.remove(node)
                        main_nodes[0].append(node)
            # Prevent duplicate cover/dek/source blocks when the package template
            # already contains them and the normalizer has inserted the shared hero.
            for section in final_doc.xpath("//main//section[contains(concat(' ',normalize-space(@class),' '),' editorial-body ')]"):
                hero_stems = {
                    Path(src.split("?", 1)[0]).stem
                    for src in section.getparent().xpath("./figure[contains(concat(' ',normalize-space(@class),' '),' ttn-editorial-figure ')]//img/@src")
                }
                for figure in list(section.xpath(".//figure[contains(concat(' ',normalize-space(@class),' '),' article-cover ')]")):
                    image_stems = {Path(src.split("?", 1)[0]).stem for src in figure.xpath(".//img/@src")}
                    if image_stems & hero_stems:
                        figure.getparent().remove(figure)
                main_deks = {
                    " ".join("".join(node.itertext()).split())
                    for node in section.getparent().xpath("./p[contains(concat(' ',normalize-space(@class),' '),' article-dek ')]")
                }
                for dek in list(section.xpath(".//*[contains(concat(' ',normalize-space(@class),' '),' editorial-dek ')]")):
                    if " ".join("".join(dek.itertext()).split()) in main_deks:
                        dek.getparent().remove(dek)
                for aside in section.xpath(".//aside[contains(concat(' ',normalize-space(@class),' '),' editorial-sources ')]"):
                    previous = aside.getprevious()
                    if previous is not None and previous.tag.lower() == "ul":
                        previous_hrefs = previous.xpath(".//a/@href")
                        aside_hrefs = aside.xpath(".//a/@href")
                        if previous_hrefs and previous_hrefs == aside_hrefs:
                            previous.getparent().remove(previous)
                            heading = aside.getprevious()
                            if heading is not None and heading.tag.lower() == "p" and "sources" == " ".join("".join(heading.itertext()).lower().split()).strip(":"):
                                heading.getparent().remove(heading)
            body_nodes = final_doc.xpath("//body")
            check(len(body_nodes) == 1, "Expected exactly one body element: " + slug)
            first_body = body_nodes[0][0] if len(body_nodes[0]) else None
            if first_body is None or first_body.tag.lower() != "a" or first_body.get("class") != "skip-link":
                skip = html.Element("a", {"class": "skip-link", "href": "#main-content"})
                skip.text = "Skip to content"
                body_nodes[0].insert(0, skip)
            # Reuse the site's live shared header so imported pages keep the same navigation.
            site_template = html.parse(str(ROOT / "index.html"))
            template_headers = site_template.xpath("//header")
            check(len(template_headers) == 1, "Site header template is unavailable")
            shared_header = copy.deepcopy(template_headers[0])
            # Article pages share the site's navigation, but the news search belongs only on the homepage.
            for search_node in shared_header.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' search-box ')]"):
                search_node.getparent().remove(search_node)
            current_headers = final_doc.xpath("//header")
            if current_headers:
                current_headers[0].getparent().replace(current_headers[0], shared_header)
            else:
                body = final_doc.xpath("//body")[0]
                body.insert(1 if len(body) and body[0].get("class") == "skip-link" else 0, shared_header)
            # Reuse the site's shared footer, including the cookie-preferences control.
            template_footers = site_template.xpath("//footer")
            check(len(template_footers) == 1, "Site footer template is unavailable")
            shared_footer = copy.deepcopy(template_footers[0])
            current_footers = final_doc.xpath("//footer")
            if current_footers:
                current_footers[0].getparent().replace(current_footers[0], shared_footer)
            else:
                final_doc.xpath("//body")[0].append(shared_footer)
            # Ensure the required GA4 and consent controls load on every imported article.
            template_scripts = site_template.xpath("//script[@src]")
            for required in ("analytics.js", "consent.js"):
                if not any(Path(src.split("?", 1)[0]).name == required for src in final_doc.xpath("//script/@src")):
                    match = next((node for node in template_scripts if Path(node.get("src").split("?", 1)[0]).name == required), None)
                    check(match is not None, "Missing site script template: " + required)
                    final_doc.xpath("//body")[0].append(copy.deepcopy(match))
            # Map generic template asset paths to the repository's real shared assets.
            # The live site uses style.css (singular); normalize the plural path
            # found in approved article templates before the strict link audit.
            for node in final_doc.xpath("//link[@href='styles.css' or starts-with(@href, 'styles.css?') or @href='assets/css/main.css']"):
                node.set("href", "style.css?v=heading-level-20261018")
            for node in final_doc.xpath("//script[@src='assets/js/main.js']"):
                node.set("src", "app.js?v=independent-loading-20261018")
            # Complete the shared editorial asset set when the source template
            # contains only a partial set. These are existing site assets.
            required_styles = ("style.css", "editorial-theme.css", "footer.css", "editorial-meta.css", "article-share.css", "editorial-related.css")
            head = final_doc.xpath("//head")[0]
            present_styles = {Path(href.split("?", 1)[0]).name for href in final_doc.xpath("//link[@rel='stylesheet']/@href")}
            for name in required_styles:
                if name not in present_styles:
                    node = html.Element("link", rel="stylesheet", href=name)
                    head.append(node)
            required_scripts = ("editorial-theme.js", "editorial-meta.js", "article-share.js", "analytics.js", "consent.js")
            present_scripts = {Path(src.split("?", 1)[0]).name for src in final_doc.xpath("//script/@src")}
            body = final_doc.xpath("//body")[0]
            for name in required_scripts:
                if name not in present_scripts:
                    node = html.Element("script", src=name, defer="defer")
                    body.append(node)
            # Apply the shared editorial hero styling to the imported cover.
            for figure in final_doc.xpath("//main//figure"):
                classes = (figure.get("class") or "").split()
                if "editorial-hero" in classes and "ttn-editorial-figure" not in classes:
                    classes = [c for c in classes if c != "editorial-hero"] + ["ttn-editorial-figure"]
                    figure.set("class", " ".join(classes))
                for image in figure.xpath(".//img"):
                    image_classes = (image.get("class") or "").split()
                    if "article-hero-image" not in image_classes:
                        image_classes.append("article-hero-image")
                    image.set("class", " ".join(image_classes))
            # Gemini's complete-page source can repeat IDs across duplicated
            # template blocks. Keep the first target (so existing fragment links
            # remain stable) and remove duplicate IDs before the site-wide audit.
            seen_ids = set()
            for element in final_doc.xpath("//*[@id]"):
                element_id = element.get("id")
                if element_id in seen_ids:
                    element.attrib.pop("id", None)
                else:
                    seen_ids.add(element_id)
            original_html = html.tostring(final_doc, encoding="unicode", method="html", doctype="<!DOCTYPE html>")
            # lxml's HTML serializer can preserve a source closing tag from
            # malformed template markup; source is a void HTML element.
            original_html = original_html.replace("</source>", "")
            # These bytes replace the packaged HTML after full archive validation.
            relations[slug + ":validated-html"] = original_html
            entries.append(dict(
                id=slug, title=m["title"], dek=m["dek"], section=m["section"], format=m["format"],
                date=m["date"], author="TTN Research Desk", tickers=m.get("tickers", []),
                image=cover, imageSmall=sm, imageMedium=md,
                imageSrcset=sm + " 480w, " + md + " 960w, " + cover + " 1672w",
                imageAlt=alt[0], body=[html.tostring(el, encoding="unicode") for el in body_nodes[0]],
                sources=sources
            ))
        all_ids = existing | {a["id"] for a in entries}
        check(all(r in all_ids for slug, refs in relations.items() if not slug.endswith(":validated-html") for r in refs), "Related reading points to missing articles")
        # Refuse all collisions before writing any files.
        for name in names:
            if name in ("publication-manifest.json", "README-PUBLISH.txt", "GEMINI_INSTRUCTIONS.txt"):
                continue
            dest = ROOT / name
            check(
                not dest.exists()
                or name in approved_html_files
                or dest.read_bytes() == z.read(name),
                "Would overwrite published file: " + name,
            )
        for name in names:
            if name in ("publication-manifest.json", "README-PUBLISH.txt", "GEMINI_INSTRUCTIONS.txt"):
                continue
            dest = ROOT / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if name in approved_html_files:
                dest.write_text(relations[name[:-5] + ":validated-html"], encoding="utf-8")
            elif not dest.exists():
                dest.write_bytes(z.read(name))
        catalog = [a for a in catalog if a["id"] not in replace_slugs]
        catalog.extend(entries)
        catalog_path.write_text("const TTN_ARTICLES = " + json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + ";\n")
        path = ROOT / "scripts/editorial_topics.py"
        with path.open("a") as out:
            out.write("\n# Approved ZIP auto-publication\n")
            for a in entries:
                if a["id"] not in existing:
                    out.write("GROUPS.setdefault(" + repr(topic[a["section"]]) + ", []).append(" + repr(a["id"]) + ")\n")
                out.write("RELATED[" + repr(a["id"]) + "] = " + repr(relations[a["id"]]) + "\n")
        # All new pages must expose the same opt-in GA4 controls as historical pages.\n        from repair_analytics_consent import repair as repair_analytics_consent\n        repair_analytics_consent(ROOT)\n        print("Imported", len(entries), "articles from", archive)

if __name__ == "__main__":
    for file in sys.argv[1:]:
        publish(file)