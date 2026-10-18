/* TTN optional analytics choice, available again through the footer. */
(() => {
  const key = 'ttn_cookie_consent';
  function show() {
    if (document.getElementById('cookie-consent')) return;
    const bar = document.createElement('div');bar.id = 'cookie-consent';
    bar.setAttribute('role','region');bar.setAttribute('aria-label','Analytics cookie preferences');
    bar.innerHTML = '<p>Optional analytics cookies help us understand how readers use TTN Finance. Choose Accept to enable analytics or Decline to keep it off. You can change your choice in the footer. <a href="cookies.html">Cookie Policy</a> and <a href="privacy.html">Privacy Policy</a>.</p><div class="cookie-consent-actions"><button id="cookie-accept" type="button">Accept</button><button id="cookie-decline" type="button">Decline</button></div>';
    document.body.appendChild(bar);
    function choose(choice) {
      try {localStorage.setItem(key,choice);} catch (_) {}
      window.dispatchEvent(new CustomEvent('ttn:consent',{detail:choice}));bar.remove();
    }
    bar.querySelector('#cookie-accept').addEventListener('click',()=>choose('accepted'));
    bar.querySelector('#cookie-decline').addEventListener('click',()=>choose('declined'));
  }
  document.addEventListener('click',event => {if(event.target.closest('[data-cookie-preferences]'))show();});
  let choice;try {choice=localStorage.getItem(key);} catch (_) {}
  if(choice!=='accepted' && choice!=='declined')show();
})();
