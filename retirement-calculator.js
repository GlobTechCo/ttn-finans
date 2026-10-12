/* Deterministic retirement scenarios, in today's dollars; no personal data requests. */
(function (root) {
  'use strict';
  const annuity = (r, n) => Math.abs(r) < 1e-12 ? n : Math.expm1(n * Math.log1p(r)) / r;
  function project(x, offset = 0) {
    const values = Object.values(x);
    if (!values.every(Number.isFinite) || ![x.age,x.retire,x.end].every(Number.isInteger) || x.age < 18 || x.age > 85 || x.retire < x.age || x.retire > 90 || x.end <= x.retire || x.end > 110 || x.savings < 0 || x.monthly < 0 || x.spending < 0 || x.income < 0 || x.inflation < 0 || x.inflation > 15 || x.before < -10 || x.before > 15 || x.after < -10 || x.after > 15 || x.fee < 0 || x.fee > 5 || Math.max(x.savings,x.monthly,x.spending,x.income) > 1e9) throw new Error('Check the inputs: ages must be whole years (18–85 now, up to 90 at retirement, up to 110 at the end). Retirement must be at or after your current age and end later. Amounts must be $0–$1 billion, returns −10% to 15%, inflation 0–15%, and fees 0–5%.');
    const months = (x.retire - x.age) * 12, duration = (x.end - x.retire) * 12;
    const netBefore = (x.before + offset - x.fee) / 100, netAfter = (x.after + offset - x.fee) / 100;
    const monthlyReturn = Math.expm1(Math.log1p(netBefore) / 12);
    const realRate = Math.expm1((Math.log1p(netAfter) - Math.log1p(x.inflation / 100)) / 12);
    const inflationFactor = Math.pow(1 + x.inflation / 100, months / 12);
    const growth = Math.pow(1 + monthlyReturn, months), contributionFactor = annuity(monthlyReturn, months);
    const nominal = x.savings * growth + x.monthly * contributionFactor;
    const balance = nominal / inflationFactor;
    const withdrawal = Math.max(0, x.spending - x.income);
    // Beginning-of-month withdrawals: PV of an annuity due, with zero terminal balance.
    const target = withdrawal * annuity(realRate, duration) / Math.pow(1 + realRate, duration - 1);
    const required = months ? Math.max(0, (target * inflationFactor - x.savings * growth) / contributionFactor) : null;
    if (![balance,target,nominal].every(Number.isFinite)) throw new Error('These assumptions exceed the calculation range.');
    const points = [{age:x.age,balance:x.savings}];
    for (let year = 1; year <= x.retire - x.age; year++) {
      const m = year * 12;
      points.push({age:x.age+year,balance:(x.savings*Math.pow(1+monthlyReturn,m)+x.monthly*annuity(monthlyReturn,m))/Math.pow(1+x.inflation/100,year)});
    }
    let remaining = balance, depletedAge = null;
    for (let m = 0; m < duration; m++) {
      if (remaining + 1e-7 < withdrawal && depletedAge === null) depletedAge = x.retire + m / 12;
      remaining = Math.max(0, remaining - withdrawal) * (1 + realRate);
      if ((m + 1) % 12 === 0) points.push({age:x.retire+(m+1)/12,balance:remaining});
    }
    return {balance,nominal,target,required,gap:balance-target,points,depletedAge,netBefore,netAfter};
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {project};
  if (!root.document) return;
  document.addEventListener('DOMContentLoaded', () => {
    const ids = ['age','retire','end','savings','monthly','spending','income','inflation','before','after','fee'];
    const el = id => document.getElementById(id);
    const money = n => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(n);
    function update() {
      const x = Object.fromEntries(ids.map(id => [id, el('rt-'+id).value.trim() === '' ? NaN : Number(el('rt-'+id).value)]));
      try {
        const scenarios = [-2,0,2].map(offset => project(x,offset));
        const b = scenarios[1]; el('rt-error').textContent = ''; el('rt-results').hidden = false;
        el('rt-balance').textContent = money(b.balance); el('rt-target').textContent = money(b.target);
        el('rt-required').textContent = b.required === null ? 'Already at retirement' : money(b.required) + ' / month';
        el('rt-status').textContent = (b.gap >= 0 ? 'Modeled surplus: ' : 'Modeled shortfall: ') + money(Math.abs(b.gap)) + '. ' + (b.depletedAge === null ? 'The base scenario funds the selected spending through age '+x.end+'.' : 'The base scenario first cannot cover a full withdrawal at age '+b.depletedAge.toFixed(1)+'.');
        el('rt-nominal').textContent = 'Base balance in retirement-year dollars: '+money(b.nominal)+'. All headline results and chart values use today’s purchasing power.';
        el('rt-scenarios').innerHTML = scenarios.map((s,i)=>'<tr><th scope="row">'+['Lower return','Base','Higher return'][i]+'</th><td>'+ (s.netBefore*100).toFixed(1)+'% / '+(s.netAfter*100).toFixed(1)+'%</td><td>'+money(s.balance)+'</td><td>'+money(s.target)+'</td><td>'+(s.required === null ? '—' : money(s.required))+'</td></tr>').join('');
        const max = Math.max(1,...b.points.map(p=>p.balance),b.target), width = 800, height = 230;
        const px = age => 55 + (age-x.age)/(x.end-x.age)*720, py = v => 190 - v/max*160;
        const path = b.points.map((p,i)=>(i?'L':'M')+px(p.age).toFixed(2)+','+py(p.balance).toFixed(2)).join(' ');
        el('rt-chart').innerHTML = '<svg viewBox="0 0 '+width+' '+height+'" role="img" aria-labelledby="rt-chart-title rt-chart-desc"><title id="rt-chart-title">Base retirement balance in today’s dollars</title><desc id="rt-chart-desc">'+el('rt-status').textContent+' Balance at retirement: '+money(b.balance)+'.</desc><line x1="55" y1="190" x2="775" y2="190" stroke="currentColor" opacity=".3"/><line x1="'+px(x.retire)+'" y1="30" x2="'+px(x.retire)+'" y2="190" stroke="currentColor" stroke-dasharray="5 5" opacity=".5"/><path d="'+path+'" fill="none" stroke="var(--accent)" stroke-width="3"/><text x="55" y="20" fill="currentColor" font-size="13">'+money(max)+'</text><text x="55" y="215" fill="currentColor" font-size="13">Age '+x.age+'</text><text x="'+px(x.retire)+'" y="215" text-anchor="middle" fill="currentColor" font-size="13">Retire '+x.retire+'</text><text x="775" y="215" text-anchor="end" fill="currentColor" font-size="13">Age '+x.end+'</text></svg>';
        el('rt-yearly').innerHTML = b.points.map(p=>'<tr><th scope="row">'+p.age+'</th><td>'+money(p.balance)+'</td></tr>').join('');
      } catch (e) {el('rt-error').textContent=e.message;el('rt-results').hidden=true;}
    }
    ids.forEach(id=>el('rt-'+id).addEventListener('input',update));
    el('rt-reset').addEventListener('click',()=>{el('rt-form').reset();update();});
    el('rt-print').addEventListener('click',()=>window.print());
    el('rt-form').addEventListener('submit',e=>e.preventDefault()); update();
  });
})(typeof window === 'undefined' ? {} : window);
