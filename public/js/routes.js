"use strict";
(() => {
  const routes = window.HIKING_ROUTES?.routes || [];
  const section = document.querySelector("#poti");
  if (!section || !routes.length) return;
  const $ = selector => section.querySelector(selector);
  const format = new Intl.NumberFormat("sl-SI", {maximumFractionDigits: 1, minimumFractionDigits: 1});
  let selected = routes[0], map, layers, mapVisible = false;

  function renderOutline(route) {
    const points = route.segments.flat();
    const meanLat = points.reduce((sum, p) => sum + p[0], 0) / points.length;
    const project = point => [point[1] * Math.cos(meanLat * Math.PI / 180), -point[0]];
    const projected = points.map(project);
    const xs = projected.map(p => p[0]), ys = projected.map(p => p[1]);
    const minX = Math.min(...xs), minY = Math.min(...ys);
    const dx = Math.max(...xs) - minX, dy = Math.max(...ys) - minY;
    const scale = Math.min(560 / Math.max(dx, .000001), 320 / Math.max(dy, .000001));
    const screen = point => { const [x,y] = project(point); return [((x-minX)*scale + (640-dx*scale)/2).toFixed(2), ((y-minY)*scale + (400-dy*scale)/2).toFixed(2)]; };
    const paths = route.segments.map(segment => `<polyline points="${segment.map(p => screen(p).join(',')).join(' ')}" fill="none" stroke="${route.color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`).join('');
    const start = screen(points[0]), end = screen(points[points.length-1]);
    $("#route-outline").innerHTML = `<svg viewBox="0 0 640 400" role="img" aria-label="Obris poti ${route.title} iz datoteke GPX"><defs><pattern id="route-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#5c7a911a"/></pattern></defs><rect width="640" height="400" fill="url(#route-grid)"/>${paths}<circle cx="${start[0]}" cy="${start[1]}" r="8" fill="#fff" stroke="${route.color}" stroke-width="4"/>${route.closed ? '' : `<rect x="${Number(end[0])-7}" y="${Number(end[1])-7}" width="14" height="14" rx="2" fill="${route.color}" stroke="#fff" stroke-width="2"/>`}<text x="602" y="27" text-anchor="middle" fill="#3b5366" font-size="13">S</text><path d="M602 37 L602 68 M596 45 L602 37 L608 45" fill="none" stroke="#3b5366" stroke-width="2"/></svg>`;
  }

  function drawMap() {
    if (!map) return;
    layers.clearLayers();
    const line = L.polyline(selected.segments, {color: selected.color, weight: 5, opacity: .95}).addTo(layers);
    const start = selected.segments[0][0], end = selected.segments.at(-1).at(-1);
    L.circleMarker(start, {radius: 7, color: selected.color, fillColor: '#fff', fillOpacity: 1, weight: 3}).bindPopup(selected.closed ? 'Začetek in konec sledi GPX' : 'Začetek sledi GPX').addTo(layers);
    if (!selected.closed) L.circleMarker(end, {radius: 7, color: '#fff', fillColor: selected.color, fillOpacity: 1, weight: 3}).bindPopup('Konec sledi GPX').addTo(layers);
    requestAnimationFrame(() => { map.invalidateSize(); map.fitBounds(line.getBounds(), {padding: [32,32], maxZoom: 15}); });
  }

  function selectRoute(id) {
    selected = routes.find(route => route.id === id) || routes[0];
    section.dataset.route = selected.id;
    section.querySelectorAll('[data-route]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.route === selected.id)));
    $('#route-title').textContent = selected.title;
    $('#route-length').textContent = `${format.format(selected.distanceMeters / 1000)} km`;
    $('#route-shape').textContent = selected.closed ? 'Sklenjena sled' : 'Enosmerna sled';
    $('#route-note').textContent = selected.closed ? 'Sled se vrne do izhodišča. Razdalja je izračunana iz priložene datoteke GPX.' : 'Sled vodi od izhodišča do cilja. Povratek ni vključen v prikazano dolžino.';
    const start = selected.segments[0][0];
    $('#route-start').textContent = `${start[0].toFixed(5)}, ${start[1].toFixed(5)}`;
    $('#route-download').href = selected.download;
    $('#route-download').download = selected.download.split('/').pop();
    $('#route-download').setAttribute('aria-label', `Prenesi GPX: ${selected.title}`);
    $('#route-start-link').href = `https://www.openstreetmap.org/?mlat=${start[0]}&mlon=${start[1]}#map=16/${start[0]}/${start[1]}`;
    renderOutline(selected);
    if (mapVisible) drawMap();
  }

  function toggleMap() {
    if (!window.L || location.protocol === 'file:') {
      $('#route-map-status').hidden = false;
      $('#route-map-status').textContent = 'Interaktivni zemljevid trenutno ni na voljo. Obris poti in prenos GPX sta na voljo spodaj.';
      return;
    }
    mapVisible = !mapVisible;
    $('#route-map').hidden = !mapVisible;
    $('#route-outline').hidden = mapVisible;
    $('#route-map-toggle').textContent = mapVisible ? 'Prikaži obris poti' : 'Odpri interaktivni zemljevid';
    $('#route-map-toggle').setAttribute('aria-expanded', String(mapVisible));
    $('#route-fit').hidden = !mapVisible;
    $('#route-map-status').hidden = true;
    if (!mapVisible) return;
    if (!map) {
      map = L.map('route-map', {scrollWheelZoom: false, zoomControl: false});
      L.control.zoom({zoomInTitle: 'Približaj', zoomOutTitle: 'Oddalji'}).addTo(map);
      layers = L.featureGroup().addTo(map);
      L.tileLayer(window.SITE_CONFIG.mapTileUrl || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
      }).on('tileerror', () => {
        $('#route-map-status').hidden = false;
        $('#route-map-status').textContent = 'Spletne podlage ni mogoče naložiti. Preverite internetno povezavo ali izberite prikaz obrisa poti. Prenos GPX ostaja na voljo.';
      }).addTo(map);
    }
    drawMap();
  }

  section.querySelectorAll('[data-route]').forEach(button => button.addEventListener('click', () => selectRoute(button.dataset.route)));
  document.querySelectorAll('[data-show-route]').forEach(link => link.addEventListener('click', () => selectRoute(link.dataset.showRoute)));
  $('#route-map-toggle').addEventListener('click', toggleMap);
  $('#route-fit').addEventListener('click', drawMap);
  selectRoute(routes[0].id);
  if (window.L && location.protocol !== 'file:') toggleMap();
})();
