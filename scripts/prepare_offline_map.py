"""Download a small OSM vector extract and build a self-contained offline map.

Normal rebuilds use the checked-in GeoJSON; --refresh explicitly fetches OSM data.
No raster tiles are downloaded or bundled.
"""
import argparse
import base64
import json
from pathlib import Path
from datetime import datetime, timezone
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
DEST = PUBLIC / 'offline'
SOURCE = DEST / 'podlaga.geojson'
ENDPOINT = 'https://overpass-api.de/api/interpreter'


def fetch_osm_api(south, west, north, east, resume=False):
    """Four bounded raw-vector requests for this small area, cached for rebuilds."""
    if (north - south) * (east - west) > .02:
        raise ValueError('Area too large for this small-extract fallback; use Overpass')
    cache = ROOT / '.cache/offline-map'
    cache.mkdir(parents=True, exist_ok=True)
    nodes, ways = {}, {}
    timestamps = []
    def fetch(bottom, left, top, right, depth=0):
            bbox = f'{left},{bottom},{right},{top}'
            path = cache / (bbox + '.osm')
            request = urllib.request.Request('https://api.openstreetmap.org/api/0.6/map?bbox=' + bbox,
                headers={'User-Agent': 'RoznatiBrkatiOfflineMap/1.0', 'Accept': 'application/xml'})
            if resume and path.exists():
                raw = path.read_bytes()
            else:
                try:
                    with urllib.request.urlopen(request, timeout=60) as response:
                        raw = response.read()
                except urllib.error.HTTPError as error:
                    message = error.read().decode('utf-8', errors='replace')
                    if error.code != 400 or 'too many nodes' not in message or depth >= 2:
                        raise ValueError(f'OSM API {error.code}: {message}') from error
                    middle = (bottom + top) / 2
                    fetch(bottom, left, middle, right, depth + 1)
                    fetch(middle, left, top, right, depth + 1)
                    return
                path.write_bytes(raw)
            timestamps.append(path.stat().st_mtime)
            root = ET.fromstring(raw)
            for node in root.findall('node'):
                nodes[node.attrib['id']] = node
            for way in root.findall('way'):
                ways[way.attrib['id']] = way
            print(f'Downloaded vector area {bbox}: {len(raw)} bytes', flush=True)
    mid_lat, mid_lon = (south + north) / 2, (west + east) / 2
    for bottom, top in ((south, mid_lat), (mid_lat, north)):
        for left, right in ((west, mid_lon), (mid_lon, east)):
            fetch(bottom, left, top, right)
    elements = []
    for node in nodes.values():
        tags = {t.attrib['k']: t.attrib['v'] for t in node.findall('tag')}
        if tags.get('name') and (tags.get('place') in ('town', 'village', 'hamlet', 'isolated_dwelling') or tags.get('natural') == 'peak'):
            elements.append({'type': 'node', 'id': node.attrib['id'], 'tags': tags,
                             'lon': float(node.attrib['lon']), 'lat': float(node.attrib['lat'])})
    for way in ways.values():
        tags = {t.attrib['k']: t.attrib['v'] for t in way.findall('tag')}
        if not (tags.get('highway') or tags.get('waterway') or tags.get('railway') == 'rail' or tags.get('natural') in ('wood', 'water') or tags.get('landuse') in ('forest', 'meadow', 'residential')):
            continue
        refs = [p.attrib['ref'] for p in way.findall('nd')]
        if not all(ref in nodes for ref in refs):
            continue
        elements.append({'type': 'way', 'id': way.attrib['id'], 'tags': tags,
                         'geometry': [{'lat': float(nodes[ref].attrib['lat']), 'lon': float(nodes[ref].attrib['lon'])} for ref in refs]})
    return {'elements': elements, 'osm3s': {'timestamp_osm_base': datetime.fromtimestamp(min(timestamps), timezone.utc).isoformat()}}


