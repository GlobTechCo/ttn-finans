"""Static article chart controls, independent of the news-feed configuration."""
from pathlib import Path
import hashlib
import html as escape_html
import json
import re
from urllib.parse import quote
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
# Preserve established instruments; identify broker CFDs and quote currencies.
INSTRUMENTS = {
    'LLY': ('NYSE:LLY', 'Eli Lilly · NYSE'),
    'ICMB': ('NASDAQ:ICMB', 'Investcorp Credit Management BDC · Nasdaq'),
    'BCIC': ('NASDAQ:BCIC', 'BCP Investment Corporation · Nasdaq'),
    'IAG': ('BME:IAG', 'International Airlines Group · BME · EUR'),
    'WLFI': ('BINANCE:WLFIUSDT', 'WLFI / Tether · Binance'),
    'QCOM': ('NASDAQ:QCOM', 'Qualcomm · Nasdaq'),
    'AGLT': ('NASDAQ:AGLT', 'Agility Robotics · Nasdaq'),
    'AAVE': ('COINBASE:AAVEUSD', 'Aave / USD · Coinbase'),
    'BOX': ('NYSE:BOX', 'Box · NYSE'),
    'WEN': ('NASDAQ:WEN', 'Wendy’s · Nasdaq'),
    'MAERSK_B': ('OMXCOP:MAERSK_B', 'A.P. Moller - Maersk B · Nasdaq Copenhagen'),
    'RIOT': ('NASDAQ:RIOT', 'Riot Platforms · Nasdaq'),
    'KD': ('NYSE:KD', 'Kyndryl · NYSE'),
    'CNTN': ('NASDAQ:CNTN', 'Canton Strategic Holdings · Nasdaq'),
    'US10Y': ('TVC:US10Y', 'U.S. 10-Year Treasury Yield · TVC'),
    '700': ('HKEX:700', 'Tencent Holdings · Hong Kong Exchange'),
    'NVO': ('NYSE:NVO', 'Novo Nordisk ADR · NYSE'),
    'BMW': ('XETR:BMW', 'BMW · Xetra'),
    'PLTR': ('NASDAQ:PLTR', 'Palantir Technologies · Nasdaq'),
    '2222': ('TADAWUL:2222', 'Saudi Aramco · Saudi Exchange'),
    'CAP': ('EURONEXT:CAP', 'Capgemini · Euronext Paris'),
    'VST': ('NYSE:VST', 'Vistra Corp. · NYSE'),
    'XOM': ('NYSE:XOM', 'ExxonMobil · NYSE'),
    'CVX': ('NYSE:CVX', 'Chevron · NYSE'),
    'TM': ('NYSE:TM', 'Toyota ADR · NYSE'),
    'MSTR': ('NASDAQ:MSTR', 'Strategy · Nasdaq'),
    'BP': ('NYSE:BP', 'BP ADS · NYSE'),
    'SBUX': ('NASDAQ:SBUX', 'Starbucks · Nasdaq'),
    'RDDT': ('NYSE:RDDT', 'Reddit · NYSE'),
    'TOST': ('NYSE:TOST', 'Toast · NYSE'),
    'ICE': ('NYSE:ICE', 'Intercontinental Exchange · NYSE'),
    'NOW': ('NYSE:NOW', 'ServiceNow · NYSE'),
    'STM': ('NYSE:STM', 'STMicroelectronics · NYSE'),
    'XLM': ('COINBASE:XLMUSD', 'Stellar / USD · Coinbase'),
    'SHEL': ('NYSE:SHEL', 'Shell ADS · NYSE'),
    'LYG': ('NYSE:LYG', 'Lloyds Banking Group ADR · NYSE'),
    'F': ('NYSE:F', 'Ford Motor · NYSE'),
    'SAP': ('NYSE:SAP', 'SAP ADR · NYSE'),
    'HOOD': ('NASDAQ:HOOD', 'Robinhood Markets · Nasdaq'),
    'GSAT': ('NASDAQ:GSAT', 'Globalstar · Nasdaq'),
    'BA': ('NYSE:BA', 'Boeing · NYSE'),
    'CRCL': ('NYSE:CRCL', 'Circle Internet Group · NYSE'),
    'ACIW': ('NASDAQ:ACIW', 'ACI Worldwide · Nasdaq'),
    'KO': ('NYSE:KO', 'Coca-Cola · NYSE'),
    'GWRE': ('NYSE:GWRE', 'Guidewire Software · NYSE'),
    'ZEC': ('BINANCE:ZECUSDT', 'Zcash / Tether · Binance'),
    'IFX': ('XETR:IFX', 'Infineon Technologies · Xetra'),
    'EWZ': ('AMEX:EWZ', 'iShares MSCI Brazil ETF'),
    'IBIT': ('NASDAQ:IBIT', 'iShares Bitcoin Trust ETF · Nasdaq'),
    'FBTC': ('BATS:FBTC', 'Fidelity Wise Origin Bitcoin Fund · Cboe BZX'),
    'GBTC': ('AMEX:GBTC', 'Grayscale Bitcoin Trust ETF · NYSE Arca'),
    'ARKB': ('BATS:ARKB', 'ARK 21Shares Bitcoin ETF · Cboe BZX'),
    'BITB': ('AMEX:BITB', 'Bitwise Bitcoin ETF · NYSE Arca'),
    'NXT': ('ASX:NXT', 'NEXTDC · ASX'),
    'VWAGY': ('OTC:VWAGY', 'Volkswagen · OTC'),
    'XYZ': ('NYSE:XYZ', 'Block · NYSE'),
    'SOBKY': ('OTC:SOBKY', 'SoftBank Corp. ADR · OTC'),
    'BCS': ('NYSE:BCS', 'Barclays ADR · NYSE'),
    'NOK': ('NYSE:NOK', 'Nokia ADR · NYSE'),
    'BTGO': ('NYSE:BTGO', 'BitGo Holdings · NYSE'),
    'SNPS': ('NASDAQ:SNPS', 'Synopsys · Nasdaq'),
    'RAND': ('EURONEXT:RAND', 'Randstad · Euronext Amsterdam'),
    **{s: (f'NASDAQ:{s}', s) for s in ['DASH','CART','AMD','TEM','SPCX','SOFI','HON','COIN','AAPL','NVDA','INTC','CRWV','AMZN','MSFT','GOOGL','AVGO','TSLA','META','MU','BRZE','ASML']},
    **{s: (f'NYSE:{s}', s) for s in ['EQT','RRC','UBS','SLB','BMY','AXP','CCI','MA','HSBC','UBER','V','LMT','SPOT','LEN','DHI','ORCL','TSM','CRM','BABA','MMM']},
    'S&P 500': ('FOREXCOM:SPXUSD', 'S&P 500 CFD · FOREX.com'),
    'NASDAQ': ('FOREXCOM:NSXUSD', 'Nasdaq-100 CFD · FOREX.com'),
    'Nasdaq Composite': ('NASDAQ:IXIC', 'Nasdaq Composite'),
    'Nasdaq-100': ('FOREXCOM:NSXUSD', 'Nasdaq-100 CFD · FOREX.com'),
    'Dow Jones': ('TVC:DJI', 'Dow Jones Industrial Average'),
    'BTC': ('BINANCE:BTCUSDT', 'Bitcoin / Tether · Binance'),
    'ETH': ('BINANCE:ETHUSDT', 'Ethereum / Tether · Binance'),
    'INIT': ('BINANCE:INITUSDT', 'Initia / Tether · Binance'),
    'SOL': ('COINBASE:SOLUSD', 'Solana / USD · Coinbase'),
    'XRP': ('BITSTAMP:XRPUSD', 'XRP / USD · Bitstamp'),
    'GOLD': ('TVC:GOLD', 'Gold · TVC'),
    'OIL': ('TVC:USOIL', 'WTI Oil · TVC'),
    'Brent Oil': ('FX:UKOIL', 'Brent Oil CFD · FXCM'),
    'EUR/USD': ('FX:EURUSD', 'EUR/USD · FXCM'),
    'GBP/USD': ('FX:GBPUSD', 'GBP/USD · FXCM'),
}
ALIASES = {'EURUSD':'EUR/USD', 'GBPUSD':'GBP/USD', 'NYSE:PLTR':'PLTR', 'TADAWUL:2222':'2222', 'NDX':'Nasdaq-100', 'SPX':'S&P 500', 'UKOIL':'Brent Oil'}
# Explicit exchange-qualified aliases and legacy instruments retained by the article catalog.
ALIASES.update({
    'NASDAQ:NVDA':'NVDA','NASDAQ:AMD':'AMD','NASDAQ:COIN':'COIN','NASDAQ:GOOGL':'GOOGL',
    'NASDAQ:CRWV':'CRWV','NASDAQ:MSTR':'MSTR','NASDAQ:IBIT':'IBIT','NASDAQ:IXIC':'Nasdaq Composite',
    'NYSE:TSM':'TSM','TVC:US10Y':'US10Y','TVC:GOLD':'GOLD',
})
INSTRUMENTS.update({
    'BNB': ('BINANCE:BNBUSDT', 'BNB / Tether · Binance'),
    'ETHA': ('NASDAQ:ETHA', 'iShares Ethereum Trust ETF · Nasdaq'),
    'TVC:TWII': ('TVC:TWII', 'Taiwan Weighted Index · TVC'),
    'TVC:NI225': ('TVC:NI225', 'Nikkei 225 · TVC'),
    'TVC:UKOIL': ('TVC:UKOIL', 'Brent Crude Oil · TVC'),
    'FX_IDC:USDJPY': ('FX_IDC:USDJPY', 'U.S. Dollar / Japanese Yen · IDC'),
    'BITSTAMP:BTCUSD': ('BITSTAMP:BTCUSD', 'Bitcoin / U.S. Dollar · Bitstamp'),
    'BITSTAMP:ETHUSD': ('BITSTAMP:ETHUSD', 'Ether / U.S. Dollar · Bitstamp'),
    'COINBASE:BTCUSD': ('COINBASE:BTCUSD', 'Bitcoin / U.S. Dollar · Coinbase'),
    'COINBASE:ETHUSD': ('COINBASE:ETHUSD', 'Ether / U.S. Dollar · Coinbase'),
    'KRX:000660': ('KRX:000660', 'SK Hynix · Korea Exchange'),
    'SIX:UBSG': ('SIX:UBSG', 'UBS Group · SIX Swiss Exchange'),
    'FX_IDC:USDCHF': ('FX_IDC:USDCHF', 'U.S. Dollar / Swiss Franc · IDC'),
    'FX_IDC:EURCHF': ('FX_IDC:EURCHF', 'Euro / Swiss Franc · IDC'),
    'KRX:005930': ('KRX:005930', 'Samsung Electronics · Korea Exchange'),
    'MIL:BAMI': ('MIL:BAMI', 'Banco BPM · Borsa Italiana'),
    'EURONEXT:ACA': ('EURONEXT:ACA', 'Crédit Agricole · Euronext Paris'),
    'MIL:UCG': ('MIL:UCG', 'UniCredit · Borsa Italiana'),
    'TSE:9434': ('TSE:9434', 'SoftBank Corp. · Tokyo Stock Exchange'),
    'TSE:9984': ('TSE:9984', 'SoftBank Group · Tokyo Stock Exchange'),
    'SP:SPX': ('SP:SPX', 'S&P 500 Index · SP'),
    'DJ:DJI': ('DJ:DJI', 'Dow Jones Industrial Average · DJ'),
    'NYSE:CEG': ('NYSE:CEG', 'Constellation Energy · NYSE'),
    'NASDAQ:GOOG': ('NASDAQ:GOOG', 'Alphabet Class C · Nasdaq'),
    'NYSE:PNC': ('NYSE:PNC', 'PNC Financial Services · NYSE'),
    'XETR:ENR': ('XETR:ENR', 'Siemens Energy · Xetra'),
    'LSE:EZJ': ('LSE:EZJ', 'easyJet · London Stock Exchange'),
    'NYSE:DB': ('NYSE:DB', 'Deutsche Bank ADR · NYSE'),
    'TVC:DXY': ('TVC:DXY', 'U.S. Dollar Index · TVC'),
    'TVC:US30Y': ('TVC:US30Y', 'U.S. 30-Year Treasury Yield · TVC'),
    'TSE:3350': ('TSE:3350', 'Metaplanet · Tokyo Stock Exchange'),
    'NASDAQ:NDX': ('NASDAQ:NDX', 'Nasdaq-100 Index · Nasdaq'),
    'NASDAQ:SMH': ('NASDAQ:SMH', 'VanEck Semiconductor ETF · Nasdaq'),
    'HIVE': ('NASDAQ:HIVE', 'HIVE Digital Technologies · Nasdaq'),
    'BAM': ('NYSE:BAM', 'Brookfield Asset Management · NYSE'),
    'BX': ('NYSE:BX', 'Blackstone · NYSE'),
})
# Match actual instrument names in editorial copy, not sources, related reading,
# the Nasdaq exchange as a company, or Dow Jones as a news publisher.
MENTIONS = {
    'VST': r'\bVistra\b',
    'S&P 500': r'\bS\s*&\s*P\s*500\b',
    'Nasdaq Composite': r'\bNasdaq\s+Composite\b',
    'Nasdaq-100': r'\bNasdaq[-\s]+100\b',
    'Dow Jones': r'\bDow(?:\s+Jones)?\s+Industrial\s+Average\b',
    'MSFT': r'\bMicrosoft\b',
    'GOOGL': r'\bGoogle\b|\bAlphabet\b',
    'META': r'\bMeta\b',
    'AAPL': r'\bApple\b',
    'AMZN': r'\bAmazon\b',
    'BTC': r'\bBitcoin\b|\bBTC\b',
    'ETH': r'\bEthereum\b|\bEther\b|\bETH\b',
    'SOL': r'\bSolana\b',
    'XRP': r'\bXRP\b',
    'GOLD': r'\bgold\b(?!\s+Coast\b)',
    'OIL': r'\bWTI\b|\bWest Texas Intermediate\b',
    'Brent Oil': r'\bBrent\b',
}
TAG_XPATH = '//*[contains(concat(" ",normalize-space(@class)," ")," article-ticker-tag ")]'

