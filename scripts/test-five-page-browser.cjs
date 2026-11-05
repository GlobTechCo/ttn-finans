const {chromium}=require("playwright");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const base=process.env.TTN_TEST_BASE||"http://127.0.0.1:8765/";
const pages=["free-cash-flow-explained.html","ai-inference-unit-economics-2026.html","stablecoins-explained-depeg-risk.html","compound-interest-calculator.html","crypto-profit-loss-calculator.html"];
(async()=>{
 const browser=await chromium.launch();
 for(const width of [360,390,768,1440]) for(const theme of ["light","dark"]){
  const context=await browser.newContext({viewport:{width,height:900}});
  await context.addInitScript(t=>localStorage.setItem("ttn-theme",t),theme);
  await context.route("**/*",route=>route.request().url().startsWith(base)?route.continue():route.abort());
  const page=await context.newPage();
  const errors=[];page.on("pageerror",e=>errors.push(e.message));
  for(const path of pages){
   const response=await page.goto(base+path,{waitUntil:"networkidle"});
   assert.equal(response.status(),200);
   assert.equal(await page.locator("h1").count(),1);
   assert.equal(await page.getAttribute("html","data-theme"),theme);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),path+" overflow at "+width);
   for(const region of await page.locator(".ttn-table-scroll").all()){
    await region.focus();assert(await region.evaluate(el=>document.activeElement===el),"table keyboard focus");
    if(width<600){await page.keyboard.press("End");assert(await region.evaluate(el=>el.scrollWidth>el.clientWidth),"mobile table scroll");}
   }
   if(path==="compound-interest-calculator.html"){
    await page.locator("#ci-rate").fill("12");await page.locator("#ci-years").fill("1");
    assert.equal(await page.textContent("#ci-result"),"$2,395.08");
    assert.equal(await page.locator("#ci-rows tr").count(),1);
    assert.equal(await page.locator("#ci-rows tr td").last().textContent(),"$2,395.08");
    await page.locator("#ci-years").fill("1.25");
    assert.equal(await page.locator("#ci-rows tr").last().locator("th").textContent(),"Year 2 (3 months)");
    await page.locator("#ci-principal").fill("");
    assert(await page.locator("#ci-breakdown").isHidden(),"invalid table hidden");
   }
   if(path==="crypto-profit-loss-calculator.html"){
    await page.locator("#pnl-leverage").fill("2");
    await page.locator("#pnl-entry-fee").fill("0.1");await page.locator("#pnl-exit-fee").fill("0.1");
    assert.equal(await page.textContent("#pnl-result"),"+$162.50");
    assert.equal(await page.textContent("#pnl-roi"),"+16.25%");
    await page.locator("#pnl-current").fill("60000");assert.equal(await page.textContent("#pnl-result"),"−$4.00");
    await page.locator("#pnl-entry-fee").fill("");assert(await page.locator("#pnl-breakdown").isHidden());
   }
   if(width===390){
    const dir=process.env.TTN_SCREENSHOT_DIR||"/tmp/ttn-five-page";
    fs.mkdirSync(dir,{recursive:true});
    await page.screenshot({path:dir+"/"+path.replace(".html","")+"-"+theme+".png",fullPage:true});
   }
  }
  await page.goto(base+"calculators.html",{waitUntil:"networkidle"});
  assert.notEqual(await page.textContent("#ci-result"),"—");
  assert.notEqual(await page.textContent("#pnl-result"),"—");
  assert.notEqual(await page.textContent("#loan-result"),"—");
  assert.deepEqual(errors,[],"runtime errors");
  await context.close();
 }
 const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
 const page=await nojs.newPage();
 for(const path of pages){
  await page.goto(base+path,{waitUntil:"domcontentloaded"});
  assert((await page.locator("main").textContent()).length>1500,"readable method without JS");
  assert(await page.locator("h1").isVisible());
 }
 await nojs.close();await browser.close();
 console.log("PASS: five pages at 360, 390, 768 and 1440 pixels, light/dark themes, keyboard tables, calculator events, directory and no-JavaScript content.");
})().catch(e=>{console.error(e);process.exit(1);});
