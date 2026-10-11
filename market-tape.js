/* Native TTN ticker strip. Real prices only; chart data from TradingView on click. */
(()=>{"use strict";
const symbols=[["btc","Bitcoin","BINANCE:BTCUSDT"],["eth","Ethereum","BINANCE:ETHUSDT"],["sp500","S&P 500","FOREXCOM:SPXUSD"],["nasdaq","Nasdaq","FOREXCOM:NSXUSD"],["gold","Gold","TVC:GOLD"],["eurusd","EUR/USD","FX:EURUSD"]];
function init(){
const host=document.getElementById("ticker-strip");if(!host||!window.TTN_CONFIG||!window.TTNTickers)return;
const ids=TTN_CONFIG.TICKERS.map(t=>t.id);
host.innerHTML='<div class="ttn-ticker-label"><span class="ttn-live-dot"></span>MARKETS</div><div class="ttn-ticker-window"><div class="ttn-ticker-track" id="ttn-ticker-track"></div></div><span class="ttn-ticker-attribution">Charts: TradingView</span>';
const track=document.getElementById("ttn-ticker-track");
function draw(){
 const entries=symbols.map(([id,label,chart],i)=>{const idMatch=TTN_CONFIG.TICKERS.find(t=>t.id===id||t.label.toLowerCase()===label.toLowerCase());const s=idMatch?TTNTickers.getState(idMatch.id):null;
 const valid=s&&s.demo!==true&&Number.isFinite(s.price);
 const price=valid?TTNTickers.fmtPrice(s.price):"—";
 const change=valid&&Number.isFinite(s.changePct)?(s.changePct>=0?"+":"")+s.changePct.toFixed(2)+"%":"";
 const direction=valid?(s.changePct>=0?"up":"down"):"unavailable";
 return '<button type="button" class="ttn-ticker-item '+direction+'" data-symbol="'+chart+'" data-label="'+label+'" aria-label="Open '+label+' TradingView chart"><span class="ttn-ticker-name">'+label+'</span><strong class="ttn-ticker-value">'+price+'</strong><span class="ttn-ticker-change">'+change+'</span></button>';
 }).join("");
 track.innerHTML=entries+entries;track.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{if(window.TTNChart)TTNChart.open(b.dataset.symbol,b.dataset.label)}));
}
draw();setInterval(draw,Math.max(10000,TTN_CONFIG.PRICE_REFRESH_MS||60000));
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();