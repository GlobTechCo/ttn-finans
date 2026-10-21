/* Browser checks for canonical sections, responsive navigation and crypto charts. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname,'..');
const source = fs.readFileSync(path.join(root,'articles.js'),'utf8');
const articles = JSON.parse(source.slice(source.indexOf('=')+1).trim().replace(/;$/,''));
const base = process.env.TTN_TEST_BASE || 'http://127.0.0.1:8765/';
const shots = process.env.TTN_SCREENSHOT_DIR || '/tmp/ttn-crypto-browser';
fs.mkdirSync(shots,{recursive:true});
const sorted = section => articles.filter(a=>a.section===section).sort((a,b)=>new Date(b.date)-new Date(a.date));
const expected = a=>a.map(x=>x.id+'.html');
const links = (page,selector)=>page.locator(selector+' .editorial-archive-card h3 a').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
async function noOverflow(page,label) {
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),label+' horizontal overflow');
}
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  for (const mobile of [false,true]) for (const theme of ['light','dark']) {
   const name=(mobile?'mobile':'desktop')+'-'+theme;
   const context=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1440,height:1000},isMobile:mobile,hasTouch:mobile,colorScheme:theme});
   await context.addInitScript(t=>{localStorage.setItem('ttn-theme',t);localStorage.setItem('ttn_cookie_consent','declined');},theme);
   const page=await context.newPage(); const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base,{waitUntil:'domcontentloaded'});
   await page.locator('#crypto-home .editorial-archive-card').first().waitFor();
   assert.deepEqual(await links(page,'#crypto-home'),expected(sorted('Crypto').filter(a=>a.format==='news').slice(0,4)));
   assert.deepEqual(await links(page,'#ttn-articles'),expected(sorted('Market Analysis').slice(0,4)));
   assert.deepEqual(await links(page,'#tech-ai-home'),expected(sorted('Tech & AI').slice(0,4)));
   const tape=await page.locator('tv-ticker-tape').getAttribute('symbols');
   assert(tape.includes('COINBASE:SOLUSD') && tape.includes('BITSTAMP:XRPUSD'));
   await noOverflow(page,name+' home');
   if (mobile) await page.getByRole('button',{name:'Open navigation',exact:true}).click();
   await page.locator('#nav-links').getByRole('link',{name:'Crypto',exact:true}).click();
   await page.locator('#crypto-archive .editorial-archive-card').first().waitFor();
   assert.deepEqual(await links(page,'#crypto-archive'),expected(sorted('Crypto').filter(a=>a.format==='news').slice(0,12)));
   assert.deepEqual(await links(page,'#crypto-explainers'),expected(sorted('Crypto').filter(a=>a.format==='explainer').slice(0,4)));
   assert.equal(await page.locator('#nav-links a[aria-current="page"]').innerText(),'Crypto');
   const all=await page.locator('.editorial-topics a').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
   assert.deepEqual([...new Set(all)].sort(),expected(sorted('Crypto')).sort());
   assert.equal(await page.locator('.crypto-chart-links a').count(),4);
   assert.match(await page.locator('tv-ticker-tape').getAttribute('symbols'),/COINBASE:SOLUSD,BITSTAMP:XRPUSD/);
   await noOverflow(page,name+' crypto');
   await page.waitForFunction(()=>{const w=document.querySelector('tv-ticker-tape');return w?.shadowRoot && /[0-9]+[.,][0-9]+/.test(w.shadowRoot.textContent);}, null, {timeout:10000}).catch(()=>{});
   console.log('QUOTE',name,await page.locator('tv-ticker-tape').evaluate(w=>({defined:!!customElements.get('tv-ticker-tape'),text:w.shadowRoot?.textContent?.slice(-1600),html:w.shadowRoot?.innerHTML?.slice(-1500)})));
   await page.screenshot({path:path.join(shots,name+'-crypto.png'),fullPage:true});
   await page.locator('.crypto-chart-links a').first().click();
   await page.getByRole('button',{name:'Close chart',exact:true}).waitFor();
   assert.match(await page.locator('#chart-panel-title').innerText(),/Bitcoin.*BITSTAMP:BTCUSD/);
   await page.keyboard.press('Escape');
   assert(await page.locator('#chart-panel').isHidden());
   assert(await page.locator('.crypto-chart-links a').first().evaluate(e=>e===document.activeElement));
   await page.locator('.crypto-chart-links a').nth(2).click();
   assert.match(await page.locator('#chart-panel-title').innerText(),/Solana.*COINBASE:SOLUSD/);
   await page.getByRole('button',{name:'Close chart',exact:true}).click();
   await page.locator('.crypto-chart-links a').nth(3).click();
   assert.match(await page.locator('#chart-panel-title').innerText(),/XRP.*BITSTAMP:XRPUSD/);
   await page.getByRole('button',{name:'Close chart',exact:true}).click();
   await page.goto(base+'analysis.html?page=2',{waitUntil:'domcontentloaded'});
   await page.getByRole('status').waitFor();
   assert.deepEqual(await links(page,'#analysis-archive'),expected(sorted('Market Analysis').slice(12,24)));
   await page.goto(base+'tech-ai.html',{waitUntil:'domcontentloaded'});
   await page.getByRole('status').waitFor();
   assert.deepEqual(await links(page,'#tech-ai-archive'),expected(sorted('Tech & AI').slice(0,12)));
   assert.deepEqual(errors,[],name+' JavaScript errors');
   console.log('PASS:',name,'home, exclusive archives, news/explainers, charts, Escape and focus');
   await context.close();
  }
  // Narrow desktop header must keep the new link and search inside the viewport.
  const header=await browser.newPage({viewport:{width:1210,height:900}});
  await header.goto(base,{waitUntil:'domcontentloaded'});await noOverflow(header,'1210px header');await header.screenshot({path:path.join(shots,'narrow-desktop-home.png')});await header.close();
  const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});const p=await nojs.newPage();
  await p.goto(base+'crypto.html');
  assert.equal(await p.locator('.editorial-topics a').count(),sorted('Crypto').length);
  assert.equal(await p.locator('#crypto-archive .editorial-archive-card').count(),Math.min(12,sorted('Crypto').filter(a=>a.format==='news').length));
  assert(await p.locator('#nav-links').getByRole('link',{name:'Crypto',exact:true}).isVisible());
  assert(await p.locator('.crypto-market noscript p').isVisible());
  await noOverflow(p,'no-JavaScript mobile');await nojs.close();
  // Block widgets: article reading and external chart fallbacks remain available.
  const blocked=await browser.newContext();await blocked.route(/tradingview/,route=>route.abort());const b=await blocked.newPage();await b.goto(base+'crypto.html');
  assert.equal(await b.locator('#crypto-archive .editorial-archive-card').count(),6);
  await b.locator('.crypto-chart-links a').first().click();
  await b.getByText('TradingView could not be loaded.',{exact:false}).waitFor();
  assert(await b.locator('#crypto-archive').isVisible());await blocked.close();
  console.log('PASS: narrow header, no-JavaScript static discovery and blocked-provider fallback');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
