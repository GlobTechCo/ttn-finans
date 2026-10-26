/* TTN GA4: measurement ID confirmed by the site owner on 2026-10-26.
   One configuration per page, activated only by analytics consent. */
(() => {
  const id = 'G-2VM6S0QL1H';
  let initialized = false;
  function apply(choice) {
    window['ga-disable-' + id] = choice !== 'accepted';
    if (choice !== 'accepted') {
      if (initialized) window.gtag('consent', 'update', {analytics_storage:'denied'});
      return;
    }
    if (initialized) {window.gtag('consent','update',{analytics_storage:'granted'});return;}
    initialized = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () {window.dataLayer.push(arguments);};
    window.gtag('consent','default',{analytics_storage:'granted',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
    window.gtag('js', new Date());
    window.gtag('config',id,{allow_google_signals:false,allow_ad_personalization_signals:false});
    const script = document.createElement('script');
    script.async = true;script.id = 'ttn-google-analytics';
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
    document.head.appendChild(script);
  }
  window.addEventListener('ttn:consent',event => apply(event.detail));
  let choice;try {choice = localStorage.getItem('ttn_cookie_consent');} catch (_) {}
  apply(choice);
})();
