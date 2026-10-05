"use strict";
(() => {
  const {routes, basemap} = window.OFFLINE_MAP;
  const bounds = L.latLngBounds([basemap.bbox[1], basemap.bbox[0]], [basemap.bbox[3], basemap.bbox[2]]);
  const map = L.map('map', {minZoom: 12, maxZoom: 18, maxBounds: bounds, maxBoundsViscosity: 1, zoomControl: false});
  L.control.zoom({zoomInTitle: 'Približaj', zoomOutTitle: 'Oddalji'}).addTo(map);
  L.control.scale({imperial: false}).addTo(map);
  map.attributionControl.addAttribution('© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a> · ODbL');
  map.createPane('base');
  map.getPane('base').style.zIndex = 250;
  const renderer = L.canvas({pane: 'base', padding: .3});

  function style(feature) {
    const p = feature.properties;
    if (feature.geometry.type === 'Polygon') return {color: p.natural === 'water' ? '#acd3df' : p.landuse === 'residential' ? '#e3ded5' : '#d7e3c9', stroke: false, fillOpacity: .8};
    if (p.waterway) return {color: '#7cbbd6', weight: p.waterway === 'river' ? 3 : 1.5};
    if (p.railway) return {color: '#8b9194', weight: 2, dashArray: '6 4'};
    if (['path', 'footway', 'track', 'bridleway', 'steps', 'cycleway'].includes(p.highway)) return {color: '#958268', weight: 1.5, dashArray: '4 4'};
    return {color: '#b39b77', weight: ['primary', 'secondary', 'tertiary'].includes(p.highway) ? 3.5 : 2};
  }
  // Areas first, then roads and waterways. Canvas keeps the small local map responsive.
  const features = basemap.features.filter(f => f.geometry.type !== 'Point');
  features.sort((a,b) => Number(b.geometry.type === 'Polygon') - Number(a.geometry.type === 'Polygon'));
  L.geoJSON(features, {style, renderer, interactive: false}).addTo(map);
  const labels = L.layerGroup().addTo(map);
  function updateLabels() {
    labels.clearLayers();
    for (const feature of basemap.features) {
      if (feature.geometry.type !== 'Point') continue;
      const p = feature.properties;
      if (p.place === 'isolated_dwelling' && map.getZoom() < 15) continue;
      const element = document.createElement('span');
      element.textContent = (p.natural === 'peak' ? '▲ ' : '') + p.name;
      const [lon, lat] = feature.geometry.coordinates;
      L.tooltip({permanent: true, direction: 'center', className: 'map-label', interactive: false}).setLatLng([lat,lon]).setContent(element).addTo(labels);
    }
  }
  map.on('zoomend', updateLabels);
  const routeLayer = L.featureGroup().addTo(map);
  let selected, gpxUrl;
  const fit = () => map.fitBounds(routeLayer.getBounds(), {padding: [40,40], maxZoom: 15});
  function selectRoute(id) {
    selected = routes.find(r => r.id === id) || routes[0];
    document.documentElement.style.setProperty('--route-color', selected.color);
    document.querySelectorAll('[data-route]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.route === selected.id)));
    routeLayer.clearLayers();
    L.polyline(selected.segments, {color: '#fff', weight: 8, opacity: .9, interactive: false}).addTo(routeLayer);
    L.polyline(selected.segments, {color: selected.color, weight: 4, interactive: false}).addTo(routeLayer);
    const start = selected.segments[0][0], end = selected.segments.at(-1).at(-1);
    L.circleMarker(start, {color: selected.color, weight: 3, fillColor: '#fff', fillOpacity: 1, radius: 7}).bindPopup('Začetek sledi GPX').addTo(routeLayer);
    if (!selected.closed) L.circleMarker(end, {color: '#fff', weight: 3, fillColor: selected.color, fillOpacity: 1, radius: 7}).bindPopup('Konec sledi GPX').addTo(routeLayer);
    document.querySelector('#route-name').textContent = selected.title;
    document.querySelector('#route-length').textContent = `${new Intl.NumberFormat('sl-SI', {minimumFractionDigits: 1, maximumFractionDigits: 1}).format(selected.distanceMeters / 1000)} km · ${selected.closed ? 'sklenjena sled' : 'enosmerna sled'}`;
    document.querySelector('#route-start').textContent = `Začetek: ${start.map(n => n.toFixed(5)).join(', ')}`;
    document.querySelector('#route-note').textContent = selected.closed ? 'Sled se vrne do izhodišča.' : 'Povratek ni vključen v prikazano dolžino.';
    if (gpxUrl) URL.revokeObjectURL(gpxUrl);
    const bytes = Uint8Array.from(atob(selected.gpxBase64), c => c.charCodeAt(0));
    gpxUrl = URL.createObjectURL(new Blob([bytes], {type: 'application/gpx+xml'}));
    const link = document.querySelector('#gpx');
    link.href = gpxUrl;
    link.download = selected.download.split('/').pop();
    link.setAttribute('aria-label', `Prenesi GPX: ${selected.title}`);
    fit();
    updateLabels();
  }
  document.querySelectorAll('[data-route]').forEach(button => button.addEventListener('click', () => {
    location.hash = button.dataset.route;
  }));
  window.addEventListener('hashchange', () => selectRoute(location.hash.slice(1)));
  document.querySelector('#fit').addEventListener('click', fit);
  document.querySelector('#map-date').textContent = new Date(basemap.metadata.osmTimestamp).toLocaleDateString('sl-SI');
  selectRoute(location.hash.slice(1));
})();
