// Session storage keeps each tab's map/list position separate from other tabs.
window.rememberWatchPlace = function ({key, map, markers, rows, select, selected}) {
  let saved;
  try { saved = JSON.parse(sessionStorage.getItem(key)); } catch {}
  const table = document.querySelector('.ranked .table-scroll');
  const list = document.getElementById('panel-alerts');  // the scrolling alerts tab
  function save() {
    const center = map.getCenter();
    const state = {center: [center.lat, center.lng], zoom: map.getZoom(),
      vessel: selected(), popup: markers.has(selected()) && markers.get(selected()).marker.isPopupOpen(), x: window.scrollX, y: window.scrollY,
      tableX: table ? table.scrollLeft : 0, listY: list ? list.scrollTop : 0};
    try { sessionStorage.setItem(key, JSON.stringify(state)); } catch {}
  }
  // Capture the originating row even when its Open link is used directly.
  rows.forEach((row, id) => {
    row.querySelector('a.link-open').addEventListener('click', () => { select(id, false); save(); });
  });
  window.addEventListener('pagehide', save);
  function restore() {
    if (!saved || location.hash) return;
    if (Array.isArray(saved.center) && saved.center.length === 2 && saved.center.every(Number.isFinite)
        && Number.isFinite(saved.zoom)) map.setView(saved.center, saved.zoom, {animate: false});
    if (markers.has(saved.vessel)) {
      select(saved.vessel, false);
      if (saved.popup) markers.get(saved.vessel).marker.openPopup();
    }
    if (table && Number.isFinite(saved.tableX)) table.scrollLeft = saved.tableX;
    if (list && Number.isFinite(saved.listY)) list.scrollTop = saved.listY;
    if (Number.isFinite(saved.y)) {
      history.scrollRestoration = 'manual';
      window.scrollTo({left: saved.x || 0, top: saved.y, behavior: 'instant'});
    }
  }
  window.addEventListener('pageshow', event => {
    if (event.persisted) return; // Back/forward cache already retains the live page.
    const ready = document.fonts ? document.fonts.ready : Promise.resolve();
    ready.then(() => requestAnimationFrame(restore));
  });
};
