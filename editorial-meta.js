/* Shared publication metadata for original editorial cards and article headers. */
window.TTNEditorialMeta = (() => {
  const escape = value => String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function format(value) {
    if (!value) return '';
    // Legacy dates without an offset do not establish a publication timezone.
    const timed = /T.*(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);
    const date = new Date(timed ? value : String(value).slice(0,10) + 'T12:00:00Z');
    if (!Number.isFinite(date.getTime())) return '';
    const options = {timeZone:'America/New_York', month:'short', day:'numeric', year:'numeric'};
    const label = new Intl.DateTimeFormat('en-US', options).format(date);
    if (!timed) return label;
    const clock = new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York',hour:'numeric',minute:'2-digit',hour12:true}).format(date);
    const zone = new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York',timeZoneName:'short'}).formatToParts(date).find(part => part.type === 'timeZoneName').value;
    return label + ' · ' + clock + ' ' + zone;
  }
  function html(article) {
    const author = escape(article.author || 'TTN Research Desk');
    const date = format(article.date);
    return '<span class="editorial-author">' + author + '</span>' + (date ? '<span class="editorial-published"><time datetime="' + escape(article.date) + '">' + escape(date) + '</time></span>' : '');
  }
  function mount() {
    const date = document.querySelector('meta[property="article:published_time"]')?.content;
    document.querySelectorAll('[data-editorial-byline]').forEach(el => {
      const time = el.querySelector('time');
      el.innerHTML = html({author:el.dataset.author || 'TTN Research Desk',date:date || time?.getAttribute('datetime')});
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
  return {format, html};
})();
