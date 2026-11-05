// Watch page: the full-screen map's side panel has three tabs (Alerts, Filters, Summary).
// - Click a tab, or use the arrow keys / Home / End when a tab has focus.
// - The last tab used is remembered for this browser tab, so applying a filter
//   (which reloads the page) brings you back to the same tab.
// - window.showWatchTab('alerts') lets other scripts (map popups, the guided tour)
//   open the tab that holds what they want to show.
(() => {
  const tabs = [...document.querySelectorAll('.watch-tabs [role="tab"]')];
  if (!tabs.length) return;
  const key = 'nightwatch-watch-tab';

  function show(tab, focus) {
    tabs.forEach(t => {
      const on = t === tab;
      t.setAttribute('aria-selected', on);
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
    });
    if (focus) tab.focus();
    try { sessionStorage.setItem(key, tab.id); } catch {}
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => show(tab, false));
    tab.addEventListener('keydown', e => {
      const moves = {ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1};
      if (!(e.key in moves)) return;
      e.preventDefault();
      show(tabs[(moves[e.key] + tabs.length) % tabs.length], true);
    });
  });

  window.showWatchTab = name => {
    const tab = document.getElementById('tab-' + name);
    if (tab && tab.getAttribute('aria-selected') !== 'true') show(tab, false);
  };

  // The guided tour asks for its next highlight; open the tab that contains it.
  document.addEventListener('tour:target', e => {
    const panel = e.detail && e.detail.closest('[role="tabpanel"]');
    if (panel) show(document.querySelector(`[aria-controls="${panel.id}"]`), false);
  });

  let saved;
  try { saved = sessionStorage.getItem(key); } catch {}
  const start = document.getElementById(saved);
  if (start && tabs.includes(start)) show(start, false);

  // The map fills the screen below the header. Measure the header (it wraps to
  // more lines on small screens) so the map is exactly the remaining height.
  const header = document.querySelector('.app-header');
  const notice = document.querySelector('.data-notice');
  const fit = () => {
    const h = (header ? header.offsetHeight : 0) + (notice ? notice.offsetHeight : 0);
    document.documentElement.style.setProperty('--header-h', h + 'px');
  };
  fit();
  window.addEventListener('resize', fit);
})();
