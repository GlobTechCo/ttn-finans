/* Shared calculators: standalone tools and the calculator directory. */
document.addEventListener("DOMContentLoaded", () => {
  const el = (id) => document.getElementById(id);
  const number = (id) => { const v = el(id).value.trim(); return v === "" ? NaN : Number(v); };
  const fmt = (v, digits = 2) => v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  function result(prefix, value, detail, color = "") {
    el(prefix + "-result").textContent = value;
    el(prefix + "-result").style.color = color;
    el(prefix + "-sub").textContent = detail;
  }
  function invalid(prefix, detail) { result(prefix, "—", detail); }
  function bind(ids, fn, event = "input") { ids.forEach((id) => el(id).addEventListener(event, fn)); }
  const money = (v) => "$" + fmt(v);

  if (el("ci-principal")) {
    function clearBreakdown() {
      if (el("ci-breakdown")) { el("ci-breakdown").hidden = true; el("ci-rows").replaceChildren(); }
    }
    function calc() {
      clearBreakdown();
      const p = number("ci-principal"), c = number("ci-monthly"), rate = number("ci-rate"), years = number("ci-years"), months = Math.round(years * 12);
      if (![p,c,rate,years].every(Number.isFinite) || p < 0 || c < 0 || rate <= -100 || rate > 1000 || years < 0 || years > 60 || Math.abs(years * 12 - months) > 0.00001) return invalid("ci", "Enter nonnegative amounts, a rate above −100%, and a horizon of 0–60 years in whole months.");
      const r = rate / 1200;
      const balanceAt = n => r === 0 ? p + c * n : p * Math.pow(1 + r, n) + c * Math.expm1(n * Math.log1p(r)) / r;
      const balance = balanceAt(months), contributed = p + c * months;
      if (![balance,contributed,balance-contributed].every(Number.isFinite)) return invalid("ci", "These values exceed the calculation range.");
      result("ci", money(balance), `Contributed: ${money(contributed)} · Growth: ${money(balance - contributed)}`);
      if (el("ci-rows")) {
        const periods = [];
        if (months === 0) periods.push(["Start (0 months)", p, 0, 0, p]);
        for (let start = 0; start < months; start += 12) {
          const end = Math.min(start + 12, months), opening = balanceAt(start), closing = balanceAt(end), deposits = c * (end - start);
          const label = end - start === 12 ? `Year ${start / 12 + 1}` : `Year ${start / 12 + 1} (${end - start} months)`;
          periods.push([label, opening, deposits, closing - opening - deposits, closing]);
        }
        for (const values of periods) {
          const tr = document.createElement("tr");
          values.forEach((v,i) => { const cell = document.createElement(i === 0 ? "th" : "td"); if (i === 0) cell.scope = "row"; cell.textContent = i === 0 ? v : money(v); tr.appendChild(cell); });
          el("ci-rows").appendChild(tr);
        }
        el("ci-breakdown").hidden = false;
      }
    }
    bind(["ci-principal","ci-monthly","ci-rate","ci-years"], calc); calc();
  }
  if (el("loan-amount")) {
    function calc() {
      const p = number("loan-amount"), rate = number("loan-rate"), n = number("loan-term");
      if (![p,rate,n].every(Number.isFinite) || p < 0 || rate < 0 || rate > 1000 || !Number.isInteger(n) || n < 1 || n > 1200) return invalid("loan", "Enter a nonnegative loan amount and rate, and a whole-number term of 1–1,200 months.");
      const r = rate / 1200;
      const payment = r === 0 ? p / n : p * r / -Math.expm1(-n * Math.log1p(r));
      if (!Number.isFinite(payment)) return invalid("loan", "These values exceed the calculation range.");
      result("loan", money(payment), `Total: ${money(payment * n)} · Interest: ${money(payment * n - p)}`);
    }
    bind(["loan-amount","loan-rate","loan-term"], calc); calc();
  }
  if (el("pnl-entry")) {
    const feeIds = ["pnl-entry-fee","pnl-exit-fee"].filter(id => el(id));
    function calc() {
      if (el("pnl-breakdown")) el("pnl-breakdown").hidden = true;
      const entry = number("pnl-entry"), current = number("pnl-current"), amount = number("pnl-amount"), leverage = number("pnl-leverage");
      const entryRate = el("pnl-entry-fee") ? number("pnl-entry-fee") : 0, exitRate = el("pnl-exit-fee") ? number("pnl-exit-fee") : 0;
      if (![entry,current,amount,leverage,entryRate,exitRate].every(Number.isFinite) || entry <= 0 || current < 0 || amount < 0 || leverage < 1 || leverage > 125 || entryRate < 0 || entryRate > 100 || exitRate < 0 || exitRate > 100) return invalid("pnl", "Entry price must be above zero; amounts must be nonnegative, leverage 1–125x, and each fee 0–100%.");
      const notional = amount * leverage, exitNotional = notional * (current / entry);
      const grossPct = (current - entry) / entry * leverage, gross = amount * grossPct;
      const entryFee = notional * (entryRate / 100), exitFee = exitNotional * (exitRate / 100), net = gross - entryFee - exitFee;
      const pct = amount > 0 ? net / amount * 100 : null;
      if (![notional,exitNotional,gross,entryFee,exitFee,net].every(Number.isFinite) || (pct !== null && !Number.isFinite(pct))) return invalid("pnl", "These values exceed the calculation range.");
      const signedMoney = v => (v < 0 ? "−" : "+") + money(Math.abs(v));
      const roi = pct === null ? "Not defined (zero margin)" : (pct >= 0 ? "+" : "") + fmt(pct) + "%";
      result("pnl", signedMoney(net), roi + ` · Leverage ${leverage}x` + (amount > 0 && net <= -amount ? " · Theoretical loss; liquidation rules are not modeled." : ""), net >= 0 ? "var(--up)" : "var(--down)");
      if (el("pnl-breakdown")) {
        el("pnl-gross").textContent = signedMoney(gross);
        el("pnl-entry-cost").textContent = money(entryFee);
        el("pnl-exit-cost").textContent = money(exitFee);
        el("pnl-net").textContent = signedMoney(net);
        el("pnl-roi").textContent = roi;
        el("pnl-breakdown").hidden = false;
      }
    }
    bind(["pnl-entry","pnl-current","pnl-amount","pnl-leverage",...feeIds], calc); calc();
  }
  async function json(url) {
    const response = await fetch(url, { signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error("Data request failed");
    return response.json();
  }
  if (el("fx-amount")) {
    const cache = new Map(); let version = 0;
    async function calc() {
      const request = ++version, amount = number("fx-amount"), from = el("fx-from").value, to = el("fx-to").value;
      if (!Number.isFinite(amount) || amount < 0) return invalid("fx", "Enter an amount of zero or more.");
      if (from === to) return result("fx", `${fmt(amount)} ${to}`, "Rate 1:1 (same currency)");
      const key = from + "_" + to;
      let quote = cache.get(key);
      result("fx", "—", "Loading daily reference rate…");
      try {
        if (!quote || Date.now() - quote.fetched > 300000) {
          const data = await json(`https://api.frankfurter.dev/v2/rate/${from.toLowerCase()}/${to.toLowerCase()}`);
          if (!Number.isFinite(data.rate) || data.rate <= 0) throw new Error("Invalid rate");
          quote = { rate: data.rate, date: data.date, fetched: Date.now() }; cache.set(key, quote);
        }
        if (request !== version) return;
        const converted = amount * quote.rate;
        if (!Number.isFinite(converted)) return invalid("fx", "This amount exceeds the calculation range.");
        result("fx", `${fmt(converted)} ${to}`, `1 ${from} = ${fmt(quote.rate, 4)} ${to} · Reference date: ${quote.date}`);
      } catch (error) { if (request === version) invalid("fx", "Could not load the rate. Use Retry rate to try again."); }
    }
    bind(["fx-amount"], calc); bind(["fx-from","fx-to"], calc, "change");
    el("fx-swap").addEventListener("click", () => { const a = el("fx-from"), b = el("fx-to"); [a.value,b.value] = [b.value,a.value]; calc(); });
    el("fx-retry")?.addEventListener("click", () => { cache.clear(); calc(); }); calc();
  }
  if (el("crypto-amount")) {
    let prices, fetched = 0, pending, version = 0;
    async function quote() {
      if (prices && Date.now() - fetched < 60000) return prices;
      if (!pending) pending = json("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd")
        .then((data) => {
          const next = { USD: 1, BTC: data.bitcoin?.usd, ETH: data.ethereum?.usd };
          if (![next.BTC,next.ETH].every((v) => Number.isFinite(v) && v > 0)) throw new Error("Invalid price");
          prices = next; fetched = Date.now(); return next;
        }).finally(() => { pending = null; });
      return pending;
    }
    async function calc() {
      const request = ++version, amount = number("crypto-amount"), from = el("crypto-from").value, to = el("crypto-to").value;
      if (!Number.isFinite(amount) || amount < 0) return invalid("crypto", "Enter an amount of zero or more.");
      if (from === to) return result("crypto", `${fmt(amount, to === "USD" ? 2 : 8)} ${to}`, "Rate 1:1 (same asset)");
      result("crypto", "—", "Loading price…");
      try {
        const p = await quote(); if (request !== version) return;
        const converted = amount * p[from] / p[to];
        if (!Number.isFinite(converted)) return invalid("crypto", "This amount exceeds the calculation range.");
        result("crypto", `${fmt(converted, to === "USD" ? 2 : 8)} ${to}`, `BTC: ${money(p.BTC)} · ETH: ${money(p.ETH)} · Fetched ${new Date(fetched).toLocaleTimeString("en-US")}`);
      } catch (error) { if (request === version) invalid("crypto", "Could not load prices. Use Retry prices to try again."); }
    }
    bind(["crypto-amount"], calc); bind(["crypto-from","crypto-to"], calc, "change");
    el("crypto-swap").addEventListener("click", () => { const a = el("crypto-from"), b = el("crypto-to"); [a.value,b.value] = [b.value,a.value]; calc(); });
    el("crypto-retry")?.addEventListener("click", () => { prices = null; fetched = 0; calc(); }); calc();
  }
});
