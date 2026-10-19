/* Exercise keyboard and pointer disclosure behavior without external services. */
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../editorial-theme.js'), 'utf8');
function element() {
  const listeners = {}, attrs = {}, classes = new Set();
  return {
    listeners, attrs,
    addEventListener(type, fn) { (listeners[type] ||= []).push(fn); },
    emit(type, event = {}) { for (const fn of listeners[type] || []) fn(event); },
    setAttribute(key, value) { attrs[key] = value; },
    getAttribute(key) { return attrs[key]; },
    classList: { add(key) { classes.add(key); }, toggle(key, value) { value ? classes.add(key) : classes.delete(key); }, contains(key) { return classes.has(key); } },
    focus() { doc.activeElement = this; }
  };
}
const doc = element(), header = element(), nav = element(), button = element(), link = element(), outside = element();
nav.contains = target => target === link;
header.contains = target => [header, nav, button, link].includes(target);
header.querySelector = selector => selector === '.nav-toggle' ? button : nav;
const media = element(); media.matches = true;
const start = source.indexOf('function initNavigation('), end = source.indexOf('\nfunction mount()', start);
assert(start > 0 && end > start);
const context = vm.createContext({ document: doc, matchMedia: () => media });
vm.runInContext(source.slice(start, end), context);
context.initNavigation(header);
const open = () => button.getAttribute('aria-expanded') === 'true';
assert(!open()); assert(header.classList.contains('ttn-nav-ready'));
button.emit('click'); assert(open()); assert(nav.classList.contains('open'));
assert.equal(button.getAttribute('aria-label'), 'Close navigation');
let prevented = false;
header.emit('keydown', {key:'Escape', preventDefault(){ prevented = true; }});
assert(!open()); assert(prevented); assert.equal(doc.activeElement, button);
button.emit('click'); nav.emit('click', {target:{closest:()=>link}}); assert(!open());
button.emit('click'); header.emit('focusout', {relatedTarget:link}); assert(open());
header.emit('focusout', {relatedTarget:outside}); assert(!open());
button.emit('click'); doc.emit('pointerdown', {target:outside}); assert(!open());
button.emit('click'); doc.activeElement=link; media.matches=false; media.emit('change'); assert(!open());
media.matches=true; media.emit('change'); assert.equal(doc.activeElement,button);
assert.equal(button.getAttribute('aria-label'), 'Open navigation');
console.log('PASS: navigation disclosure, Escape and focus return, link selection, Tab exit, outside click and responsive reset.');