def network_only_mention(label, copy):
    """Do not turn a blockchain-network mention into a tradable asset ticker."""
    if label not in {'ETH', 'SOL'}:
        return False
    pattern = MENTIONS[label]
    matches = list(re.finditer(pattern, copy, re.I))
    if not matches:
        return False
    for match in matches:
        context = copy[max(0, match.start() - 65):min(len(copy), match.end() + 45)]
        network_context = re.search(r'\b(?:blockchain|network|chain|ecosystem|protocol)\b', context, re.I)
        financial_context = re.search(
            r'\b(?:price|trading|market|coin|token|investment|investor|ETF|holdings|USD|dollar|volume|capitalization)\b',
            context, re.I,
        )
        if not network_context or financial_context:
            return False
    return True

def expected_tickers(article, doc):
    body = doc.xpath('//section[@class="editorial-body"]')
    assert len(body) == 1, article['id']
    article_copy = body[0].xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," article-body ")]')
    if article_copy:
        # Internal context links must not create unrelated ticker matches.
        # Match instruments against the article's own prose, not linked article titles.
        body_copy = html.fromstring(html.tostring(article_copy[0], encoding="unicode"))
        for link in body_copy.xpath(".//a"):
            link.drop_tree()
        body_text = body_copy.text_content()
    else:
        body_text = body[0].text_content()
    copy = ' '.join([article['title'], article.get('dek',''), body_text])
    labels = list(dict.fromkeys(ALIASES.get(t,t) for t in article.get('tickers',[])))
    for label, pattern in MENTIONS.items():
        if re.search(pattern, copy, re.I) and label not in labels:
            if network_only_mention(label, copy):
                continue
            labels.append(label)
    # A Composite reading must not silently open the Nasdaq-100 broker CFD.
    if 'Nasdaq Composite' in labels and 'NASDAQ' in labels:
        labels.remove('NASDAQ')
    unknown = [label for label in labels if label not in INSTRUMENTS]
    if unknown:
        print(f"WARNING: {article['id']}: unmapped tickers {unknown}; retain article and process supported tickers")
    return [label for label in labels if label in INSTRUMENTS]

