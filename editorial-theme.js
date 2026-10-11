/* Shared TTN appearance control: no news/aggregator behavior changed. */
(()=>{const storageKey="ttn-theme";let selected;try{selected=localStorage.getItem(storageKey)}catch(e){}
const initial=selected==="dark"||selected==="light"?selected:(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");
document.documentElement.dataset.theme=initial;
function mount(){document.querySelectorAll(".topnav").forEach(header=>{if(header.querySelector(".theme-switch"))return;const b=document.createElement("button");b.type="button";b.className="theme-switch";b.setAttribute("aria-label","Switch between light and dark appearance");b.addEventListener("click",()=>{const next=document.documentElement.dataset.theme==="light"?"dark":"light";document.documentElement.dataset.theme=next;try{localStorage.setItem(storageKey,next)}catch(e){};refresh()});header.appendChild(b)});refresh()}
function refresh(){document.querySelectorAll(".theme-switch").forEach(b=>{const dark=document.documentElement.dataset.theme==="dark";b.textContent=dark?"☀ Light":"☾ Dark";b.setAttribute("aria-pressed",String(dark))})}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",mount);else mount();
})();