def refresh(routes, endpoint, osm_api=False, resume=False):
    points = [p for r in routes for segment in r['segments'] for p in segment]
    south = round(min(p[0] for p in points) - .015, 6)
    west = round(min(p[1] for p in points) - .022, 6)
    north = round(max(p[0] for p in points) + .015, 6)
    east = round(max(p[1] for p in points) + .022, 6)
    bbox = f'{south},{west},{north},{east}'
    query = f'''[out:json][timeout:90];(
      way[highway]({bbox}); way[waterway]({bbox}); way[railway=rail]({bbox});
      way[natural~"^(wood|water)$"]({bbox});
      way[landuse~"^(forest|meadow|residential)$"]({bbox});
      node[place~"^(town|village|hamlet|isolated_dwelling)$"][name]({bbox});
      node[natural=peak][name]({bbox});
    );out geom;'''
    if osm_api:
        raw = fetch_osm_api(south, west, north, east, resume)
        endpoint = 'https://api.openstreetmap.org/api/0.6/map'
        query = f'Bounded API extracts within {west},{south},{east},{north}; filtered roads, waterways, areas and place names.'
    else:
        request = urllib.request.Request(endpoint,
            data=urllib.parse.urlencode({'data': query}).encode(),
            headers={'User-Agent': 'RoznatiBrkatiOfflineMap/1.0 (local hiking website)',
                     'Content-Type': 'application/x-www-form-urlencoded'})
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = json.load(response)
    if raw.get('remark'):
        raise ValueError('Incomplete Overpass response: ' + raw['remark'])
    features = []
    for item in raw['elements']:
        tags = item.get('tags', {})
        props = {key: tags[key] for key in ('name', 'highway', 'waterway', 'railway', 'natural', 'landuse', 'place', 'ele') if key in tags}
        if item['type'] == 'node':
            geometry = {'type': 'Point', 'coordinates': [item['lon'], item['lat']]}
        else:
            coords = [[round(p['lon'], 6), round(p['lat'], 6)] for p in item.get('geometry', [])]
            if len(coords) < 2:
                continue
            area = len(coords) >= 4 and coords[0] == coords[-1] and not any(k in tags for k in ('highway', 'waterway', 'railway'))
            geometry = {'type': 'Polygon' if area else 'LineString', 'coordinates': [coords] if area else coords}
        features.append({'type': 'Feature', 'id': f'{item["type"]}/{item["id"]}', 'properties': props, 'geometry': geometry})
    if len(features) < 50:
        raise ValueError('Unexpectedly small map extract; previous data retained')
    data = {'type': 'FeatureCollection', 'bbox': [west, south, east, north],
            'metadata': {'source': 'OpenStreetMap contributors', 'license': 'ODbL-1.0',
                         'licenseUrl': 'https://www.openstreetmap.org/copyright',
                         'endpoint': endpoint, 'query': query,
                         'osmTimestamp': raw['osm3s']['timestamp_osm_base'],
                         'downloadedAt': datetime.now(timezone.utc).isoformat()},
            'features': features}
    SOURCE.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')


def script(text):
    return '<script>' + text.replace('</script', '<\\/script') + '</script>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Fetch a fresh OSM extract over the network')
    parser.add_argument('--endpoint', default=ENDPOINT, help='Overpass API endpoint for the optional refresh')
    parser.add_argument('--osm-api', action='store_true', help='Use four small OSM API vector extracts if Overpass is unavailable')
    parser.add_argument('--resume', action='store_true', help='Reuse cached OSM API responses to resume an interrupted download')
    args = parser.parse_args()
    routes = json.loads((PUBLIC / 'data/routes.json').read_text(encoding='utf-8'))['routes']
    DEST.mkdir(parents=True, exist_ok=True)
    if args.refresh:
        refresh(routes, args.endpoint, args.osm_api, args.resume)
    if not SOURCE.exists():
        parser.error('No map extract; run with --refresh once')
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    west, south, east, north = data['bbox']
    for route in routes:
        if any(not (south <= p[0] <= north and west <= p[1] <= east) for s in route['segments'] for p in s):
            raise ValueError('Route outside map extract; run again with --refresh')
        route['gpxBase64'] = base64.b64encode((PUBLIC / route['download']).read_bytes()).decode('ascii')
    leaflet = PUBLIC / 'vendor/leaflet'
    leaflet_css = (leaflet / 'leaflet.css').read_text(encoding='utf-8')
    for filename in ('layers.png', 'layers-2x.png', 'marker-icon.png'):
        encoded = base64.b64encode((leaflet / 'images' / filename).read_bytes()).decode('ascii')
        leaflet_css = leaflet_css.replace('images/' + filename, 'data:image/png;base64,' + encoded)
    template = (ROOT / 'content/offline-map.html').read_text(encoding='utf-8')
    output = template.replace('<!-- MAP_STYLES -->', '<style>' + leaflet_css + '</style>')
    payload = '<!-- Leaflet license:\n' + (leaflet / 'LICENSE').read_text(encoding='utf-8') + '\n-->\n'
    payload += script((leaflet / 'leaflet.js').read_text(encoding='utf-8'))
    payload += script('window.OFFLINE_MAP = ' + json.dumps({'routes': routes, 'basemap': data}, ensure_ascii=False, separators=(',', ':')) + ';')
    payload += script((PUBLIC / 'js/offline-map.js').read_text(encoding='utf-8'))
    output = output.replace('<!-- MAP_SCRIPTS -->', payload)
    (DEST / 'zemljevid.html').write_text(output, encoding='utf-8')
    print(f'Offline map: {len(data["features"])} features, {len(output.encode("utf-8")) / 1024:.0f} KB; {DEST / "zemljevid.html"}')


if __name__ == '__main__':
    main()
