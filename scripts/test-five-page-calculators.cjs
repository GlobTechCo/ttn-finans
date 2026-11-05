/* Regression checks for the approved five-page methodology update. */
const fs=require("node:fs"),cp=require("node:child_process");
const source=fs.readFileSync("calculators.js","utf8");
const baseline=cp.execFileSync("git",["show","5dded16dcd2cf7d2b39ae96acba02b767ac97880:calculators.js"],{encoding:"utf8"});

function assert(ok,message) { if (!ok) throw new Error(message); }
function near(a,b,message) { assert(Math.abs(a-b) <= Math.max(.000001,Math.abs(b)*1e-10), message+": "+a+" versus "+b); }
function harness(values, extras=[],code=source) {
  const nodes={};
  const make=()=>({value:"",textContent:"",style:{},hidden:true,children:[],events:{},addEventListener(e,f){this.events[e]=f;},replaceChildren(){this.children=[];},appendChild(c){this.children.push(c);}});
  for(const [id,value] of Object.entries(values)) nodes[id]=Object.assign(make(),{value:String(value)});
  for(const id of extras)nodes[id]=make();
  const document={getElementById:id=>nodes[id]||null,createElement:make,addEventListener:(e,fn)=>fn()};
  new Function("document",code)(document);
  return {nodes,set(id,value){nodes[id].value=String(value);nodes[id].events.input();}};
}
const ciResult=["ci-result","ci-sub","ci-breakdown","ci-rows"],pnlResult=["pnl-result","pnl-sub","pnl-breakdown","pnl-gross","pnl-entry-cost","pnl-exit-cost","pnl-net","pnl-roi"];
const dollars=s=>Number(s.replace(/[^0-9.−-]/g,"").replace("−","-"));
const ciCases=[
 [1000,100,12,1],[1000,100,0,10],[1000,0,7,10],[1000,100,7,0],[1000,100,7,1.25],[0,100,7,1/12],[1000,100,-10,2],[1000,100,1000,60]
];
for(const [p,c,rate,years] of ciCases){
 const values={"ci-principal":p,"ci-monthly":c,"ci-rate":rate,"ci-years":years};
 const h=harness(values,ciResult),old=harness(values,["ci-result","ci-sub"],baseline);
 let b=p;for(let m=0;m<Math.round(years*12);m++)b=b*(1+rate/1200)+c;
 const shown=dollars(h.nodes["ci-result"].textContent);
 assert(h.nodes["ci-result"].textContent===old.nodes["ci-result"].textContent,"CI baseline balance");
 assert(h.nodes["ci-sub"].textContent===old.nodes["ci-sub"].textContent,"CI baseline contributions");
 assert(Math.abs(shown-b)<=Math.max(.011,Math.abs(b)*1e-10),"CI independent monthly recurrence");
 const rows=h.nodes["ci-rows"].children;
 assert(rows.length===Math.max(1,Math.ceil(years)),"CI yearly rows");
 near(dollars(rows.at(-1).children[4].textContent),shown,"CI last row matches final result");
 if(years===1.25) assert(rows.at(-1).children[0].textContent==="Year 2 (3 months)","partial year label");
}
let h=harness({"ci-principal":1000,"ci-monthly":100,"ci-rate":7,"ci-years":1},ciResult);
h.set("ci-principal","");assert(h.nodes["ci-breakdown"].hidden && !h.nodes["ci-rows"].children.length,"CI invalid clears stale table");
for(const val of [-1,61,0.1]) {h.set("ci-principal",1000);h.set("ci-years",val);assert(h.nodes["ci-result"].textContent==="—","invalid horizon");}
for(const exit of [65000,55000,60000,0]){
 for(const lev of [1,2,125]){
  const values={"pnl-entry":60000,"pnl-current":exit,"pnl-amount":1000,"pnl-leverage":lev};
  const h=harness({...values,"pnl-entry-fee":0,"pnl-exit-fee":0},pnlResult),old=harness(values,["pnl-result","pnl-sub"],baseline);
  assert(h.nodes["pnl-result"].textContent===old.nodes["pnl-result"].textContent,"zero fees preserve gross result");
  const quantity=1000*lev/60000,gross=quantity*(exit-60000),entryFee=quantity*60000*.001,exitFee=quantity*exit*.002;
  h.set("pnl-entry-fee",.1);h.set("pnl-exit-fee",.2);
  assert(Math.abs(dollars(h.nodes["pnl-result"].textContent)-(gross-entryFee-exitFee))<.011,"net trade arithmetic");
  assert(Math.abs(dollars(h.nodes["pnl-entry-cost"].textContent)-entryFee)<.011,"entry fee base");
  assert(Math.abs(dollars(h.nodes["pnl-exit-cost"].textContent)-exitFee)<.011,"exit fee base");
 }
}
h=harness({"pnl-entry":60000,"pnl-current":65000,"pnl-amount":1000,"pnl-leverage":2,"pnl-entry-fee":.1,"pnl-exit-fee":.1},pnlResult);
assert(h.nodes["pnl-result"].textContent==="+$162.50" && h.nodes["pnl-roi"].textContent==="+16.25%","worked PNL");
h.set("pnl-current",60000);assert(h.nodes["pnl-result"].textContent==="−$4.00","flat price fee loss");
h.set("pnl-amount",0);assert(h.nodes["pnl-roi"].textContent.includes("Not defined"),"zero-margin return undefined");
h.set("pnl-entry-fee","");assert(h.nodes["pnl-result"].textContent==="—" && h.nodes["pnl-breakdown"].hidden,"invalid fee clears breakdown");
h.set("pnl-entry-fee",101);assert(h.nodes["pnl-result"].textContent==="—","fee bounds");
for(const fee of [-1,Infinity]){h.set("pnl-entry-fee",fee);assert(h.nodes["pnl-result"].textContent==="—","invalid fee");}
const directory=harness({"ci-principal":1000,"ci-monthly":100,"ci-rate":7,"ci-years":10,"pnl-entry":60000,"pnl-current":65000,"pnl-amount":1000,"pnl-leverage":1,"loan-amount":10000,"loan-rate":5,"loan-term":60},["ci-result","ci-sub","pnl-result","pnl-sub","loan-result","loan-sub"]);
assert(directory.nodes["loan-result"].textContent==="$188.71","shared loan regression");
assert(directory.nodes["pnl-result"].textContent==="+$83.33","directory legacy optional fields");
near(182935-115948,66987,"reported FCF");
near((10000+2000)*.004+1000*2/60*30,1048,"AI system A");
near((10000+1000)*.008+200*2/60*30,288,"AI system B");
console.log("PASS: calculator boundaries, independent arithmetic, yearly tables, zero-fee regression, directory and loan compatibility.");
