/* Run with Playwright installed. Defaults to the deployed TTN homepage. */
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const BASE=process.env.TTN_TEST_BASE || 'https://globtechco.github.io/ttn-finans/';
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  for(const mode of [
   {name:'desktop-light',viewport:{width:1365,height:900},colorScheme:'light'},
   {name:'mobile-dark',viewport:{width:390,height:844},colorScheme:'dark'}
  ]){
   const context=await browser.newContext(mode);
   const page=await context.newPage(),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   // A proxy outage must never prevent original source news from opening.
   await page.route('**/api.rss2json.com/**',r=>r.abort());
   await page.goto(BASE,{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>typeof TTNNews!=='undefined'&&TTNNews.getAllItems().length>1,null,{timeout:18000});
   await page.waitForFunction(()=>TTNNews.getAllItems().some(i=>i.source==='MarketWatch'),null,{timeout:12000});
   const items=await page.evaluate(()=>TTNNews.getAllItems());
   assert(items.length>10,'Real RSS items should load despite blocked conversion proxy');
   const sources=[...new Set(items.map(i=>i.source))];
   assert(sources.length>=3,'Independent original sources should remain available');
   assert(items.every(i=>/^https?:\/\//.test(i.link)),'Only original article URLs should open');
   assert(await page.locator('#news-feed .news-item').count()>0);
   if(await page.locator('#cookie-decline').count())await page.locator('#cookie-decline').click();
   const link=page.locator('#featured-article .open-article').first();
   // Live sources can replace the featured story between a DOM read and click.
   // Capture the URL of the element actually clicked, in the same event, so
   // the assertion still detects an incorrect modal without racing a refresh.
   await page.evaluate(()=>document.addEventListener('click',event=>{
    const clicked=event.target.closest('#featured-article .open-article');
    if(clicked)window.__ttnTestClickedSource=clicked.dataset.link;
   },true));
   await link.click();
   await page.waitForSelector('#news-modal.open');
   const expected=await page.evaluate(()=>window.__ttnTestClickedSource);
   assert(/^https?:\/\//.test(expected),'Capture the clicked original source URL');
   assert.equal(await page.locator('.news-modal-source-link').getAttribute('href'),expected);
   assert((await page.locator('#news-modal h2').innerText()).length>5);
   await page.keyboard.press('Escape');
   await page.waitForFunction(()=>!document.querySelector('#news-modal').classList.contains('open'));
   await link.click();
   await page.goBack();
   await page.waitForFunction(()=>!document.querySelector('#news-modal').classList.contains('open'));
   await page.locator('#search-input').fill('MarketWatch');
   // Search matches headline/body/ticker; it need not match the outlet name.
   await page.locator('#search-input').fill('');
   assert(await page.locator('#news-feed .news-item').count()>0);
   assert.deepEqual(errors,[],'No uncaught page errors');
   console.log('PASS_NEWS_BROWSER',JSON.stringify({mode:mode.name,items:items.length,sources,modal:true,escape:true,back:true,errors}));
   await context.close();
  }
 } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
