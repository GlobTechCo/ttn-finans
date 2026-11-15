#!/usr/bin/env python3
"""Trim five over-length TTN articles to the approved 700-900 word range."""
from html.parser import HTMLParser
from html import unescape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "articles.js"
CUTS = {
 "trm-labs-beacon-concierge-law-enforcement-crypto-freezing-2026": [
  "Cryptocurrency transactions are recorded",
  "The service is designed to cover investigations across different blockchains",
  "TRM has pointed to the Beacon Network's work related to the Binance exploit",
  "TRM also reported that participating network members generated more than 45,000 alerts",
  "For individual investigators, manually following every transaction path can be difficult",
  "The main change introduced by Beacon Concierge is broader access to coordinated support",
  "By offering a managed service without requiring a TRM licence",
  "The model reflects a wider development in digital-asset enforcement"
 ],
 "bitcoin-four-month-low-crypto-liquidations-november-2026": [
  "The price observations refer to different trading periods",
  "The resulting sale can push prices lower",
  "The combination of ETF withdrawals and large derivatives liquidations nevertheless points to pressure",
  "The latest fall demonstrates how several different pressures can reinforce each other",
  "For now, the data point to a market under stress"
 ],
 "xfusion-1-2-billion-ai-server-ipo-2026": [
  "The committee's questions therefore point to the issues potential investors are likely to examine in greater detail",
  "These risks are particularly relevant in the AI server market",
  "The market's development will depend not only on the number of AI projects announced",
  "The planned 8 billion yuan offering could provide resources for expansion"
 ],
 "european-earnings-growth-stoxx-600-energy-2026": [
  "The figures also show why aggregate earnings estimates should not be treated as a complete measure of economic strength",
  "The 25% earnings-growth forecast is a strong headline",
  "For now, the STOXX 600 reporting season points to a meaningful improvement"
 ],
 "samsung-ai-data-center-infrastructure-expansion-november-2026": [
  "The same structure that gives Samsung its breadth could make the strategy difficult to execute",
  "Those businesses could benefit even if the group does not become a major independent data-center operator",
  "Samsung is trying to move up the AI value chain at a time when infrastructure demand is expanding"
 ]
}


CUTS.update({
 "ai-inference-unit-economics-2026": ["High utilization is not sufficient if it produces unacceptable queues", "A credible assessment reports accepted volume, error rates, retries, human effort, latency and the cost boundary"],
 "stablecoins-explained-depeg-risk": ["Check the issuer, asset composition, reserve-report date, redemption eligibility, costs and relevant legal terms", "Compare the product with"],
 "free-cash-flow-explained": ["Free cash flow is commonly used to describe the cash a company generates after capital spending", "Evaluate several periods, the company's definition, working-capital movements and capital-spending plans", "When reviewing"],
 "global-equity-funds-3863-billion-inflows-november-2026": ["Next week's fund reports will be more useful for assessing whether the latest AI-related volatility led to a sustained reduction", "For now, the clearest conclusion is narrower than either a bullish or bearish headline might suggest"],
 "microsoft-oracle-rented-ai-capacity-reassessment-2026": ["In separate reporting on November 6, Reuters said AI infrastructure provider IREN had experienced changes to network requirements", "These facts concern a different company and should not be merged into the Oracle rental story", "The investment case for data-center operators increasingly depends on both customer demand", "Customers face their own tradeoffs. Locking in capacity can provide certainty"],
 "binance-63-billion-heist-crypto-insurance-scrutiny-2026": ["The immediate question for insurance underwriters is not only what happened at Binance", "Such attacks can defeat security assumptions that rely on the integrity of trusted workstations", "Policies can also contain sublimits that restrict compensation for particular types of incidents", "Insurance is also not a substitute for maintaining sufficient liquidity", "That creates uncertainty at the point a business might need financial protection most", "There is a difference between an insurer requesting stronger controls and a regulator mandating them", "Future developments will include technical findings from the investigation", "Reuters' November 6 reporting points toward stricter questions from underwriters"],
 "credit-agricole-banco-bpm-merger-proposal-european-banks-rally-november-9": ["The evidence supports a narrow conclusion. Banks rose on specific corporate news"],
 "wall-street-rebounds-oil-falls-nvidia-diverges-november-9-2026": ["A sustainable recovery would require more than one session of relief"],
 "google-tpu-8tx-8i-max-ai-chips-cloud-november-9-2026": ["Context is the information a model can consider during a task", "Google began building TPUs more than a decade ago for internal workloads", "There is also a wider infrastructure question"],
 "pnc-coinbase-usdc-corporate-payments-pilot-november-9-2026": ["The attraction for corporate treasurers is therefore operational flexibility", "Those uncertainties do not negate the practical potential of the model", "PNC and Coinbase have moved beyond a general statement of interest in digital assets"],
 "australia-ai-safety-regulator-openai-agent-breach-november-10-2026": ["The implications reach beyond healthcare", "For policymakers, the challenge is to distinguish unintended system behavior", "The government still needs to translate its commitments into enforceable obligations"],
 "coinbase-kalshi-cftc-stock-perpetual-futures-lawsuit-november-10-2026": ["The industry coalition's composition is notable", "Whatever the eventual judgment, the case shows why technology borrowed from cryptocurrency markets"],
 "asian-stocks-kospi-nikkei-oil-us-cpi-november-10-2026": ["Lower oil prices can strengthen margins for energy-consuming businesses", "Three developments deserve particular attention:", "Asia's previous session already showed how quickly expectations can shift"],
 "brent-below-90-global-stocks-rise-us-cpi-day-november-10": ["CoreWeave reports after the bell, alongside D-Wave Quantum and Rigetti Computing"],
 "dollar-19-month-high-fed-december-hike-odds-30-year-auction-november-12-2026": ["Gold fell below $4,000 an ounce"],
 "msci-removes-strategy-index-november-30-bitcoin-treasury-november-12-2026": ["Investors will also follow the watchlist"],
 "nvidia-board-reportedly-preparing-remove-ceo-huang-november-12-2026": ["Further steps in the congressional inquiry are also possible"]
})

