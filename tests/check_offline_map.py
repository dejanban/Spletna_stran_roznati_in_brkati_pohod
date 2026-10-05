"""Verify the downloaded HTML works on its own with the network disabled."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import json
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    data = json.loads((PUBLIC / 'offline/podlaga.geojson').read_text(encoding='utf-8'))
    routes = json.loads((PUBLIC / 'data/routes.json').read_text(encoding='utf-8'))['routes']
    assert len(data['features']) > 50
    assert any(f['properties'].get('highway') for f in data['features'])
    assert any(f['geometry']['type'] == 'Point' for f in data['features'])
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(PUBLIC)))
    Thread(target=server.serve_forever, daemon=True).start()
    previews = ROOT / 'artifacts/previews'
    previews.mkdir(parents=True, exist_ok=True)
    try:
        with TemporaryDirectory() as folder, sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            context = browser.new_context(viewport={'width':1280, 'height':1000}, accept_downloads=True)
            page = context.new_page()
            errors, requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.locator('button[data-route="brkati"]').click()
            expect(page.locator('#route-offline-open')).to_have_attribute('href', 'offline/zemljevid.html#brkati')
            with page.expect_popup() as popup:
                page.locator('#route-offline-open').click()
            expect(popup.value.locator('#route-name')).to_have_text('Brkati pohod')
            popup.value.close()
            with page.expect_download() as download:
                page.locator('a[download="Pohoda-zemljevid-brez-povezave.html"]').click()
            saved = Path(folder) / 'pohoda.html'
            download.value.save_as(saved)
            assert saved.read_bytes() == (PUBLIC / 'offline/zemljevid.html').read_bytes()
            # Open a relocated file, with no sibling assets and no network.
            context.set_offline(True)
            page.on('request', lambda request: requests.append(request.url))
            page.goto(saved.as_uri())
            for route in routes:
                page.locator(f'button[data-route="{route["id"]}"]').click()
                expect(page.locator('#route-name')).to_have_text(route['title'])
                expect(page.locator('#map canvas')).to_be_visible()
                assert page.locator('.map-label').count() > 0
                # Basemap really paints pixels (a blank canvas/GPX outline is insufficient).
                assert page.locator('#map canvas').evaluate('c => c.getContext("2d").getImageData(0,0,c.width,c.height).data.some((v,i) => i % 4 === 3 && v > 0)')
                with page.expect_download() as gpx:
                    page.locator('#gpx').click()
                assert Path(gpx.value.path()).read_bytes() == (PUBLIC / route['download']).read_bytes()
            expect(page.locator('#route-note')).to_contain_text('Povratek ni vključen')
            line = page.locator('#map .leaflet-overlay-pane path').first
            original = line.get_attribute('d')
            page.locator('.leaflet-control-zoom-in').click()
            expect(line).not_to_have_attribute('d', original)
            page.locator('#fit').click()
            page.reload()
            expect(page.locator('#route-name')).to_have_text('Brkati pohod')
            page.screenshot(path=str(previews / 'preview-offline-desktop.png'))
            for width in (360,390,768,1024):
                page.set_viewport_size({'width':width, 'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.set_viewport_size({'width':390, 'height':844})
            page.screenshot(path=str(previews / 'preview-offline-mobile.png'), full_page=True)
            assert not [url for url in requests if url.startswith(('http:', 'https:'))], requests
            assert not errors, errors
            browser.close()
        print('PASS: actual HTML download, standalone offline reload, local basemap, both routes, zoom, GPX bytes, mobile layout, no network requests.')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
