/* boot.js - runs before anything else, as a plain script in the page's head.

   Computers only: it is decided here, before anything heavy loads, so a phone never downloads Python.  A phone or
   tablet is a device with no mouse or trackpad; the window width does not decide it, since a computer window can be
   narrow too.

   It also keeps every error that happens before the app has started (COILGEN.errors), so that the crash dialog of
   app/crash.js can show them: a page that fails early must still be able to say why. */
(function () {
  "use strict";
  var root = document.documentElement;
  var phone = window.matchMedia("(pointer: coarse)").matches && !window.matchMedia("(any-pointer: fine)").matches;
  var embedded = window.self !== window.top;
  if (phone) root.classList.add("phone");
  if (embedded) root.classList.add("embedded");
  var early = [];
  window.COILGEN = { phone: phone, embedded: embedded, errors: early, onError: null };
  function keep(kind, message, where) {
    var item = { kind: kind, message: String(message), where: where || "", at: Date.now() };
    if (window.COILGEN.onError) window.COILGEN.onError(item); else early.push(item);
  }
  window.addEventListener("error", function (e) {
    // a file that did not load (an image, a script) is an event on that element, with no message of its own
    if (e.target && e.target !== window && e.target.tagName) {
      keep("load", e.target.tagName.toLowerCase() + " did not load", e.target.src || e.target.href || "");
      return;
    }
    keep("error", e.message || "error", (e.filename || "") + (e.lineno ? ":" + e.lineno : ""));
  }, true);
  window.addEventListener("unhandledrejection", function (e) {
    var r = e.reason;
    keep("promise", r && (r.stack || r.message) || r, "");
  });
  window.addEventListener("securitypolicyviolation", function (e) {
    keep("policy", "blocked by the page's security policy: " + e.violatedDirective, e.blockedURI || "");
  });
})();