def matching_section_close(source, start):
    depth=0
    for match in re.finditer(r'</?section\b[^>]*>',source[start:],flags=re.I):
        if match.group(0).startswith('</'):
            depth-=1
        else:
            depth+=1
        if depth==0:
            return start+match.start()
    raise ValueError('Unclosed editorial-body section')


def matching_div_close(source, start):
    """Return the position immediately after the matching closing div."""
    depth = 0
    for match in re.finditer(r'</?div\b[^>]*>', source[start:], flags=re.I):
        token = match.group(0)
        if token.startswith('</'):
            depth -= 1
        elif not token.rstrip().endswith('/>'):
            depth += 1
        if depth == 0:
            return start + match.end()
    raise ValueError('Unclosed article-body div')


def ticker_block(labels):
    items=[]
    for label in labels:
        symbol, name=INSTRUMENTS[label]
        esc=lambda s:escape_html.escape(s,quote=True)
        url='https://www.tradingview.com/chart/?symbol='+quote(symbol,safe='')
        items.append(f'<a class="article-ticker-tag" href="{url}" data-tv="{esc(symbol)}" data-label="{esc(name)}" aria-label="Open {esc(name)} chart" title="{esc(name)}"><b>{esc(label)}</b></a>')
    return '<div class="article-tickers" aria-label="Instruments mentioned in this article">'+''.join(items)+'</div>'

