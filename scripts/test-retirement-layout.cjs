/* Regression for intrinsic grid overflow, mobile scenario cards and chart resizing. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const base=process.env.TTN_TEST_BASE || 'http://127.0.0.1:8765/';
const shots=process.env.TTN_SCREENSHOT_DIR || '/tmp/ttn-retirement-layout';
fs.mkdirSync(shots,{recursive:true});
async function bounds(page,label){
 const m=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,boxes:['.topnav','.retirement-layout','#rt-form','[aria-label="Retirement results"]','#rt-chart','.retirement-scenarios'].map(s=>{const e=document.querySelector(s),r=e.getBoundingClientRect();return {selector:s,left:r.left,right:r.right,width:r.width};}),chart:document.querySelector('#rt-chart svg')?.viewBox.baseVal.width}));
 console.log(label,JSON.stringify(m));
 assert(m.document<=m.viewport+1,label+' document overflow');
 for(const b of m.boxes)assert(b.left>=-1 && b.right<=m.viewport+1,label+' overflow '+b.selector);
 const chart=m.boxes.find(b=>b.selector==='#rt-chart');assert(Math.abs(m.chart-chart.width)<=1,label+' chart not fitted');
}
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  // Reproduce the prior page with the old CSS/JS, without changing the live site.
  const old=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  for(const file of ['retirement-calculator.css','retirement-calculator.js']){
   const body=execFileSync('git',['show','222a77deff198829ae65373c70baeb5e940013c5:'+file],{encoding:'utf8'});
   await old.route('**/'+file+'*',r=>r.fulfill({body,contentType:file.endsWith('css')?'text/css':'text/javascript'}));
  }
  const before=await old.newPage();await before.goto(base+'retirement-calculator.html');await before.locator('#rt-results').waitFor({state:'visible'});
  console.log('BASELINE',await before.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,chart:document.querySelector('#rt-chart').getBoundingClientRect().width})));
  await before.screenshot({path:path.join(shots,'retirement-before-390.png'),fullPage:true});await old.close();
  for(const width of [320,360,390,430,600,768,850,851,1080,1440])for(const theme of ['light','dark']){
   const context=await browser.newContext({viewport:{width,height:844},isMobile:width<768,hasTouch:width<768,colorScheme:theme});
   await context.addInitScript(t=>{localStorage.setItem('ttn-theme',t);localStorage.setItem('ttn_cookie_consent','declined');},theme);
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base+'retirement-calculator.html',{waitUntil:'load'});await page.locator('#rt-results').waitFor({state:'visible'});await page.evaluate(()=>document.fonts.ready);
   await bounds(page,width+'-'+theme+' initial');
   assert.equal(await page.locator('#rt-balance').innerText(),'$331,174');
   if(width<=600){assert.equal(await page.locator('.retirement-scenarios tbody tr').first().evaluate(e=>getComputedStyle(e).display),'grid');assert.equal(await page.locator('#rt-age').evaluate(e=>getComputedStyle(e).fontSize),'16px');}
   await page.locator('#rt-monthly').fill('1500');await page.locator('#rt-retire').fill('70');await bounds(page,width+'-'+theme+' changed');
   await page.locator('#rt-retire').fill('30');assert(await page.locator('#rt-error').innerText());assert(await page.locator('#rt-results').isHidden());
   await page.getByRole('button',{name:'Reset example',exact:true}).click();assert.equal(await page.locator('#rt-balance').innerText(),'$331,174');await bounds(page,width+'-'+theme+' reset');
   if(width===390||width===1440)await page.screenshot({path:path.join(shots,'retirement-after-'+width+'-'+theme+'.png'),fullPage:true});
   if(width===390){await page.locator('[aria-label="Retirement results"]').screenshot({path:path.join(shots,'retirement-results-'+theme+'.png')});await page.getByRole('button',{name:'Open navigation',exact:true}).click();await bounds(page,theme+' open navigation');await page.keyboard.press('Escape');}
   // Simulate rotation and a narrow resize without reloading or losing inputs.
   if(width===430){await page.setViewportSize({width:844,height:430});await page.waitForFunction(()=>Math.abs(document.querySelector('#rt-chart svg').viewBox.baseVal.width-document.querySelector('#rt-chart').getBoundingClientRect().width)<1);await bounds(page,theme+' rotated');await page.setViewportSize({width:360,height:780});await page.waitForFunction(()=>Math.abs(document.querySelector('#rt-chart svg').viewBox.baseVal.width-document.querySelector('#rt-chart').getBoundingClientRect().width)<1);await bounds(page,theme+' resized');}
   assert.deepEqual(errors,[],width+'-'+theme+' JS errors');await context.close();
  }
  console.log('PASS: retirement layout 320–1440px, both themes, initial load, edits, reset, navigation and rotation.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
