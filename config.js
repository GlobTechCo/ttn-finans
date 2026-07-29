/**
 * TTN — site configuration
 * ------------------------------------------------------------
 * All API keys and data sources live here.
 * Free APIs need no key. For stock indices/gold it's recommended
 * to add a free Twelve Data key (800 requests/day):
 * https://twelvedata.com/pricing  -> "Basic" (free)
 *
 * If a key is left blank, those tickers show demo data
 * (marked with a DEMO badge) — the site stays fully functional.
 * ------------------------------------------------------------
 */

const TTN_CONFIG = {
  // Free Twelve Data key (for S&P 500, Nasdaq, Gold)
  TWELVE_DATA_KEY: "", // <-- paste your key here

  // Free CoinGecko "Demo" key — raises the free rate limit for BTC/ETH prices
  // Sign up: https://www.coingecko.com/en/api/pricing (Demo plan is free)
  // Without a key, CoinGecko still works but may fall back to demo data
  // more often if the shared public rate limit is hit.
  COINGECKO_KEY: "", // <-- paste your key here (optional)

  // Free Finnhub key (finnhub.io) — supplementary news source
  // Sign up: https://finnhub.io/register (free, 60 req/min)
  // Without a key this is simply skipped — news still loads from RSS below
  FINNHUB_KEY: "", // <-- paste your key here (optional)

  // Free Currents API key — structured news JSON with real per-article
  // images more often than RSS. Free tier explicitly allows commercial use.
  // Sign up: https://currentsapi.services (free, no card, ~600-1000 req/day)
  CURRENTS_KEY: "", // <-- paste your key here (optional)

  // Free APITube key — structured news JSON with sentiment/category data
  // and real per-article images. Free tier explicitly allows commercial use.
  // Sign up: https://apitube.io (free, no card, 1000 req/day)
  APITUBE_KEY: "", // <-- paste your key here (optional)

  // Free rss2json.com key (raises the daily news request limit)
  // Works without a key too, just with a lower daily limit
  RSS2JSON_KEY: "", // <-- paste your key here (optional)

  // Free Pexels key — guarantees a real, relevant photo on every news card
  // even when the source's own RSS feed has no image at all (common with
  // Seeking Alpha, Investing.com, and others). Without a key, cards with
  // no source photo fall back to a plain icon instead.
  // Sign up: https://www.pexels.com/api/ (free, no card required)
  PEXELS_KEY: "egFatky8LlcBGp4hdoSNHslhOcGbX4m7wZr3x4Nptc2HKWlZv6NQjkgn", // <-- paste your key here (optional but recommended)

  // Price refresh interval (ms)
  PRICE_REFRESH_MS: 45000,

  // Search terms used to pull a relevant Pexels stock photo per news
  // category when the source itself provides no image
  CATEGORY_PHOTO_QUERIES: {
    crypto: "cryptocurrency bitcoin coins",
    stocks: "stock market trading screen",
    forex: "currency exchange money",
    gold: "gold bars bullion",
    oil: "oil tanker crude petroleum",
    chips: "semiconductor microchip technology",
    bonds: "stock market graph decline",
    general: "financial newspaper business",
  },

  // Tickers shown in the top strip
  TICKERS: [
    {
      id: "btc",
      label: "Bitcoin",
      symbol: "BTC",
      type: "crypto",
      coingeckoId: "bitcoin",
      tvSymbol: "BINANCE:BTCUSDT",
      demoBase: 64500,
    },
    {
      id: "eth",
      label: "Ethereum",
      symbol: "ETH",
      type: "crypto",
      coingeckoId: "ethereum",
      tvSymbol: "BINANCE:ETHUSDT",
      demoBase: 1870,
    },
    {
      id: "spx",
      label: "S&P 500",
      symbol: "SPX",
      type: "index",
      twelveDataSymbol: "SPX",
      tvSymbol: "FOREXCOM:SPXUSD",
      demoBase: 6280,
    },
    {
      id: "ndx",
      label: "Nasdaq",
      symbol: "NDX",
      type: "index",
      twelveDataSymbol: "NDX",
      tvSymbol: "FOREXCOM:NSXUSD",
      demoBase: 22950,
    },
    {
      id: "gold",
      label: "Gold",
      symbol: "XAU/USD",
      type: "commodity",
      twelveDataSymbol: "XAU/USD",
      tvSymbol: "TVC:GOLD",
      demoBase: 3380,
    },
    {
      id: "eurusd",
      label: "EUR/USD",
      symbol: "FX",
      type: "forex",
      // Frankfurter — free, no key, CORS-enabled
      frankfurterPair: { from: "EUR", to: "USD" },
      tvSymbol: "FX:EURUSD",
      demoBase: 1.16,
    },
  ],

  // Financial news RSS sources (aggregated, never rewritten).
  // Verified working as of July 2026 — RSS URLs for financial sites change
  // more often than you'd expect; MarketWatch's own domain feed died and
  // moved to a Dow Jones-hosted URL, and Reuters killed its public RSS
  // entirely (no reliable free replacement, so it's not included here —
  // see README for details on why).
  NEWS_FEEDS: [
    { name: "CNBC Markets", url: "https://www.cnbc.com/id/100003114/device/rss/rss.html" },
    { name: "MarketWatch", url: "https://feeds.content.dowjones.io/public/rss/mw_topstories" },
    { name: "Yahoo Finance", url: "https://finance.yahoo.com/news/rssindex" },
    { name: "Business Insider", url: "https://markets.businessinsider.com/rss/news" },
    { name: "Investing.com", url: "https://www.investing.com/rss/news_25.rss" },
    { name: "Seeking Alpha", url: "https://seekingalpha.com/feed.xml" },
  ],

  // Ticker dictionary for auto-detecting assets mentioned in news headlines/descriptions.
  // trackedId links back to an entry in TICKERS above (reuses its already-live % change).
  // coingeckoId lets extra crypto tickers pull a live price independently of TICKERS.
  // Entries with neither only show a live % if a Finnhub key is set (stock quotes).
  TICKER_DICTIONARY: [
    { match: ["bitcoin", "btc"], label: "BTC", tvSymbol: "BINANCE:BTCUSDT", trackedId: "btc" },
    { match: ["ethereum", "eth", "ether"], label: "ETH", tvSymbol: "BINANCE:ETHUSDT", trackedId: "eth" },
    { match: ["tesla", "tsla"], label: "TSLA", tvSymbol: "NASDAQ:TSLA" },
    { match: ["apple", "aapl"], label: "AAPL", tvSymbol: "NASDAQ:AAPL" },
    { match: ["nvidia", "nvda"], label: "NVDA", tvSymbol: "NASDAQ:NVDA" },
    { match: ["microsoft", "msft"], label: "MSFT", tvSymbol: "NASDAQ:MSFT" },
    { match: ["amazon", "amzn"], label: "AMZN", tvSymbol: "NASDAQ:AMZN" },
    { match: ["meta platforms", "meta ", "facebook"], label: "META", tvSymbol: "NASDAQ:META" },
    { match: ["google", "alphabet", "googl"], label: "GOOGL", tvSymbol: "NASDAQ:GOOGL" },
    { match: ["berkshire hathaway", "berkshire"], label: "BRK-B", tvSymbol: "NYSE:BRK.B" },
    { match: ["s&p 500", "s&p500", "sp500"], label: "S&P 500", tvSymbol: "FOREXCOM:SPXUSD", trackedId: "spx" },
    { match: ["nasdaq"], label: "NASDAQ", tvSymbol: "FOREXCOM:NSXUSD", trackedId: "ndx" },
    { match: ["dow jones", "dow "], label: "DOW", tvSymbol: "TVC:DJI" },
    { match: ["gold"], label: "GOLD", tvSymbol: "TVC:GOLD", trackedId: "gold" },
    { match: ["oil", "crude"], label: "OIL", tvSymbol: "TVC:USOIL" },
    { match: ["euro", "eur/usd", "eurusd"], label: "EUR/USD", tvSymbol: "FX:EURUSD", trackedId: "eurusd" },
    { match: ["dogecoin", "doge"], label: "DOGE", tvSymbol: "BINANCE:DOGEUSDT", coingeckoId: "dogecoin" },
    { match: ["solana", "sol "], label: "SOL", tvSymbol: "BINANCE:SOLUSDT", coingeckoId: "solana" },
    { match: ["ripple", "xrp"], label: "XRP", tvSymbol: "BINANCE:XRPUSDT", coingeckoId: "ripple" },
  ],
};