def refresh_article_tickers(root=ROOT):
    articles=json.loads((root/'articles.js').read_text().split('=',1)[1].strip().removesuffix(';'))
    version=hashlib.sha256((root/'chart.js').read_bytes()).hexdigest()[:12]
    changed=[]
    template_doc=html.parse(str(root/'index.html'))
    template_footers=template_doc.xpath('//footer')
    if len(template_footers)!=1:
        raise ValueError('The canonical site footer template is missing or duplicated')
    shared_footer=html.tostring(template_footers[0],encoding='unicode',method='html')
    for article in articles:
        page=root/(article['id']+'.html');text=page.read_text();before=text
        # Collapse duplicate shared footers and keep the sole footer after </main>.
        footer_pattern=r'<footer\b[^>]*>.*?</footer>'
        footer_matches=list(re.finditer(footer_pattern,text,flags=re.S|re.I))
        for match in reversed(footer_matches[:-1]):
            text=text[:match.start()]+text[match.end():]
        year_script_pattern=r'<script\b[^>]*>\s*document\.getElementById\(["\']year["\']\)\.textContent\s*=\s*new Date\(\)\.getFullYear\(\);\s*</script>'
        text=re.sub(year_script_pattern,'',text,flags=re.S|re.I)
        footer_match=re.search(footer_pattern,text,flags=re.S|re.I)
        if footer_match:
            footer_html=footer_match.group()
            text=text[:footer_match.start()]+text[footer_match.end():]
        else:
            # Some legacy article pages have no footer at all. Add the canonical
            # site footer and move cookie preferences into it rather than duplicate the control.
            text=re.sub(r'<button\b[^>]*data-cookie-preferences[^>]*>.*?</button>\s*','',text,flags=re.S|re.I)
            footer_html=shared_footer
        if 'id="year"' not in footer_html:
            footer_html=re.sub(r'<span([^>]*)>\s*2026\s*</span>',r'<span\1 id="year">2026</span>',footer_html,count=1)
        year_script='<script>document.getElementById("year").textContent = new Date().getFullYear();</script>' if 'id="year"' in footer_html else ''
        # Put the sole footer after article sources and related reading; run its year
        # updater after the footer exists in the document.
        if '</body>' in text:
            text=text.replace('</body>','\n'+footer_html+year_script+'</body>',1)
        else:
            text+=footer_html+year_script
        if re.search(r'<link\b[^>]*href=["\']footer\.css(?:\?[^"\']*)?["\']',text,re.I) is None:
            text=text.replace('</head>','<link rel="stylesheet" href="footer.css"></head>',1)
        doc=html.fromstring(text);labels=expected_tickers(article,doc)
        tags=doc.xpath(TAG_XPATH)
        actual=[(e.get('data-label'),e.get('data-tv')) for e in tags]
        expected=[(label,INSTRUMENTS[label][0]) for label in labels]
        # Existing controls can retain their familiar labels and markup. Rebuild
        # only incomplete/wrong blocks, so this is not a site-wide layout rewrite.
        actual_symbols=[s for _,s in actual]
        # Remove old blocks and put tickers immediately after article copy, before sources.
        text=re.sub(r'<div\b[^>]*class="[^"]*\barticle-tickers\b[^"]*"[^>]*>.*?</div>\s*','',text,flags=re.S)
        if labels:
            section_start=text.index('<section class="editorial-body">')
            section_close=matching_section_close(text,section_start)
            body_match=re.search(r'<div\b(?=[^>]*class="[^"]*\barticle-body\b[^"]*")[^>]*>',text[section_start:section_close])
            body_start=section_start+body_match.start() if body_match else -1
            source_markers=('<aside class="editorial-sources"','<details class="editorial-sources"','<section class="article-sources"','<h2>Sources</h2>')
            source_positions=[p for marker in source_markers if (p:=text.find(marker,section_start,section_close))>=0]
            source_pos=min(source_positions) if source_positions else -1
            if body_start >= 0:
                # Insert immediately after the complete article-body wrapper,
                # before Related Reading and Sources.
                insert_at=matching_div_close(text, body_start)
            elif source_pos >= 0 and source_pos < section_close:
                insert_at=source_pos
            else:
                # Legacy pages can keep sources outside main; the ticker still
                # belongs immediately after the editorial copy, before section end.
                insert_at=section_close
            text=text[:insert_at]+ticker_block(labels)+text[insert_at:]
        if labels:
            pattern=r'<script\b[^>]*src="chart\.js[^\"]*"[^>]*></script>'
            script=f'<script defer src="chart.js?v={version}"></script>'
            if re.search(pattern,text):
                text=re.sub(pattern,script,text)
            else:
                text=text.replace('</body>',script+'</body>')
        if text!=before:
            page.write_text(text);changed.append(page.name)
    print(f'Checked {len(articles)} article ticker blocks; repaired {len(changed)} pages.')
    return changed

if __name__=='__main__':
    refresh_article_tickers()
