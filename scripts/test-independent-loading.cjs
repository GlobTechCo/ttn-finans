// Regression checks for stalled third-party services. Run with Node.js.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const tick = () => new Promise(resolve => setTimeout(resolve, 5));
function setup(fetch) {
  class Element extends EventTarget {
    constructor() { super(); this.innerHTML = ''; this.value = ''; }
    get textContent() { return this.innerHTML.replace(/<[^>]*>/g, ''); }
    set textContent(v) { this.innerHTML = v; }
    querySelectorAll() { return []; }
    querySelector() { return null; }
  }
  const elements = new Map();
  const document = new EventTarget();
  document.readyState = 'complete';
  document.getElementById = id => {
    if (!elements.has(id)) elements.set(id, new Element());
    return elements.get(id);
  };
  document.createElement = () => new Element();
  const context = vm.createContext({document, Event, AbortController, console, fetch,
    setTimeout: (fn, ms) => { assert.equal(ms,8000); return setTimeout(fn,40); },
    clearTimeout, setInterval: () => 0,
    TTN_CONFIG: {NEWS_FEEDS:[{name:'Fast',url:'fast'},{name:'Slow',url:'slow'}],
      TICKER_DICTIONARY:[],TICKERS:[], PEXELS_KEY:'test', CATEGORY_PHOTO_QUERIES:{general:'finance'}}});
  const load = file => vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),context);
  return {context,load,document,elements};
}
function stalled(signal, body=false) {
  const pending = new Promise((resolve,reject) => signal.addEventListener('abort', () => reject(new Error('aborted')), {once:true}));
  return body ? Promise.resolve({ok:true,json:()=>pending}) : pending;
}
(async () => {
  // A good source must render before the stalled source, quote service and
  // optional photo response finish, including a response with a stalled body.
  const s = setup((url,options) => {
    if (url.includes('rss_url=fast')) return Promise.resolve({ok:true,json:async()=>({status:'ok',items:[
      {title:'Fast financial headline',description:'Source excerpt',link:'https://example.com/news',thumbnail:'https://example.com/photo.jpg',pubDate:new Date().toISOString()}
    ]})});
    return stalled(options.signal,true);
  });
  s.context.TTNTickers = {getChangePct:()=>null};
  s.load('news.js');
  let finished=false;
  const news=vm.runInContext('TTNNews.init()',s.context).then(()=>finished=true);
  await tick();
  assert.match(s.document.getElementById('featured-article').innerHTML,/Fast financial headline/);
  assert.match(s.document.getElementById('featured-article').innerHTML,/<h2>/);
  assert.doesNotMatch(s.document.getElementById('featured-article').innerHTML,/<h1>/);
  assert.equal(finished,false,'slow feed must still be pending when first headline renders');
  assert.match(s.document.getElementById('featured-article').innerHTML,/loading="eager"/);
  await news;
  assert.match(s.document.getElementById('featured-article').innerHTML,/Fast financial headline/);
  // A pending price init must never prevent news init or initial summary.
  const calls=[];const a=setup(()=>{});
  a.context.TTNTickers={init:()=>{calls.push('prices');return new Promise(()=>{});}};
  a.context.TTNNews={init:()=>{calls.push('news');return Promise.resolve();}};
  a.context.TTNMarketSummary={render:()=>calls.push('summary')};a.load('app.js');
  assert.deepEqual(calls,['summary','prices','news']);
  // Failed quote APIs must not manufacture prices or changes.
  const q=setup((url,options)=>stalled(options.signal));
  q.context.TTN_CONFIG.TICKERS=[{id:'btc',type:'crypto',coingeckoId:'bitcoin'},{id:'spx',twelveDataSymbol:'SPX'}];
  q.load('tickers.js');await vm.runInContext('TTNTickers.init()',q.context);
  assert.equal(vm.runInContext('TTNTickers.getState("btc").price',q.context),null);
  assert.equal(vm.runInContext('TTNTickers.getChangePct("spx")',q.context),null);
  console.log('PASS: progressive news, stalled headers/body, independent startup, honest missing quotes');
})().catch(e=>{console.error(e);process.exitCode=1;});
