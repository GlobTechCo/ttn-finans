/**
 * TTN — financial calculators
 */
document.addEventListener("DOMContentLoaded", () => {
  const fmt = (v) =>
    v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  /* ---------- 1. Compound interest ---------- */
  function calcCompound() {
    const principal = parseFloat(document.getElementById("ci-principal").value) || 0;
    const monthly = parseFloat(document.getElementById("ci-monthly").value) || 0;
    const rate = (parseFloat(document.getElementById("ci-rate").value) || 0) / 100;
    const years = parseFloat(document.getElementById("ci-years").value) || 0;

    const monthlyRate = rate / 12;
    const months = years * 12;
    let balance = principal;
    let totalContributed = principal;

    for (let i = 0; i < months; i++) {
      balance = balance * (1 + monthlyRate) + monthly;
      totalContributed += monthly;
    }

    const growth = balance - totalContributed;
    document.getElementById("ci-result").textContent = `$${fmt(balance)}`;
    document.getElementById("ci-sub").textContent =
      `Contributed: $${fmt(totalContributed)} · Growth: $${fmt(growth)}`;
  }
  ["ci-principal", "ci-monthly", "ci-rate", "ci-years"].forEach((id) =>
    document.getElementById(id).addEventListener("input", calcCompound)
  );
  calcCompound();

  /* ---------- 2. Currency converter (live via Frankfurter) ---------- */
  let fxRateCache = {}; // "EUR_USD" -> rate

  async function calcFx() {
    const amount = parseFloat(document.getElementById("fx-amount").value) || 0;
    const from = document.getElementById("fx-from").value;
    const to = document.getElementById("fx-to").value;
    const subEl = document.getElementById("fx-sub");
    const resultEl = document.getElementById("fx-result");

    if (from === to) {
      resultEl.textContent = `${fmt(amount)} ${to}`;
      subEl.textContent = "Rate 1:1 (same currency)";
      return;
    }

    const cacheKey = `${from}_${to}`;
    if (fxRateCache[cacheKey]) {
      resultEl.textContent = `${fmt(amount * fxRateCache[cacheKey])} ${to}`;
      subEl.textContent = `1 ${from} = ${fxRateCache[cacheKey].toFixed(4)} ${to}`;
      return;
    }

    subEl.textContent = "Loading rate…";
    const endpoints = [
      `https://api.frankfurter.app/latest?from=${from}&to=${to}`,
      `https://api.frankfurter.dev/v1/latest?base=${from}&symbols=${to}`,
      `https://api.frankfurter.app/latest?from=${from}&to=${to}`,
    ];
    for (let attempt = 0; attempt < endpoints.length; attempt++) {
      try {
        const res = await fetch(endpoints[attempt]);
        const data = await res.json();
        const rate = data.rates[to];
        if (!rate) throw new Error("no rate in response");
        fxRateCache[cacheKey] = rate;
        resultEl.textContent = `${fmt(amount * rate)} ${to}`;
        subEl.textContent = `1 ${from} = ${rate.toFixed(4)} ${to}`;
        return;
      } catch (e) {
        if (attempt === endpoints.length - 1) {
          subEl.textContent = "Rate temporarily unavailable. Check your connection and try again";
          resultEl.textContent = "—";
        } else {
          await new Promise((r) => setTimeout(r, 400)); // brief pause before trying the next endpoint
        }
      }
    }
  }
  let fxDebounce;
  document.getElementById("fx-amount").addEventListener("input", () => {
    clearTimeout(fxDebounce);
    fxDebounce = setTimeout(calcFx, 350);
  });
  document.getElementById("fx-from").addEventListener("change", calcFx);
  document.getElementById("fx-to").addEventListener("change", calcFx);
  document.getElementById("fx-swap").addEventListener("click", () => {
    const from = document.getElementById("fx-from");
    const to = document.getElementById("fx-to");
    [from.value, to.value] = [to.value, from.value];
    calcFx();
  });
  calcFx();

  /* ---------- 3. Crypto P&L ---------- */
  function calcPnl() {
    const entry = parseFloat(document.getElementById("pnl-entry").value) || 0;
    const current = parseFloat(document.getElementById("pnl-current").value) || 0;
    const amount = parseFloat(document.getElementById("pnl-amount").value) || 0;
    const leverage = parseFloat(document.getElementById("pnl-leverage").value) || 1;

    if (entry <= 0) return;
    const priceChangePct = (current - entry) / entry;
    const pnl = amount * priceChangePct * leverage;
    const pnlPct = priceChangePct * leverage * 100;

    const resultEl = document.getElementById("pnl-result");
    resultEl.textContent = `${pnl >= 0 ? "+" : ""}$${fmt(pnl)}`;
    resultEl.style.color = pnl >= 0 ? "var(--up)" : "var(--down)";
    document.getElementById("pnl-sub").textContent =
      `${pnlPct >= 0 ? "+" : ""}${pnlPct.toFixed(2)}% · Leverage ${leverage}x`;
  }
  ["pnl-entry", "pnl-current", "pnl-amount", "pnl-leverage"].forEach((id) =>
    document.getElementById(id).addEventListener("input", calcPnl)
  );
  calcPnl();

  /* ---------- 4. Loan / EMI calculator ---------- */
  function calcLoan() {
    const principal = parseFloat(document.getElementById("loan-amount").value) || 0;
    const annualRate = (parseFloat(document.getElementById("loan-rate").value) || 0) / 100;
    const months = parseFloat(document.getElementById("loan-term").value) || 1;

    const monthlyRate = annualRate / 12;
    let payment;
    if (monthlyRate === 0) {
      payment = principal / months;
    } else {
      payment =
        (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) /
        (Math.pow(1 + monthlyRate, months) - 1);
    }
    const totalPaid = payment * months;
    const totalInterest = totalPaid - principal;

    document.getElementById("loan-result").textContent = `$${fmt(payment)}`;
    document.getElementById("loan-sub").textContent =
      `Total: $${fmt(totalPaid)} · Extra cost: $${fmt(totalInterest)}`;
  }
  ["loan-amount", "loan-rate", "loan-term"].forEach((id) =>
    document.getElementById(id).addEventListener("input", calcLoan)
  );
  calcLoan();

  /* ---------- 5. Crypto converter (live via CoinGecko) ---------- */
  const cryptoIds = { BTC: "bitcoin", ETH: "ethereum" };
  let cryptoPriceCache = {}; // "BTC" -> price in USD

  async function fetchCryptoPrices() {
    const needed = Object.keys(cryptoIds).filter((sym) => !(sym in cryptoPriceCache));
    if (!needed.length) return;
    const ids = needed.map((sym) => cryptoIds[sym]).join(",");
    try {
      const res = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd`);
      const data = await res.json();
      needed.forEach((sym) => {
        cryptoPriceCache[sym] = data[cryptoIds[sym]]?.usd || null;
      });
    } catch (e) {
      needed.forEach((sym) => (cryptoPriceCache[sym] = null));
    }
  }

  function cryptoToUsd(amount, symbol) {
    if (symbol === "USD") return amount;
    const price = cryptoPriceCache[symbol];
    return price ? amount * price : null;
  }

  function usdToCrypto(usdAmount, symbol) {
    if (symbol === "USD") return usdAmount;
    const price = cryptoPriceCache[symbol];
    return price ? usdAmount / price : null;
  }

  async function calcCrypto() {
    const amount = parseFloat(document.getElementById("crypto-amount").value) || 0;
    const from = document.getElementById("crypto-from").value;
    const to = document.getElementById("crypto-to").value;
    const subEl = document.getElementById("crypto-sub");
    const resultEl = document.getElementById("crypto-result");

    if (from === to) {
      resultEl.textContent = `${fmt(amount)} ${to}`;
      subEl.textContent = "Same asset";
      return;
    }

    if (Object.keys(cryptoIds).some((sym) => !(sym in cryptoPriceCache))) {
      subEl.textContent = "Loading price…";
      await fetchCryptoPrices();
    }

    const usdValue = cryptoToUsd(amount, from);
    if (usdValue == null) {
      subEl.textContent = "Price temporarily unavailable. Check your connection and try again";
      resultEl.textContent = "—";
      return;
    }
    const result = usdToCrypto(usdValue, to);
    if (result == null) {
      subEl.textContent = "Price temporarily unavailable. Check your connection and try again";
      resultEl.textContent = "—";
      return;
    }

    const decimals = to === "USD" ? 2 : 8;
    resultEl.textContent = `${result.toLocaleString("en-US", { maximumFractionDigits: decimals })} ${to}`;
    if (from === "USD" && cryptoPriceCache[to]) {
      subEl.textContent = `1 ${to} = $${fmt(cryptoPriceCache[to])}`;
    } else if (to === "USD" && cryptoPriceCache[from]) {
      subEl.textContent = `1 ${from} = $${fmt(cryptoPriceCache[from])}`;
    } else {
      subEl.textContent = `Live CoinGecko price`;
    }
  }
  document.getElementById("crypto-amount").addEventListener("input", calcCrypto);
  document.getElementById("crypto-from").addEventListener("change", calcCrypto);
  document.getElementById("crypto-to").addEventListener("change", calcCrypto);
  document.getElementById("crypto-swap").addEventListener("click", () => {
    const from = document.getElementById("crypto-from");
    const to = document.getElementById("crypto-to");
    [from.value, to.value] = [to.value, from.value];
    calcCrypto();
  });
  calcCrypto();
});
