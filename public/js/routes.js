"use strict";
(() => {
  const routes = window.HIKING_ROUTES?.routes || [];
  const section = document.querySelector("#poti");
  if (!section || !routes.length) return;
  const $ = selector => section.querySelector(selector);
  const format = new Intl.NumberFormat("sl-SI", {maximumFractionDigits: 1, minimumFractionDigits: 1});
  let selected = routes[0], map, layers, mapVisible = false;

  function renderOutline(route) {
    const hasTrack = Boolean(route.segments?.length);
    const points = hasTrack ? route.segments.flat() : [route.meetingPoint.coordinates, route.finishPoint.coordinates];
    const meanLat = points.reduce((sum, p) => sum + p[0], 0) / points.length;
    const project = point => [point[1] * Math.cos(meanLat * Math.PI / 180), -point[0]];
    const projected = points.map(project);
    const xs = projected.map(p => p[0]), ys = projected.map(p => p[1]);
    const minX = Math.min(...xs), minY = Math.min(...ys);
    const dx = Math.max(...xs) - minX, dy = Math.max(...ys) - minY;
    const scale = Math.min(560 / Math.max(dx, .000001), 320 / Math.max(dy, .000001));
    const screen = point => { const [x,y] = project(point); return [((x-minX)*scale + (640-dx*scale)/2).toFixed(2), ((y-minY)*scale + (400-dy*scale)/2).toFixed(2)]; };
    const paths = (route.segments || []).map(segment => `<polyline points="${segment.map(p => screen(p).join(',')).join(' ')}" fill="none" stroke="${route.color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`).join('');
    const start = screen(points[0]), end = screen(points[points.length-1]);
    const labels = hasTrack ? '' : `<text x="${start[0]}" y="${Number(start[1])+25}" text-anchor="middle" fill="${route.color}" font-size="16">Začetek</text><text x="${end[0]}" y="${Number(end[1])-18}" text-anchor="middle" fill="${route.color}" font-size="16">Cilj: Gače</text>`;
    $("#route-outline").innerHTML = `<svg viewBox="0 0 640 400" role="img" aria-label="${hasTrack ? `Obris poti ${route.title} iz datoteke GPX` : `Začetna in končna točka: ${route.title}`}"><defs><pattern id="route-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#5c7a911a"/></pattern></defs><rect width="640" height="400" fill="url(#route-grid)"/>${paths}<circle cx="${start[0]}" cy="${start[1]}" r="8" fill="#fff" stroke="${route.color}" stroke-width="4"/>${route.closed ? '' : `<rect x="${Number(end[0])-7}" y="${Number(end[1])-7}" width="14" height="14" rx="2" fill="${route.color}" stroke="#fff" stroke-width="2"/>`}${labels}<text x="602" y="27" text-anchor="middle" fill="#3b5366" font-size="13">S</text><path d="M602 37 L602 68 M596 45 L602 37 L608 45" fill="none" stroke="#3b5366" stroke-width="2"/></svg>`;
  }

  function drawMap() {
    if (!map) return;
    layers.clearLayers();
    if (selected.segments?.length) {
      L.polyline(selected.segments, {color: selected.color, weight: 5, opacity: .95}).addTo(layers);
      const start = selected.segments[0][0], end = selected.segments.at(-1).at(-1);
      L.circleMarker(start, {radius: 7, color: selected.color, fillColor: '#fff', fillOpacity: 1, weight: 3}).bindPopup(selected.closed ? 'Začetek in konec sledi GPX' : 'Začetek sledi GPX').addTo(layers);
      if (!selected.closed) L.circleMarker(end, {radius: 7, color: '#fff', fillColor: selected.color, fillOpacity: 1, weight: 3}).bindPopup('Konec sledi GPX').addTo(layers);
    }
    const meeting = selected.meetingPoint;
    const label = document.createElement('span');
    label.textContent = `Zbor in začetek pohoda: ${meeting.address}`;
    L.marker(meeting.coordinates, {title: label.textContent, alt: label.textContent}).bindPopup(label).addTo(layers);
    if (selected.finishPoint) {
      const finishLabel = document.createElement('span');
      finishLabel.textContent = `Zaključek pohoda: ${selected.finishPoint.address}`;
      L.marker(selected.finishPoint.coordinates, {title: finishLabel.textContent, alt: finishLabel.textContent}).bindPopup(finishLabel).addTo(layers);
    }
    requestAnimationFrame(() => { map.invalidateSize(); map.fitBounds(layers.getBounds(), {paddingTopLeft: [64,96], paddingBottomRight: [32,32], maxZoom: 15}); });
  }

  function selectRoute(id) {
    selected = routes.find(route => route.id === id) || routes[0];
    section.dataset.route = selected.id;
    section.querySelectorAll('[data-route]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.route === selected.id)));
    $('#route-title').textContent = selected.title;
    const hasTrack = Boolean(selected.segments?.length);
    $('.route-details .eyebrow').textContent = hasTrack ? 'SLED IZ DATOTEKE GPX' : 'ZAČETNA IN KONČNA TOČKA';
    $('.route-stats').hidden = !hasTrack;
    $('#route-length').textContent = hasTrack ? `${format.format(selected.distanceMeters / 1000)} km` : '';
    $('#route-shape').textContent = selected.closed ? 'Sklenjena sled' : 'Enosmerna sled';
    $('#route-note').textContent = !hasTrack ? 'Prikazani sta začetna točka in zaključek na smučišču Gače.' : selected.closed ? 'Sled se vrne do izhodišča. Razdalja je izračunana iz priložene datoteke GPX.' : 'Sled vodi od izhodišča do cilja. Povratek ni vključen v prikazano dolžino.';
    const start = selected.meetingPoint.coordinates;
    $('#route-address').textContent = selected.meetingPoint.address;
    $('#route-start').textContent = `${start[0].toFixed(6)}, ${start[1].toFixed(6)}`;
    $('#route-download').hidden = !selected.download;
    if (selected.download) {
      $('#route-download').href = selected.download;
      $('#route-download').download = selected.download.split('/').pop();
      $('#route-download').setAttribute('aria-label', `Prenesi GPX: ${selected.title}`);
    } else {
      $('#route-download').removeAttribute('href');
      $('#route-download').removeAttribute('download');
      $('#route-download').removeAttribute('aria-label');
    }
    $('#route-finish').hidden = !selected.finishPoint;
    if (selected.finishPoint) {
      const [lat, lon] = selected.finishPoint.coordinates;
      $('#route-finish-address').textContent = selected.finishPoint.address;
      $('#route-end').textContent = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
      $('#route-end-link').href = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=16/${lat}/${lon}`;
    }
    updateMapLabels();
    $('#route-start-link').href = `https://www.openstreetmap.org/?mlat=${start[0]}&mlon=${start[1]}#map=16/${start[0]}/${start[1]}`;
    renderOutline(selected);
    if (mapVisible) drawMap();
  }

  function updateMapLabels() {
    const hasTrack = Boolean(selected.segments?.length);
    $('#route-map-toggle').textContent = mapVisible ? (hasTrack ? 'Prikaži obris poti' : 'Prikaži samo točki') : 'Odpri interaktivni zemljevid';
    $('#route-fit').textContent = hasTrack ? 'Pokaži celotno pot' : 'Pokaži obe točki';
  }

  function toggleMap() {
    if (!window.L || location.protocol === 'file:') {
      $('#route-map-status').hidden = false;
      $('#route-map-status').textContent = 'Interaktivni zemljevid trenutno ni na voljo. Podatki o pohodu so na voljo ob prikazu.';
      return;
    }
    mapVisible = !mapVisible;
    $('#route-map').hidden = !mapVisible;
    $('#route-outline').hidden = mapVisible;
    updateMapLabels();
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
        $('#route-map-status').textContent = 'Spletne podlage ni mogoče naložiti. Preverite internetno povezavo. Podatki o pohodu ostajajo na voljo ob zemljevidu.';
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
