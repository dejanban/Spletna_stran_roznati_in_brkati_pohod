"""Browser checks; requires Python Playwright and installed Microsoft Edge.
Run: python tests/check_site.py
Uses a temporary loopback server; no connection to a real Google account.
"""
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse, parse_qs, urljoin
import hashlib
import json
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = ROOT / 'artifacts' / 'previews'

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # Browser navigation can cancel an in-flight image response.

def run():
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((ROOT / 'public/data/news.json').read_text(encoding='utf-8'))
    expected_counts = {'brkati-2025': 27, 'brkati-2024': 110, 'brkati-2023': 20, 'roznati-2025': 50, 'roznati-2024': 20}
    exclusions = json.loads((ROOT / 'content/gallery-exclusions.json').read_text(encoding='utf-8'))
    for article in catalog['articles']:
        assert len(article['photos']) == expected_counts[article['eventId']]
        assert not {photo['sourceUrl'] for photo in article['photos']}.intersection(exclusions.get(article['eventId'], []))
        for photo in article['photos']:
            image_path = (ROOT / 'public' / photo['url']).resolve()
            assert image_path.is_relative_to((ROOT / 'public/assets/novice').resolve())
            assert hashlib.sha256(image_path.read_bytes()).hexdigest() == photo['sha256']
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'public')))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 1000}, timezone_id='Europe/Ljubljana')
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.clock.install(time=datetime(2026, 10, 5, 10, tzinfo=timezone.utc))
            # News and photos must work without reaching the source website.
            page.route('**/*radio-odeon.com/**', lambda route: route.abort())
            assert page.goto(base).status == 200
            # A folder reorganization must preserve every entry-point asset and poster.
            resources = page.locator('script[src], link[href], img[src]').evaluate_all(
                "nodes => nodes.map(e => e.getAttribute('src') || e.getAttribute('href'))")
            resources += page.evaluate('window.EVENTS.map(event => event.poster).filter(Boolean)')
            for resource in set(resources):
                assert page.request.get(urljoin(base + '/', resource)).status == 200, resource
            for private_path in ['.git/config', '.cache/odeon/brkati-2025.html', 'docs/UPORABA.md', 'content/news-copy.json']:
                assert page.request.get(base + '/' + private_path).status == 404, private_path
            expect(page.locator('.event-card')).to_have_count(6)
            expect(page.locator('#upcoming-content')).to_contain_text('Brkati pohod 2026')
            expect(page.locator('#upcoming-content')).to_contain_text('21. november 2026')
            page.locator('[data-filter="roznati"]').click()
            expect(page.locator('.event-card')).to_have_count(3)
            page.select_option('#year-filter', '2023')
            expect(page.locator('.empty-results')).to_be_visible()
            page.locator('[data-filter="brkati"]').click()
            expect(page.locator('.event-card')).to_have_count(1)
            page.select_option('#year-filter', 'all')
            page.locator('[data-filter="all"]').click()
            page.locator('[data-event="roznati-2026"]').first.click()
            expect(page.locator('#event-dialog')).to_be_visible()
            expect(page.locator('.gallery-empty')).to_contain_text('še niso objavljene')
            page.keyboard.press('Escape')
            expect(page.locator('#event-dialog')).not_to_be_visible()
            assert page.evaluate('document.activeElement.dataset.event') == 'roznati-2026'
            expect(page.locator('.news-card')).to_have_count(5)
            for article in catalog['articles']:
                trigger = page.locator(f'[data-news="{article["eventId"]}"]').first
                trigger.click()
                expect(page.locator('#dialog-title')).to_have_text(article['title'])
                expect(page.locator('.news-source a')).to_have_attribute('href', article['sourceUrl'])
                expect(page.locator('.gallery-frame img')).to_be_visible()
                expect(page.locator('.gallery-frame img')).to_have_attribute('src', article['photos'][0]['url'])
                assert page.locator('.gallery-frame img').evaluate('img => img.complete && img.naturalWidth > 0')
                page.locator('[data-pause]').click()
                page.locator('[data-prev]').click()
                expect(page.locator('.gallery-counter')).to_have_text(f'{len(article["photos"])} / {len(article["photos"])}')
                expect(page.locator('.gallery-frame img')).to_be_visible()
                expect(page.locator('.gallery-frame img')).to_have_attribute('src', article['photos'][-1]['url'])
                page.keyboard.press('Escape')
                assert page.evaluate('document.activeElement.dataset.news') == article['eventId']
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(PREVIEWS / 'preview-desktop.png'), full_page=True)
            for width in [360, 390, 768, 1024, 1440]:
                page.set_viewport_size({'width': width, 'height': 900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow at {width}'
            page.set_viewport_size({'width': 390, 'height': 844})
            page.locator('.menu-toggle').click()
            expect(page.locator('#navigation')).to_be_visible()
            page.locator('#navigation a[href="#arhiv"]').click()
            expect(page.locator('#navigation')).not_to_be_visible()
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(PREVIEWS / 'preview-mobile.png'), full_page=True)
            page.locator('[data-news="brkati-2025"]').first.click()
            expect(page.locator('.gallery-frame img')).to_be_visible()
            assert page.locator('#event-dialog').evaluate('e => e.scrollWidth <= e.clientWidth')
            page.screenshot(path=str(PREVIEWS / 'preview-news-mobile.png'))
            page.keyboard.press('Escape')
            page.set_viewport_size({'width': 1440, 'height': 1000})
            page.locator('#novice').scroll_into_view_if_needed()
            page.screenshot(path=str(PREVIEWS / 'preview-news.png'))
            page.locator('[data-news="brkati-2025"]').first.click()
            expect(page.locator('.gallery-frame img')).to_be_visible()
            page.screenshot(path=str(PREVIEWS / 'preview-news-dialog.png'))
            page.keyboard.press('Escape')

            # Local photographs: actual image rendering, previous/next, pause, automatic rotation.
            page.evaluate('''() => { window.EVENTS[0].photos = [
              {url:'assets/vabila/roznati-2026.webp', caption:'Test image one'},
              {url:'assets/vabila/roznati-2025.webp', caption:'Test image two'}]; }''')
            page.locator('[data-event="roznati-2026"]').first.click()
            expect(page.locator('.gallery-frame img')).to_be_visible()
            expect(page.locator('.gallery-counter')).to_have_text('1 / 2')
            page.clock.run_for(5700)
            expect(page.locator('.gallery-counter')).to_have_text('2 / 2')
            page.locator('[data-pause]').click()
            page.clock.run_for(6000)
            expect(page.locator('.gallery-counter')).to_have_text('2 / 2')
            page.locator('[data-prev]').click()
            expect(page.locator('.gallery-counter')).to_have_text('1 / 2')
            page.keyboard.press('Escape')

            # Drive contract: pagination, download, failure/retry and empty albums.
            mode = {'value': 'success'}
            def drive(route):
                parsed = urlparse(route.request.url)
                query = parse_qs(parsed.query)
                if mode['value'] == 'error':
                    route.fulfill(status=403, json={'error': {'message': 'Test denied'}})
                elif parsed.path.endswith('/files'):
                    if mode['value'] == 'empty':
                        route.fulfill(json={'files': []})
                    elif 'pageToken' in query:
                        route.fulfill(json={'files': [{'id':'photo2','name':'02 Second image'}]})
                    else:
                        route.fulfill(json={'files':[{'id':'photo1','name':'01 First image'}], 'nextPageToken':'next'})
                else:
                    route.fulfill(status=200, content_type='image/webp', body=(ROOT/'public/assets/vabila/roznati-2026.webp').read_bytes())
            page.route('https://www.googleapis.com/drive/v3/**', drive)
            page.evaluate("window.SITE_CONFIG.driveApiKey='test-key'; window.EVENTS[0].driveFolderId='test-folder';")
            page.locator('[data-event="roznati-2026"]').first.click()
            page.locator('[data-load]').click()
            expect(page.locator('.gallery-counter')).to_have_text('1 / 2')
            expect(page.locator('.gallery-frame img')).to_be_visible()
            page.locator('[data-next]').click()
            expect(page.locator('.gallery-counter')).to_have_text('2 / 2')
            page.keyboard.press('Escape')
            mode['value'] = 'error'
            page.locator('[data-event="roznati-2026"]').first.click()
            page.locator('[data-load]').click()
            expect(page.locator('.gallery-error')).to_be_visible()
            mode['value'] = 'empty'
            page.locator('[data-retry]').click()
            expect(page.locator('.gallery-empty')).to_be_visible()
            page.keyboard.press('Escape')

            # Future and same-day events use the announcement section, then enter the archive.
            original = (ROOT/'public/data/events.js').read_text(encoding='utf-8')
            page.route('**/data/events.js*', lambda route: route.fulfill(content_type='text/javascript', body=original.replace('2026-10-03', '2026-10-06')))
            page.reload()
            expect(page.locator('#upcoming-content')).to_contain_text('PRIHAJAJOČI POHOD')
            expect(page.locator('.event-card')).to_have_count(5)
            page.locator('#upcoming-content [data-event="roznati-2026"]').click()
            expect(page.locator('.gallery')).to_have_count(0)
            page.keyboard.press('Escape')
            page.clock.set_system_time(datetime(2026,10,6,10,tzinfo=timezone.utc))
            page.reload()
            expect(page.locator('#upcoming-content')).to_contain_text('DANES')
            page.clock.set_system_time(datetime(2026,10,7,10,tzinfo=timezone.utc))
            page.reload()
            expect(page.locator('.event-card')).to_have_count(6)
            assert not errors, errors
            browser.close()
            print('PASS: 227 catalog images and editorial exclusions verified; five news popups and first/last photos load locally with Radio Odeon blocked; source links, focus, mobile layout, archive, filters, dates, slideshow, mocked Drive checks; no JavaScript errors.')
    finally:
        server.shutdown()
        server.server_close()

if __name__ == '__main__':
    run()
