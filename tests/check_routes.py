"""Check GPX parsing, downloads and route UI without external map requests."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from tempfile import TemporaryDirectory
import hashlib
import importlib.util
import json
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    spec = importlib.util.spec_from_file_location('prepare_routes', ROOT / 'scripts/prepare_routes.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    routes = json.loads((ROOT / 'public/data/routes.json').read_text(encoding='utf-8'))['routes']
    assert [(r['pointCount'], r['closed']) for r in routes] == [(1166, True), (152, False)]
    assert 10700 < routes[0]['distanceMeters'] < 10800
    assert 4500 < routes[1]['distanceMeters'] < 4600
    for route in routes:
        path = ROOT / 'public' / route['download']
        assert module.read_route(path)['segments'] == route['segments']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == route['sha256']
    with TemporaryDirectory() as folder:
        path = Path(folder) / 'segments.gpx'
        path.write_text('<gpx><trk><trkseg><trkpt lat="0" lon="0"/><trkpt lat="0" lon="0.01"/></trkseg><trkseg><trkpt lat="20" lon="20"/><trkpt lat="20" lon="20.01"/></trkseg></trk></gpx>')
        assert 2000 < module.read_route(path)['distanceMeters'] < 2300  # No bridge between distant segments.
        path.write_text('<gpx><rte><rtept lat="999" lon="0"/><rtept lat="0" lon="0.01"/></rte></gpx>')
        try:
            module.read_route(path)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid latitude accepted')

    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'public')))
    Thread(target=server.serve_forever, daemon=True).start()
    previews = ROOT / 'artifacts/previews'
    previews.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width':1440, 'height':1000})
            errors, tile_requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            def block_tile(route):
                tile_requests.append(route.request.url)
                route.abort()
            page.route('https://tile.openstreetmap.org/**', block_tile)
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            for route in routes:
                page.locator(f'button[data-route="{route["id"]}"]').click()
                expect(page.locator('#route-title')).to_have_text(route['title'])
                expect(page.locator('#route-map')).to_be_visible()
                with page.expect_download() as download_info:
                    page.locator('#route-download').click()
                download = download_info.value
                assert Path(download.path()).read_bytes() == (ROOT / 'public' / route['download']).read_bytes()
            assert tile_requests  # OpenStreetMap loads beneath the GPX by default.
            expect(page.locator('#route-length')).to_have_text('4,5 km')
            expect(page.locator('#route-note')).to_contain_text('Povratek ni vključen')
            expect(page.locator('#route-map')).to_be_visible()
            expect(page.locator('#route-map .leaflet-overlay-pane path')).to_have_count(3)
            expect(page.locator('#route-map-status')).to_be_visible()
            expect(page.locator('#route-map')).to_have_attribute('data-local-basemap', 'ready')
            expect(page.locator('#route-map .leaflet-local-base-pane canvas')).to_have_count(1)
            assert page.locator('#route-map .route-map-label').count() > 0
            line = page.locator('#route-map .leaflet-overlay-pane path').first
            before_zoom = line.get_attribute('d')
            page.locator('.leaflet-control-zoom-in').click()
            expect(line).not_to_have_attribute('d', before_zoom)
            page.locator('#route-fit').click()
            page.locator('button[data-route="roznati"]').click()
            expect(page.locator('#route-map .leaflet-overlay-pane path')).to_have_count(2)
            expect(page.locator('#route-length')).to_have_text('10,7 km')
            page.locator('#route-map-toggle').click()
            expect(page.locator('#route-outline')).to_be_visible()
            page.locator('#poti').evaluate("e => e.scrollIntoView({block:'start',behavior:'instant'})")
            page.screenshot(path=str(previews / 'preview-routes-desktop.png'))
            for width in [360, 390, 768, 1024, 1440]:
                page.set_viewport_size({'width':width, 'height':900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.set_viewport_size({'width':390, 'height':844})
            page.locator('#poti').evaluate("e => e.scrollIntoView({block:'start',behavior:'instant'})")
            page.screenshot(path=str(previews / 'preview-routes-mobile.png'))
            page.locator('[data-show-route="brkati"]').click()
            expect(page.locator('#route-title')).to_have_text('Brkati pohod')
            page.goto((ROOT / 'public/index.html').as_uri())
            expect(page.locator('#route-outline svg')).to_have_count(1)
            page.locator('#route-map-toggle').click()
            expect(page.locator('#route-map-status')).to_contain_text('trenutno ni na voljo')
            assert not errors, errors
            browser.close()
        print('PASS: GPX coordinates, distance, segments, validity, original downloads, route switching, map zoom, offline fallback and mobile layout.')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
