/**
 * TTN — live ticker price module
 *
 * The visible ticker strip is now TradingView's own "Ticker Tape" widget
 * (see index.html) — it needs no API key and has no rate limits, so it
 * never shows a DEMO badge.
 *
 * This module keeps running quietly in the background: it still fetches
 * CoinGecko / Frankfurter / Twelve Data prices, because the news ticker
 * chips (% change badges) and the Market Snapshot text both need real
 * numbers to work with — something TradingView's widget can't hand back
 * to us, since it's a sealed iframe.
 */
const TTNTickers = (() => {

  // Bound both response headers and JSON body parsing; a stalled provider
  // must not leave its consumer waiting indefinitely.
  async function fetchJSON(url, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } finally { clearTimeout(timer); }
  }

  const state = {}; // id -> { price, changePct, demo }

  function fmtPrice(v, opts = {}) {
    if (v == null || isNaN(v)) return "—";
    const decimals = opts.decimals ?? (v >= 1000 ? 2 : v >= 1 ? 2 : 4);
    return v.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  }

  function applyUpdate(id, price, changePct, isDemo) {
    state[id] = { price, changePct, demo: isDemo };
    document.dispatchEvent(new Event("ttn-prices-updated"));
  }

  async function fetchCrypto() {
    const cryptoTickers = TTN_CONFIG.TICKERS.filter((t) => t.type === "crypto");
    if (!cryptoTickers.length) return;
    const ids = cryptoTickers.map((t) => t.coingeckoId).join(",");
    try {
      const data = await fetchJSON(
        `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true`,
        TTN_CONFIG.COINGECKO_KEY
          ? { headers: { "x-cg-demo-api-key": TTN_CONFIG.COINGECKO_KEY } }
          : undefined
      );
      cryptoTickers.forEach((t) => {
        const d = data[t.coingeckoId];
        if (d) applyUpdate(t.id, d.usd, d.usd_24h_change ?? 0, false);
        else applyUpdate(t.id, null, null, true);
      });
    } catch (e) {
      cryptoTickers.forEach((t) => applyUpdate(t.id, null, null, true));
    }
  }

  async function fetchForex() {
    const fx = TTN_CONFIG.TICKERS.find((t) => t.type === "forex");
    if (!fx) return;
    let rate = null;
    let changePct = 0;
    try {
      const data = await fetchJSON(
        `https://api.frankfurter.app/latest?from=${fx.frankfurterPair.from}&to=${fx.frankfurterPair.to}`
      );
      rate = data.rates[fx.frankfurterPair.to];
    } catch (e) {
      applyUpdate(fx.id, null, null, true);
      return;
    }
    // Change % is best-effort — if it fails, still show the real current rate
    try {
      const prevData = await fetchJSON(
        `https://api.frankfurter.app/${shiftDate(-3)}?from=${fx.frankfurterPair.from}&to=${fx.frankfurterPair.to}`
      );
      const prevRate = Object.values(prevData.rates)[0] ?? rate;
      changePct = ((rate - prevRate) / prevRate) * 100;
    } catch (e) {
      changePct = 0;
    }
    applyUpdate(fx.id, rate, changePct, false);
  }

  function shiftDate(days) {
    const d = new Date();
    d.setDate(d.getDate() + days);
    return d.toISOString().slice(0, 10);
  }

  async function fetchTwelveData() {
    const symbols = TTN_CONFIG.TICKERS.filter((t) => t.twelveDataSymbol);
    if (!symbols.length) return;
    if (!TTN_CONFIG.TWELVE_DATA_KEY) {
      symbols.forEach((t) => applyUpdate(t.id, null, null, true));
      return;
    }
    for (const t of symbols) {
      try {
        const data = await fetchJSON(
          `https://api.twelvedata.com/quote?symbol=${encodeURIComponent(
            t.twelveDataSymbol
          )}&apikey=${TTN_CONFIG.TWELVE_DATA_KEY}`
        );
        if (data.close) {
          applyUpdate(t.id, parseFloat(data.close), parseFloat(data.percent_change ?? 0), false);
        } else {
          applyUpdate(t.id, null, null, true);
        }
      } catch (e) {
        applyUpdate(t.id, null, null, true);
      }
    }
  }


  async function refreshAll() {
    await Promise.allSettled([fetchCrypto(), fetchForex(), fetchTwelveData()]);
  }

  function init() {
    const firstLoad = refreshAll();
    setInterval(refreshAll, TTN_CONFIG.PRICE_REFRESH_MS);
    return firstLoad;
  }

  function getChangePct(id) {
    return state[id]?.demo ? null : (state[id]?.changePct ?? null);
  }

  function getState(id) {
    return state[id] || null;
  }

  return { init, fmtPrice, getChangePct, getState };
})();
