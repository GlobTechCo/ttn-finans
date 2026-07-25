/**
 * TTN — Market Snapshot
 * A short, automatically-composed summary built from the site's own live
 * data: which tracked assets are up/down right now, the day's biggest
 * mover, and which tickers are getting the most news mentions.
 *
 * Note: this is a rule-based summary generated client-side from live
 * numbers — not a call to a language model. Wiring in a real LLM-written
 * summary would need a server to hold the API key safely (an API key
 * placed directly in this file would be visible to anyone who views the
 * page source, and could run up your bill). If you later add a small
 * backend, this is the function to swap out.
 */
const TTNMarketSummary = (() => {
  function composeSummary() {
    const tracked = TTN_CONFIG.TICKERS.map((t) => ({
      label: t.label,
      ...TTNTickers.getState(t.id),
    })).filter((t) => t.changePct != null);

    if (!tracked.length) return null;

    const up = tracked.filter((t) => t.changePct >= 0);
    const down = tracked.filter((t) => t.changePct < 0);
    const biggestMover = [...tracked].sort((a, b) => Math.abs(b.changePct) - Math.abs(a.changePct))[0];
    const trending = TTNNews.getTrending().slice(0, 3);

    const sentiment =
      up.length > down.length ? "broadly higher" : up.length < down.length ? "broadly lower" : "mixed";

    let text = `Tracked assets are trading ${sentiment} right now: ${up.length} up, ${down.length} down out of ${tracked.length}. `;

    if (biggestMover) {
      text += `${biggestMover.label} is the biggest mover, ${biggestMover.changePct >= 0 ? "up" : "down"} ${Math.abs(
        biggestMover.changePct
      ).toFixed(2)}%. `;
    }

    if (trending.length) {
      const names = trending.map(([label]) => label).join(", ");
      text += `In the news, ${names} ${trending.length > 1 ? "are" : "is"} getting the most mentions right now.`;
    }

    return text;
  }

  function render() {
    const el = document.getElementById("market-summary-text");
    if (!el) return;
    const text = composeSummary();
    if (!text) {
      el.textContent = "Snapshot will appear once live prices finish loading.";
      return;
    }
    el.textContent = text;
    const stampEl = document.getElementById("market-summary-stamp");
    if (stampEl) stampEl.textContent = `Updated ${new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}`;
  }

  return { render };
})();
