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
    'BCS': ('NYSE:BCS', 'Barclays ADR · NYSE'),
    'NOK': ('NYSE:NOK', 'Nokia ADR · NYSE'),
    'RAND': ('EURONEXT:RAND', 'Randstad · Euronext Amsterdam'),
    **{s: (f'NASDAQ:{s}', s) for s in ['SOFI','HON','COIN','AAPL','NVDA','INTC','CRWV','AMZN','MSFT','GOOGL','AVGO','TSLA','META','MU','BRZE','ASML']},
    **{s: (f'NYSE:{s}', s) for s in ['UBER','V','LMT','SPOT','LEN','DHI','ORCL','TSM','CRM','BABA','MMM']},
    'S&P 500': ('FOREXCOM:SPXUSD', 'S&P 500 CFD · FOREX.com'),
    'NASDAQ': ('FOREXCOM:NSXUSD', 'Nasdaq-100 CFD · FOREX.com'),
    'Nasdaq Composite': ('NASDAQ:IXIC', 'Nasdaq Composite'),
    'Nasdaq-100': ('NASDAQ:NDX', 'Nasdaq-100'),
    'Dow Jones': ('TVC:DJI', 'Dow Jones Industrial Average'),
    'BTC': ('BINANCE:BTCUSDT', 'Bitcoin / Tether · Binance'),
    'ETH': ('BINANCE:ETHUSDT', 'Ethereum / Tether · Binance'),
    'SOL': ('COINBASE:SOLUSD', 'Solana / USD · Coinbase'),
    'XRP': ('BITSTAMP:XRPUSD', 'XRP / USD · Bitstamp'),
    'GOLD': ('TVC:GOLD', 'Gold · TVC'),
    'OIL': ('TVC:USOIL', 'WTI Oil · TVC'),
    'Brent Oil': ('FX:UKOIL', 'Brent Oil CFD · FXCM'),
    'EUR/USD': ('FX:EURUSD', 'EUR/USD · FXCM'),
    'GBP/USD': ('FX:GBPUSD', 'GBP/USD · FXCM'),
}
ALIASES = {'EURUSD':'EUR/USD', 'GBPUSD':'GBP/USD'}
# Match actual instrument names in editorial copy, not sources, related reading,
# the Nasdaq exchange as a company, or Dow Jones as a news publisher.
MENTIONS = {
    'S&P 500': r'\bS\s*&\s*P\s*500\b',
    'Nasdaq Composite': r'\bNasdaq\s+Composite\b',
    'Nasdaq-100': r'\bNasdaq[-\s]+100\b',
    'Dow Jones': r'\bDow(?:\s+Jones)?\s+Industrial\s+Average\b',
    'BTC': r'\bBitcoin\b|\bBTC\b',
    'ETH': r'\bEthereum\b|\bEther\b|\bETH\b',
    'SOL': r'\bSolana\b',
    'XRP': r'\bXRP\b',
    'GOLD': r'\bgold\b',
    'OIL': r'\bWTI\b|\bWest Texas Intermediate\b',
    'Brent Oil': r'\bBrent\b',
}
TAG_XPATH = '//*[contains(concat(" ",normalize-space(@class)," ")," article-ticker-tag ")]'

def expected_tickers(article, doc):
    body = doc.xpath('//section[@class="editorial-body"]')
    assert len(body) == 1, article['id']
    copy = ' '.join([article['title'], article.get('dek',''), body[0].text_content()])
    labels = list(dict.fromkeys(ALIASES.get(t,t) for t in article.get('tickers',[])))
    for label, pattern in MENTIONS.items():
        if re.search(pattern, copy, re.I) and label not in labels:
            labels.append(label)
    # A Composite reading must not silently open the Nasdaq-100 broker CFD.
    if 'Nasdaq Composite' in labels and 'NASDAQ' in labels:
        labels.remove('NASDAQ')
    for label in labels:
        if label not in INSTRUMENTS:
            raise ValueError(f"{article['id']}: verify TradingView mapping for {label}")
    return labels

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
    for article in articles:
        page=root/(article['id']+'.html');text=page.read_text();before=text
        doc=html.fromstring(text);labels=expected_tickers(article,doc)
        tags=doc.xpath(TAG_XPATH)
        actual=[(e.get('data-label'),e.get('data-tv')) for e in tags]
        expected=[(label,INSTRUMENTS[label][0]) for label in labels]
        # Existing controls can retain their familiar labels and markup. Rebuild
        # only incomplete/wrong blocks, so this is not a site-wide layout rewrite.
        actual_symbols=[s for _,s in actual]
        if sorted(actual_symbols)!=sorted(s for _,s in expected) or len(actual_symbols)!=len(set(actual_symbols)):
            text=re.sub(r'<div\b[^>]*class="article-tickers"[^>]*>.*?</div>\s*','',text,flags=re.S)
            if labels:
                body_end=text.index('</section>',text.index('<section class="editorial-body">'))+len('</section>')
                text=text[:body_end]+ticker_block(labels)+text[body_end:]
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
