/* Shared TTN appearance control: no news/aggregator behavior changed. */
(()=>{const storageKey="ttn-theme";let selected;try{selected=localStorage.getItem(storageKey)}catch(e){}
const initial=selected==="dark"||selected==="light"?selected:(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");
document.documentElement.dataset.theme=initial;

// A disclosure navigation: ordinary links retain their natural Tab order.
function initNavigation(header) {
  const button = header.querySelector('.nav-toggle');
  const nav = header.querySelector('.nav-links');
  if (!button || !nav) return;
  // Normalize legacy article headers to the same three-line menu icon.
  button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true"><path d="M3 5h18M3 12h18M3 19h18"/></svg>';
  const compact = matchMedia('(max-width: 1200px)');
  function setOpen(open, restoreFocus = false) {
    nav.classList.toggle('open', open);
    button.setAttribute('aria-expanded', String(open));
    button.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    if (restoreFocus) button.focus();
  }
  button.addEventListener('click', () => setOpen(button.getAttribute('aria-expanded') !== 'true'));
  header.addEventListener('keydown', event => {
    if (event.key === 'Escape' && button.getAttribute('aria-expanded') === 'true') {
      event.preventDefault();
      setOpen(false, true);
    }
  });
  nav.addEventListener('click', event => {
    if (event.target.closest('a') && compact.matches) setOpen(false);
  });
  header.addEventListener('focusout', event => {
    if (event.relatedTarget && !header.contains(event.relatedTarget)) setOpen(false);
  });
  document.addEventListener('pointerdown', event => {
    if (!header.contains(event.target)) setOpen(false);
  });
  compact.addEventListener('change', () => {
    const focusWouldBeHidden = compact.matches && nav.contains(document.activeElement);
    setOpen(false, focusWouldBeHidden);
  });
  setOpen(false);
  header.classList.add('ttn-nav-ready');
}

function mount(){document.querySelectorAll(".topnav").forEach(header=>{initNavigation(header);const brand=header.querySelector(".brand");if(brand&&!brand.classList.contains("ttn-brand-clean")){brand.classList.remove("ttn-wordmark");brand.classList.add("ttn-brand-clean");brand.setAttribute("aria-label","TTN Finance home");brand.innerHTML='<span class="ttn-brand-title"><span class="ttn-brand-ttn">TTN</span><span class="ttn-brand-finance">Finance</span></span><span class="ttn-brand-tagline">Markets. Technology. Global Economy.</span>';} if(header.querySelector(".theme-switch"))return;const b=document.createElement("button");b.type="button";b.className="theme-switch";b.setAttribute("aria-label","Switch between light and dark appearance");b.addEventListener("click",()=>{const next=document.documentElement.dataset.theme==="light"?"dark":"light";document.documentElement.dataset.theme=next;try{localStorage.setItem(storageKey,next)}catch(e){};refresh()});header.appendChild(b)});refresh()}
function refresh(){document.querySelectorAll(".theme-switch").forEach(b=>{const dark=document.documentElement.dataset.theme==="dark";const label=dark?"Switch to light theme":"Switch to dark theme";b.innerHTML=dark?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.8 13A9 9 0 0 1 11 3.2 9 9 0 1 0 20.8 13Z"/></svg>';b.setAttribute("aria-label",label);b.title=label;b.setAttribute("aria-pressed",String(dark))})}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",mount);else mount();
})();