class ParagraphCounter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.in_p = False
        self.current = []
        self.paragraphs = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section" and "editorial-body" in attrs.get("class", "").split():
            self.in_body = True
        if self.in_body and tag == "p":
            self.in_p = True
            self.current = []
        if self.in_p and tag == "br":
            self.current.append(" ")
    def handle_endtag(self, tag):
        if tag == "p" and self.in_p:
            self.paragraphs.append("".join(self.current))
            self.in_p = False
        if tag == "section":
            self.in_body = False
    def handle_data(self, data):
        if self.in_p:
            self.current.append(data)

def count_words(text):
    parser = ParagraphCounter()
    parser.feed(text)
    return sum(len(p.split()) for p in parser.paragraphs)

def main():
    source = CATALOG.read_text(encoding="utf-8")
    prefix, payload = source.split("=", 1)
    articles = json.loads(payload.strip().removesuffix(";"))
    for slug, prefixes in CUTS.items():
        path = ROOT / (slug + ".html")
        text = path.read_text(encoding="utf-8")
        start = text.find('class="editorial-body"')
        end = text.find("</section>", start)
        if start < 0 or end < 0:
            raise ValueError("Editorial body missing: " + slug)
        before, body, after = text[:start], text[start:end], text[end:]
        removed = []
        for prefix in prefixes:
            paragraph = None
            for candidate in re.findall(r"<p\b[^>]*>[\s\S]*?</p>", body, re.I):
                plain = unescape(re.sub(r"<[^>]+>", " ", candidate)).strip()
                if plain.startswith(prefix):
                    paragraph = candidate
                    break
            if paragraph:
                body = body.replace(paragraph, "", 1)
                removed.append(prefix)
        text = before + body + after
        words = count_words(text)
        if not 700 <= words <= 900:
            raise ValueError(f"{slug}: resulting word count {words} is outside 700-900")
        # Keep Article structured data synchronized with the actual paragraph count.
        schema_re = re.compile(r'(<script\s+type=["\']application/ld\+json["\']\s*>)([\s\S]*?)(</script>)', re.I)
        m = schema_re.search(text)
        if not m:
            raise ValueError("JSON-LD missing: " + slug)
        schema = json.loads(m.group(2))
        schema["wordCount"] = words
        text = text[:m.start()] + m.group(1) + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + m.group(3) + text[m.end():]
        path.write_text(text, encoding="utf-8")
        print(f"PASS: {slug}: {words} words; removed {len(removed)} repetitive paragraphs.")

if __name__ == "__main__":
    main()
