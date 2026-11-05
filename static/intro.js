// Intro loading screen, played when you click Home or the Nightwatch logo.
//
// 1. Click Home: the full-screen loader fades in on the current page, and we
//    note in sessionStorage that the intro should play, then go to the home page.
// 2. The home page sees that note before it is drawn (inline script in base.html)
//    and starts with the loader covering everything.
// 3. Once the page has loaded (and the loader has shown for at least ~1.2 s),
//    the loader slides up and the hero content animates in (style.css, "Intro").
//
// Skipped entirely when the visitor's device asks for reduced motion, and for
// Ctrl/Cmd-clicks (open in new tab). Without JavaScript, Home is a normal link.
(() => {
  const KEY = 'nightwatch-intro';
  const root = document.documentElement;
  const intro = document.getElementById('intro');
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!intro) return;

  // ---- Step 1: leaving a page through a Home link ----
  document.querySelectorAll('[data-home-link]').forEach(link => {
    link.addEventListener('click', e => {
      if (calm || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      try { sessionStorage.setItem(KEY, '1'); } catch {}
      intro.hidden = false;
      requestAnimationFrame(() => intro.classList.add('intro-in'));
      setTimeout(() => location.assign(link.href), 380);  // let the fade-in finish
    });
  });

  // Coming back with the browser's Back button can restore a page with the
  // loader still showing; hide it again.
  window.addEventListener('pageshow', e => {
    if (e.persisted && !root.classList.contains('intro-play')) {
      intro.classList.remove('intro-in');
      intro.hidden = true;
    }
  });

  // ---- Steps 2-3: arriving on the home page ----
  if (!root.classList.contains('intro-play')) return;
  try { sessionStorage.removeItem(KEY); } catch {}   // play once per click

  const MIN_SHOW = 1200;  // ms: long enough to read, short enough not to annoy
  const reveal = () => {
    setTimeout(() => {
      root.classList.add('intro-done');                 // slide loader away, animate hero in
      setTimeout(() => {                                 // tidy up once the last item has settled
        root.classList.remove('intro-play', 'intro-done');
        intro.hidden = true;
      }, 2400);
    }, Math.max(0, MIN_SHOW - performance.now()));
  };
  let started = false;
  const once = () => { if (!started) { started = true; reveal(); } };
  if (document.readyState === 'complete') once();
  else window.addEventListener('load', once, {once: true});
  setTimeout(once, 4000);  // safety net: never leave the loader up if something is slow
})();
