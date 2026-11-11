// Exercise the actual floating share control and clipboard on recent articles.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const base = process.env.TTN_TEST_BASE || 'http://127.0.0.1:8765/';
const pages = [
  'coreweave-q3-2026-results-ai-spending.html',
  'siemens-energy-record-2026-data-center-power-demand.html',
  'nvidia-h200-china-procurement-export-controls-november-2026.html',
];

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  try {
    for (const viewport of [{width: 1365, height: 900}, {width: 390, height: 844}]) {
      const ctx = await browser.newContext({viewport, permissions: ['clipboard-read', 'clipboard-write']});
      await ctx.addInitScript(() => localStorage.setItem('ttn_cookie_consent', 'declined'));
      for (const file of pages) {
        const page = await ctx.newPage();
        const url = new URL(file, base).href;
        const response = await page.goto(url, {waitUntil: 'domcontentloaded'});
        assert.equal(response.status(), 200, file + ': HTTP status');
        const button = page.getByRole('button', {name: 'Copy article link'});
        await button.waitFor({state: 'visible'});
        const box = await button.boundingBox();
        assert(box && box.width >= 40 && box.width <= 60 && box.y >= viewport.height - 100,
          file + ': copy button is not a compact floating control');
        assert.equal(await button.locator('svg').count(), 1, file + ': link icon missing');
        await button.click();
        const copied = await page.evaluate(() => navigator.clipboard.readText());
        // Production pages copy the canonical site URL, not the local test-server URL.
        const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
        assert.equal(copied, canonical, file + ': incorrect clipboard URL');
        await page.close();
      }
      await ctx.close();
    }
    console.log('PASS: copy-link button and clipboard on three articles, desktop and mobile');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
