// AutoGlob — shared site script

document.addEventListener('DOMContentLoaded', function () {

  // Mobile nav toggle
  var toggle = document.getElementById('navToggle');
  var nav = document.getElementById('mainNav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var isOpen = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
    nav.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // Simple cookie consent banner
  var CONSENT_KEY = 'autoglob_cookie_consent';
  if (!localStorage.getItem(CONSENT_KEY)) {
    var banner = document.createElement('div');
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Cookie consent');
    banner.style.cssText = 'position:fixed;left:16px;right:16px;bottom:16px;z-index:100;' +
      'background:#141310;border:1px solid #2a2620;border-radius:3px;padding:16px 18px;' +
      'display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;' +
      'max-width:920px;margin:0 auto;font-family:Inter,sans-serif;color:#f2f0ea;font-size:13.5px;';
    banner.innerHTML =
      '<span style="max-width:56ch;color:#9a9690;">We use cookies for site functionality, analytics and advertising. See our ' +
      '<a href="cookies.html" style="color:#e8c468;">Cookie Policy</a>.</span>' +
      '<span style="display:flex;gap:10px;flex-shrink:0;">' +
      '<button id="cookieDecline" style="background:none;border:1px solid #2a2620;color:#9a9690;padding:9px 14px;border-radius:2px;font-size:13px;cursor:pointer;">Decline</button>' +
      '<button id="cookieAccept" style="background:#c9a227;border:none;color:#0a0a0a;font-weight:600;padding:9px 14px;border-radius:2px;font-size:13px;cursor:pointer;">Accept</button>' +
      '</span>';
    document.body.appendChild(banner);

    document.getElementById('cookieAccept').addEventListener('click', function () {
      localStorage.setItem(CONSENT_KEY, 'accepted');
      banner.remove();
    });
    document.getElementById('cookieDecline').addEventListener('click', function () {
      localStorage.setItem(CONSENT_KEY, 'declined');
      banner.remove();
    });
  }
});
