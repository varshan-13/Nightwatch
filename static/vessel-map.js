// Display recorded locations only: event samples do not establish a vessel track.
(() => {
  if (!window.L) return; // Keep the coordinate list and fallback message visible.
  const data = JSON.parse(document.getElementById('vessel-map-config').textContent);
  const fallback = document.getElementById('vessel-map-error');
  const map = L.map('vessel-map', {scrollWheelZoom: false});
  const tiles = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors', maxZoom: 12,
  }).addTo(map);
  tiles.on('tileerror', () => { fallback.hidden = false; });
  tiles.on('tileload', () => { fallback.hidden = true; });
  const accent = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();
  const locations = [[data.lat, data.lon]];
  data.events.forEach(event => {
    const label = document.createElement('span');
    label.textContent = `${data.labels[event.event] || event.event} · ${event.time}`;
    L.circleMarker([event.lat, event.lon], {radius: 6, color: accent, fillOpacity: 0.35}).bindPopup(label).addTo(map);
    locations.push([event.lat, event.lon]);
  });
  const label = document.createElement('b');
  label.textContent = data.label;
  L.marker([data.lat, data.lon]).bindPopup(label).addTo(map);
  map.fitBounds(locations, {padding: [30, 30], maxZoom: 7});
})();
