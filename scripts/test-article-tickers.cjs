/* Regression coverage for standalone article instruments in all three sections. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const base = process.env.TTN_TEST_BASE || 'http://127.0.0.1:8765/';
const shots = process.env.TTN_SCREENSHOT_DIR || '/tmp/ttn-crypto-browser';
fs.mkdirSync(shots, { recursive: true });
const cases = [
  ['coinbase-ireland-safeguarding-fine-october-2026', 'NASDAQ:COIN'],
  ['spotify-q3-2026-subscribers-ai-spending', 'NYSE:SPOT'],
  ['honeywell-q3-2026-automation-outlook', 'NASDAQ:HON'],
  ['barclays-q3-2026-profit-share-buyback', 'NYSE:BCS'],
  ['nokia-q3-2026-ai-cloud-network-orders', 'NYSE:NOK'],
  ['grayscale-in-kind-crypto-subscriptions-october-2026', 'BITSTAMP:XRPUSD'],
  ['us-oil-inventories-eia-october-21-2026', 'TVC:USOIL'],
  ['us-oil-inventories-eia-october-21-2026', 'FX:UKOIL'],
  ['solana-alpenglow-mainnet-october-2026', 'COINBASE:SOLUSD'],
  ['randstad-q3-2026-staffing-recovery', 'EURONEXT:RAND'],
  ['nvidia-dsx-europe-power-cooling-october-2026', 'NASDAQ:NVDA'],
  ['wall-street-close-october-19-2026-ai-rebound', 'FOREXCOM:SPXUSD'],
  ['micron-taichung-union-agreement-october-2026', 'NASDAQ:MU'],
  ['ai-stocks-oil-110-premarket-october-20-2026', 'FX:UKOIL'],
  ['bitcoin-rebound-etf-outflows-october-19-2026', 'BINANCE:BTCUSDT'],
];
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const mobile of [false, true]) for (const theme of ['light', 'dark']) {
      const name = (mobile ? 'mobile' : 'desktop') + '-' + theme;
      const context = await browser.newContext({
        viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 },
        isMobile: mobile, hasTouch: mobile, colorScheme: theme,
      });
      await context.addInitScript(t => localStorage.setItem('ttn-theme', t), theme);
      // Isolate the integration from third-party availability. Live provider
      // rendering is checked separately after deployment.
      await context.route('https://s3.tradingview.com/tv.js', route => route.fulfill({
        contentType: 'application/javascript',
        body: 'window.TradingView={widget:function(o){const d=document.createElement("div");d.setAttribute("data-chart-symbol",o.symbol);d.textContent=o.symbol;document.getElementById(o.container_id).appendChild(d);}};',
      }));
      const page = await context.newPage();
      const errors = []; page.on('pageerror', e => errors.push(e.message));
      for (const [id, symbol] of cases) {
        await page.goto(base + id + '.html', { waitUntil: 'domcontentloaded' });
        const control = page.locator('.static-page .article-ticker-tag[data-tv="' + symbol + '"]');
        await control.waitFor();
        assert.equal(new URL(await control.getAttribute('href')).searchParams.get('symbol'), symbol);
        await control.scrollIntoViewIfNeeded();
        assert(await control.evaluate(e => e.getBoundingClientRect().top > 300), 'Start at article-end control');
        await control.click();
        await page.locator('#tv-chart-container [data-chart-symbol="' + symbol + '"]').waitFor();
        assert(await page.locator('#chart-panel').isVisible());
        await page.waitForFunction(() => {
          const r = document.getElementById('chart-panel').getBoundingClientRect();
          return r.top >= 0 && r.top < 120 && r.bottom <= innerHeight;
        });
        assert((await page.locator('#chart-panel-title').innerText()).includes(symbol));
        await page.keyboard.press('Escape');
        assert(await page.locator('#chart-panel').isHidden());
        assert(await control.evaluate(e => e === document.activeElement));
        await control.press('Enter');
        assert(await page.locator('#chart-panel').isVisible());
        await page.getByRole('button', { name: 'Close chart', exact: true }).click();
        await control.press('Space');
        assert(await page.locator('#chart-panel').isVisible());
        await page.keyboard.press('Escape');
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
        if (id.startsWith('micron-')) {
          await control.scrollIntoViewIfNeeded();
          await page.screenshot({ path: path.join(shots, name + '-article-tickers.png') });
        }
      }
      // A second instrument must replace the first chart rather than keep a stale symbol.
      await page.locator('.article-ticker-tag[data-tv="COINBASE:SOLUSD"]').click();
      await page.locator('#tv-chart-container [data-chart-symbol="COINBASE:SOLUSD"]').waitFor();
      await page.locator('.article-ticker-tag[data-tv="BINANCE:ETHUSDT"]').click();
      await page.locator('#tv-chart-container [data-chart-symbol="BINANCE:ETHUSDT"]').waitFor();
      assert.deepEqual(errors, [], name + ' article JavaScript errors');
      await context.close();
      console.log('PASS:', name, 'Analysis/Tech/Crypto ticker activation, symbol switching, keyboard, focus and layout');
    }
    const nojs = await browser.newContext({ javaScriptEnabled: false });
    const page = await nojs.newPage();
    await page.goto(base + cases.find(([, symbol]) => symbol === 'NASDAQ:MU')[0] + '.html');
    assert.equal(new URL(await page.locator('.article-ticker-tag[data-tv="NASDAQ:MU"]').getAttribute('href')).searchParams.get('symbol'), 'NASDAQ:MU');
    assert(await page.locator('.editorial-body').isVisible());
    await nojs.close();
    const blocked = await browser.newContext();
    await blocked.route(/tradingview/, route => route.abort());
    const b = await blocked.newPage();
    await b.goto(base + cases.find(([, symbol]) => symbol === 'NASDAQ:MU')[0] + '.html');
    await b.locator('.article-ticker-tag[data-tv="NASDAQ:MU"]').click();
    await b.getByText('TradingView could not be loaded.', { exact: false }).waitFor();
    assert(await b.locator('.editorial-body').isVisible());
    await blocked.close();
    console.log('PASS: standalone no-JavaScript link and blocked-provider reading fallback');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
