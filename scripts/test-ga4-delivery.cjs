// Browser-level GA4 delivery check. Collection requests are intercepted and NEVER sent to Google.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const base = process.env.TTN_TEST_BASE || 'http://127.0.0.1:8765/';
const mid = 'G-2VM6S0QL1H';
const pages = ['index.html','nonfarm-payrolls-jobs-report-explained.html','pnc-coinbase-usdc-corporate-payments-pilot-november-9-2026.html'];
(async () => {
  const browser = await chromium.launch({headless:true, args:['--no-sandbox']});
  try {
    for (const file of pages) {
      const ctx = await browser.newContext({serviceWorkers:'block'});
      const page = await ctx.newPage();
      const hits = [], tagRequests = [], errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      await page.route(/https:\/\/[^/]*(google-analytics\.com|analytics\.google\.com)\//, async route => {
        const u = new URL(route.request().url());
        if (u.pathname.includes('collect')) hits.push({url:u.href,tid:u.searchParams.get('tid'),en:u.searchParams.get('en'),gcs:u.searchParams.get('gcs')});
        await route.fulfill({status:204,body:''}); // no synthetic traffic in user's property
      });
      page.on('request', req => {if(req.url().includes('googletagmanager.com/gtag/js'))tagRequests.push(req.url());});
      const response = await page.goto(new URL(file,base).href,{waitUntil:'domcontentloaded',timeout:30000});
      assert.equal(response.status(),200,file+': HTTP');
      await page.waitForSelector('#cookie-accept',{timeout:7000});
      assert.equal(await page.evaluate(() => localStorage.getItem('ttn_cookie_consent')),null,file+': unexpectedly consented');
      assert.equal(await page.evaluate(() => Boolean(document.getElementById('ttn-google-analytics'))),false,file+': Google tag loaded before consent');
      await page.click('#cookie-accept');
      await page.waitForFunction(() => localStorage.getItem('ttn_cookie_consent') === 'accepted');
      await page.waitForFunction(() => Boolean(document.getElementById('ttn-google-analytics')),{timeout:10000});
      await page.waitForTimeout(5000);
      const state = await page.evaluate(() => ({disabled:window['ga-disable-G-2VM6S0QL1H'],commands:(window.dataLayer||[]).map(x=>Array.from(x)),scripts:[...document.scripts].filter(s=>s.src.includes('googletagmanager.com')).length,gaCookie:document.cookie.includes('_ga=')}));
      console.log('GA4_BROWSER',JSON.stringify({page:file,hits:hits.map(x=>({tid:x.tid,en:x.en,gcs:x.gcs})),tagRequests,errors,state}));
      assert.equal(state.disabled,false,file+': analytics disabled after consent');
      assert(state.commands.some(x=>x[0]==='config'&&x[1]===mid),file+': missing config');
      assert(hits.some(x=>x.tid===mid&&x.en==='page_view'),file+': missing GA4 page_view HTTP request after Accept');
      await ctx.close();
    }
    console.log('PASS: GA4 collection initiated on all tested pages only after visitor consent');
  } finally {
    await browser.close();
  }
})().catch(err=>{console.error(err);process.exitCode=1;});
