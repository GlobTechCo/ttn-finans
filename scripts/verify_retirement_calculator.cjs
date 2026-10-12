const assert = require('node:assert/strict');
const {project} = require('../retirement-calculator.js');
const base = {age:35,retire:65,end:95,savings:50000,monthly:500,spending:4000,income:1800,before:6,after:4,inflation:2.5,fee:0.5};
const close = (a,b) => assert.ok(Math.abs(a-b)<Math.max(1e-5,Math.abs(b)*1e-8), `${a} != ${b}`);
const zero = {...base,before:0,after:0,inflation:0,fee:0};
let r=project(zero); close(r.balance,230000);close(r.target,792000);close(r.required,(792000-50000)/360);
// Solving for the contribution must produce the target independently through monthly cash flows.
for(const x of [base,{...base,inflation:6,before:-4,after:-2},{...base,before:3,after:3,inflation:3,fee:0}]){
 r=project(x);let balance=x.savings;const rate=Math.pow(1+(x.before-x.fee)/100,1/12)-1;
 for(let i=0;i<(x.retire-x.age)*12;i++)balance=balance*(1+rate)+r.required;
 close(balance/Math.pow(1+x.inflation/100,x.retire-x.age),r.target);
 // Starting from the target, beginning-of-month withdrawals exhaust it at the horizon.
 let remaining=r.target;const real=Math.pow((1+(x.after-x.fee)/100)/(1+x.inflation/100),1/12)-1;
 for(let i=0;i<(x.end-x.retire)*12;i++)remaining=(remaining-Math.max(0,x.spending-x.income))*(1+real);
 close(remaining,0);
}
assert.equal(project({...base,income:5000}).target,0);
assert.equal(project({...base,retire:35}).required,null);
assert.ok(project(base,-2).required>project(base,2).required);
assert.ok(project({...base,fee:1}).balance<project({...base,fee:0}).balance);
assert.ok(project({...base,end:100}).target>project(base).target);
assert.throws(()=>project({...base,retire:34}));assert.throws(()=>project({...base,monthly:NaN}));
const fs=require('node:fs');const html=fs.readFileSync('retirement-calculator.html','utf8');
assert.match(html,/<h1>Retirement Planning Calculator<\/h1>/);assert.match(html,/rel="canonical" href="https:\/\/globtechco.github.io\/ttn-finans\/retirement-calculator.html"/);
const schema=JSON.parse(html.match(/<script type="application\/ld\+json">(.*?)<\/script>/s)[1]);assert.equal(schema['@graph'][1]['@type'],'WebApplication');
assert.match(fs.readFileSync('sitemap.xml','utf8'),/retirement-calculator.html/);
for(const name of ['calculators','index','compound-interest-calculator','dollar-cost-averaging-vs-lump-sum','tips-inflation-protected-bonds-explained','bond-duration-explained','etf-creation-redemption-mechanism','money-market-funds-vs-savings-explained'])assert.match(fs.readFileSync(name+'.html','utf8'),/href="retirement-calculator.html"/);
console.log('PASS: zero-return reference, independent cash-flow checks, inflation, negative returns, fees, retirement-now, income coverage, input errors, metadata and internal links.');
